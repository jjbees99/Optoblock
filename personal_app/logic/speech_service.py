from __future__ import annotations

import threading
import wave
from datetime import datetime
from pathlib import Path
from typing import Callable

from personal_app.data.database import APP_DIR


class SpeechServiceError(RuntimeError):
    pass


class SpeechService:
    """Microphone recorder with a replaceable transcription backend."""

    def __init__(self, recordings_dir: Path | None = None, sample_rate: int = 16_000) -> None:
        self.recordings_dir = recordings_dir or APP_DIR / "voice_recordings"
        self.sample_rate = sample_rate
        self._stream = None
        self._frames: list[bytes] = []

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start_recording(self) -> None:
        if self.is_recording:
            raise SpeechServiceError("A recording is already in progress.")
        try:
            import sounddevice as sound
        except ImportError as exc:
            raise SpeechServiceError("Microphone support is not installed. Run: pip install -r requirements.txt") from exc

        self._frames = []

        def receive_audio(data, _frames, _time, status) -> None:
            if status:
                # Non-fatal input warnings are handled by PortAudio while recording continues.
                pass
            self._frames.append(bytes(data))

        try:
            self._stream = sound.RawInputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=receive_audio,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise SpeechServiceError(f"Could not open the microphone: {exc}") from exc

    def stop_recording(self) -> Path:
        if not self.is_recording:
            raise SpeechServiceError("No recording is in progress.")
        stream = self._stream
        self._stream = None
        try:
            stream.stop()
            stream.close()
        except Exception as exc:
            raise SpeechServiceError(f"Could not finish the recording: {exc}") from exc
        if not self._frames:
            raise SpeechServiceError("No audio was captured. Check the selected microphone and permissions.")

        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        target = self.recordings_dir / f"voice-brain-dump-{datetime.now():%Y%m%d-%H%M%S}.wav"
        with wave.open(str(target), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(self.sample_rate)
            audio.writeframes(b"".join(self._frames))
        self._frames = []
        return target

    def transcribe(self, audio_path: Path) -> str:
        """Transcribe with SpeechRecognition; replace this method for Whisper or Vosk."""
        try:
            import speech_recognition as speech
        except ImportError as exc:
            raise SpeechServiceError("Speech recognition is not installed. Run: pip install -r requirements.txt") from exc
        recognizer = speech.Recognizer()
        try:
            with speech.AudioFile(str(audio_path)) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio).strip()
        except speech.UnknownValueError as exc:
            raise SpeechServiceError("Speech could not be understood. You can type the transcript manually.") from exc
        except speech.RequestError as exc:
            raise SpeechServiceError(f"The speech service is unavailable: {exc}") from exc
        except (OSError, ValueError) as exc:
            raise SpeechServiceError(f"The recording could not be read: {exc}") from exc

    def transcribe_async(
        self,
        audio_path: Path,
        on_success: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        def work() -> None:
            try:
                on_success(self.transcribe(audio_path))
            except SpeechServiceError as exc:
                on_error(str(exc))

        threading.Thread(target=work, daemon=True, name="voice-transcription").start()

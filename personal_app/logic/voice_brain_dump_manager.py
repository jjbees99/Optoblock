import json
from datetime import datetime
from pathlib import Path

from personal_app.app import AppContext
from personal_app.data.database import APP_DIR
from personal_app.logic.brain_dump_parser import SuggestedItem


class TranscriptStorage:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or APP_DIR / "voice_transcripts"

    def save(self, transcript: str, audio_path: Path | None = None) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"voice-brain-dump-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
        target.write_text(
            json.dumps(
                {
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "transcript": transcript,
                    "audio_path": str(audio_path) if audio_path else "",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return target


class VoiceBrainDumpManager:
    def __init__(self, context: AppContext) -> None:
        self.context = context

    def add_approved(self, items: list[SuggestedItem]) -> dict[str, int]:
        counts = {category: 0 for category in ("To-Do", "Shopping", "Projects / Learning", "Reminder Candidate", "Archive / Notes")}
        for item in items:
            text = item.text.strip()
            if not text:
                continue
            if item.category == "Shopping":
                self.context.shopping.add(text)
            elif item.category == "Projects / Learning":
                self.context.projects.add(text, category="Voice Brain Dump")
            elif item.category == "Reminder Candidate":
                self.context.tasks.add(text, category="Reminder")
            elif item.category == "Archive / Notes":
                self.context.brain_dump.add_archived(text)
            else:
                self.context.tasks.add(text, category="Voice Brain Dump")
            counts[item.category] += 1
        return counts

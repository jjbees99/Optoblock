from datetime import date, timedelta

from pathlib import Path

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QTextEdit

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button
from personal_app.logic.speech_service import SpeechService, SpeechServiceError


class DashboardPage(Compartment):
    items_added = Signal(dict)
    transcript_ready = Signal(str)
    transcription_failed = Signal(str)
    def __init__(self, context: AppContext) -> None:
        super().__init__("Life Admin Dashboard", "A calm view of what needs attention now.", "Dashboard")
        self.context = context
        self.speech = SpeechService()
        self.last_audio_path: Path | None = None
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.focus = QTextEdit()
        self.focus.setPlaceholderText("Today focus")
        self.focus.setFixedHeight(90)
        self.focus.setText(context.settings.get("daily_focus") or "")
        self.focus.textChanged.connect(self._save_focus)
        quick = QHBoxLayout()
        self.quick = QTextEdit()
        self.quick.setPlaceholderText("Quick brain dump...")
        self.quick.setFixedHeight(54)
        capture = subtle_button("Capture")
        capture.clicked.connect(self._capture)
        self.voice = subtle_button("Voice")
        self.voice.setToolTip("Record speech into the quick brain dump")
        self.voice.clicked.connect(self._toggle_voice)
        quick.addWidget(self.quick, 1)
        quick.addWidget(self.voice)
        quick.addWidget(capture)
        self.voice_notice = QLabel("")
        self.voice_notice.setObjectName("InlineNotice")
        self.transcript_ready.connect(self._voice_ready)
        self.transcription_failed.connect(self._voice_failed)
        refresh = subtle_button("Refresh")
        refresh.clicked.connect(self.refresh)
        self.layout.addWidget(self.summary)
        self.layout.addWidget(self.focus)
        self.layout.addLayout(quick)
        self.layout.addWidget(self.voice_notice)
        self.layout.addWidget(refresh)
        self.refresh()

    def _save_focus(self) -> None:
        self.context.settings.set("daily_focus", self.focus.toPlainText().strip())

    def refresh(self) -> None:
        tasks = self.context.tasks.stats()
        shopping = self.context.shopping.stats()
        suggestion = self.context.unwind.suggest()
        suggest_text = suggestion["name"] if suggestion else "No unwind ideas left today."
        highs = ", ".join(row["name"] for row in tasks["high"]) or "None"
        today = date.today()
        task_rows = self.context.tasks.list("Active")
        due_today = sum(row["due_date"] == today.isoformat() for row in task_rows)
        overdue = sum(bool(row["due_date"] and row["due_date"] < today.isoformat()) for row in task_rows)
        bills = self.context.life_admin.list("bills")
        upcoming_bills = sum(row["status"] == "Upcoming" and bool(row["due_date"]) and row["due_date"] <= (today + timedelta(days=14)).isoformat() for row in bills)
        followups = self.context.life_admin.list("follow_ups")
        followups_due = sum(row["status"] != "Completed" and bool(row["due_date"]) and row["due_date"] <= (today + timedelta(days=3)).isoformat() for row in followups)
        self.summary.setText(
            f"Today: {due_today} tasks   •   Overdue: {overdue}\n"
            f"Bills in the next 14 days: {upcoming_bills}   •   Follow-ups due soon: {followups_due}\n"
            f"Active projects: {self.context.projects.in_progress_count()}\n"
            f"Next action: {self.context.projects.next_action()}"
        )

    def _capture(self) -> None:
        body = self.quick.toPlainText().strip()
        if body:
            self.context.brain_dump.add(body)
            self.quick.clear()
            self.items_added.emit({"Inbox": 1})

    def _toggle_voice(self) -> None:
        if self.speech.is_recording:
            try:
                self.last_audio_path = self.speech.stop_recording()
            except SpeechServiceError as exc:
                self._voice_failed(str(exc))
                return
            self.voice.setText("Voice")
            self.voice.setEnabled(False)
            self.voice_notice.setText("Transcribing…")
            self.speech.transcribe_async(self.last_audio_path, self.transcript_ready.emit, self.transcription_failed.emit)
            return
        try:
            self.speech.start_recording()
        except SpeechServiceError as exc:
            self.voice_notice.setText(str(exc))
            return
        self.voice.setText("Stop")
        self.voice_notice.setText("Listening… click Stop when finished.")

    def _voice_ready(self, text: str) -> None:
        existing = self.quick.toPlainText().strip()
        self.quick.setPlainText(" ".join(part for part in (existing, text.strip()) if part))
        self.voice.setEnabled(True)
        self.voice.setText("Voice")
        self.voice_notice.setText("Speech added. Edit it or capture it.")
        self._remove_temporary_audio()

    def _voice_failed(self, message: str) -> None:
        self.voice.setEnabled(True)
        self.voice.setText("Voice")
        self.voice_notice.setText(message)
        self._remove_temporary_audio()

    def _remove_temporary_audio(self) -> None:
        if self.last_audio_path:
            try:
                self.last_audio_path.unlink(missing_ok=True)
            except OSError:
                pass
            self.last_audio_path = None


class BrainDumpPage(Compartment):
    items_added = Signal(dict)
    transcript_ready = Signal(str)
    transcription_failed = Signal(str)
    def __init__(self, context: AppContext) -> None:
        super().__init__("Inbox / Brain Dump", "Capture first; choose a destination or let keywords suggest one.", "Brain Dump Scanner")
        self.context = context
        self.speech = SpeechService()
        self.last_audio_path: Path | None = None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._autosave_draft)
        self.text = QTextEdit()
        self.text.setPlaceholderText("Messy thoughts, loose ideas, reminders...")
        self.text.setPlainText(context.settings.get("brain_dump_draft") or "")
        self.text.textChanged.connect(self._save_timer.start)
        route = QHBoxLayout()
        self.destination = QComboBox()
        self.destination.addItems(["Auto-sort", "Inbox", "Shopping", "Follow-Up", "Bills & Renewals", "Errands & Appointments", "Projects"])
        self.voice = subtle_button("🎙 Voice")
        self.voice.clicked.connect(self._toggle_voice)
        route.addWidget(self.destination, 1)
        route.addWidget(self.voice)
        self.items = QLabel()
        self.items.setWordWrap(True)
        self.layout.addWidget(self.text)
        self.layout.addLayout(route)
        self.layout.addWidget(self.items)
        self.transcript_ready.connect(self._voice_ready)
        self.transcription_failed.connect(self._voice_failed)
        self.refresh()

    def save(self) -> None:
        self._save_timer.stop()
        body = self.text.toPlainText().strip()
        if body:
            destination = self.destination.currentText()
            if destination == "Auto-sort":
                destination = self._destination(body)
            self._route(body, destination)
            self.text.clear()
            self.refresh()
            self.items_added.emit({destination: 1})

    def _autosave_draft(self) -> None:
        self.context.settings.set("brain_dump_draft", self.text.toPlainText())

    def _toggle_voice(self) -> None:
        if self.speech.is_recording:
            try:
                self.last_audio_path = self.speech.stop_recording()
            except SpeechServiceError as exc:
                self._voice_failed(str(exc)); return
            self.voice.setText("🎙 Voice")
            self.voice.setEnabled(False)
            self.speech.transcribe_async(self.last_audio_path, self.transcript_ready.emit, self.transcription_failed.emit)
            return
        try:
            self.speech.start_recording()
            self.voice.setText("■ Stop")
        except SpeechServiceError as exc:
            self._voice_failed(str(exc))

    def _voice_ready(self, text: str) -> None:
        existing = self.text.toPlainText().strip()
        self.text.setPlainText(" ".join(part for part in (existing, text.strip()) if part))
        self.voice.setEnabled(True); self.voice.setText("🎙 Voice")
        self._remove_audio()

    def _voice_failed(self, _message: str) -> None:
        self.voice.setEnabled(True); self.voice.setText("🎙 Voice")
        self._remove_audio()

    def _remove_audio(self) -> None:
        if self.last_audio_path:
            try: self.last_audio_path.unlink(missing_ok=True)
            except OSError: pass
            self.last_audio_path = None

    @staticmethod
    def _destination(body: str) -> str:
        text = body.casefold()
        rules = [
            (("buy", "shopping", "order", "groceries"), "Shopping"),
            (("email", "message", "reply", "call"), "Follow-Up"),
            (("bill", "pay", "subscription", "renew"), "Bills & Renewals"),
            (("appointment", "meeting", "doctor", "training"), "Errands & Appointments"),
            (("idea", "project", "build", "research"), "Projects"),
        ]
        return next((destination for words, destination in rules if any(word in text for word in words)), "Inbox")

    def _route(self, body: str, destination: str) -> None:
        if destination == "Shopping":
            self.context.shopping.add(body)
        elif destination == "Follow-Up":
            self.context.life_admin.add("follow_ups", contact=body, reason="Captured from inbox")
        elif destination == "Bills & Renewals":
            self.context.life_admin.add("bills", title=body)
        elif destination == "Errands & Appointments":
            self.context.life_admin.add("errands", title=body)
        elif destination == "Projects":
            self.context.projects.add(body)
        else:
            self.context.brain_dump.add(body)

    def refresh(self) -> None:
        rows = self.context.brain_dump.list()[:5]
        self.items.setText("\n\n".join(row["body"] for row in rows) or "No saved brain dumps yet.")

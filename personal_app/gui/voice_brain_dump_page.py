from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button
from personal_app.logic.brain_dump_parser import CATEGORIES, BrainDumpParser, SuggestedItem
from personal_app.logic.speech_service import SpeechService, SpeechServiceError
from personal_app.logic.voice_brain_dump_manager import TranscriptStorage, VoiceBrainDumpManager


class VoiceBrainDumpPage(Compartment):
    transcript_ready = Signal(str)
    transcription_failed = Signal(str)
    items_added = Signal(object)

    def __init__(self, context: AppContext) -> None:
        super().__init__("Voice Brain Dump", "Record or type thoughts, then review every destination before adding.", "Voice Brain Dump")
        self.context = context
        self.speech = SpeechService()
        self.parser = BrainDumpParser()
        self.storage = TranscriptStorage()
        self.manager = VoiceBrainDumpManager(context)
        self.last_audio_path: Path | None = None

        recording_controls = QHBoxLayout()
        self.record_button = QPushButton("Record")
        self.record_button.clicked.connect(self.toggle_recording)
        recording_controls.addWidget(self.record_button)
        recording_controls.addStretch(1)

        self.transcript = QTextEdit()
        self.transcript.setPlaceholderText("Your transcript will appear here. You can also type or edit it before extraction.")
        self.transcript.setMinimumHeight(80)
        extract = QPushButton("Extract Items")
        extract.clicked.connect(self.extract_items)

        self.items = QTableWidget(0, 3)
        self.items.setHorizontalHeaderLabels(["Add", "Suggested item", "Category"])
        self.items.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items.horizontalHeader().setStretchLastSection(True)
        self.items.verticalHeader().setVisible(False)

        review_controls = QHBoxLayout()
        remove = danger_button("Delete selected")
        approve = QPushButton("Approve and Add")
        remove.clicked.connect(self.delete_selected)
        approve.clicked.connect(self.approve)
        review_controls.addWidget(remove)
        review_controls.addStretch(1)
        review_controls.addWidget(approve)

        self.notice = QLabel("Ready to record or type.")
        self.notice.setObjectName("CompartmentDescription")
        self.notice.setWordWrap(True)
        self.transcript_ready.connect(self._transcription_succeeded)
        self.transcription_failed.connect(self._transcription_failed)

        self.layout.addLayout(recording_controls)
        self.layout.addWidget(self.transcript)
        self.layout.addWidget(extract)
        self.layout.addWidget(self.items, 1)
        self.layout.addLayout(review_controls)
        self.layout.addWidget(self.notice)

    def toggle_recording(self) -> None:
        if self.speech.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        try:
            self.speech.start_recording()
        except SpeechServiceError as exc:
            self.notice.setText(str(exc))
            return
        self.record_button.setText("Stop")
        self.notice.setText("Recording from the default microphone...")

    def stop_recording(self) -> None:
        try:
            self.last_audio_path = self.speech.stop_recording()
        except SpeechServiceError as exc:
            self._reset_record_buttons()
            self.notice.setText(str(exc))
            return
        self._reset_record_buttons()
        self.notice.setText("Transcribing. This first backend requires an internet connection...")
        self.speech.transcribe_async(
            self.last_audio_path,
            self.transcript_ready.emit,
            self.transcription_failed.emit,
        )

    def extract_items(self) -> None:
        text = self.transcript.toPlainText().strip()
        if not text:
            self.notice.setText("Enter or record a transcript before extracting items.")
            return
        self.storage.save(text, self.last_audio_path)
        suggestions = self.parser.parse(text)
        self.items.setRowCount(0)
        for suggestion in suggestions:
            self._add_suggestion(suggestion)
        self.notice.setText(f"Found {len(suggestions)} suggested item(s). Review the text, category, and checkboxes.")

    def _add_suggestion(self, suggestion: SuggestedItem) -> None:
        row = self.items.rowCount()
        self.items.insertRow(row)
        approved = QTableWidgetItem()
        approved.setFlags(approved.flags() | Qt.ItemIsUserCheckable)
        approved.setCheckState(Qt.Checked)
        self.items.setItem(row, 0, approved)
        self.items.setItem(row, 1, QTableWidgetItem(suggestion.text))
        category = QComboBox()
        category.addItems(CATEGORIES)
        category.setCurrentText(suggestion.category)
        self.items.setCellWidget(row, 2, category)

    def delete_selected(self) -> None:
        rows = sorted({index.row() for index in self.items.selectedIndexes()}, reverse=True)
        for row in rows:
            self.items.removeRow(row)

    def approve(self) -> None:
        approved: list[SuggestedItem] = []
        for row in range(self.items.rowCount()):
            check = self.items.item(row, 0)
            text = self.items.item(row, 1)
            category = self.items.cellWidget(row, 2)
            if check and check.checkState() == Qt.Checked and text and isinstance(category, QComboBox):
                approved.append(SuggestedItem(text.text().strip(), category.currentText()))
        if not approved:
            self.notice.setText("Select at least one non-empty item to add.")
            return
        counts = self.manager.add_approved(approved)
        summary = ", ".join(f"{count} {name}" for name, count in counts.items() if count)
        self.items.setRowCount(0)
        self.notice.setText(f"Added: {summary}.")
        self.items_added.emit(counts)

    def _transcription_succeeded(self, text: str) -> None:
        self.transcript.setPlainText(text)
        self.storage.save(text, self.last_audio_path)
        self.notice.setText("Transcription complete. Edit it if needed, then extract items.")

    def _transcription_failed(self, message: str) -> None:
        self.notice.setText(message)

    def _reset_record_buttons(self) -> None:
        self.record_button.setEnabled(True)
        self.record_button.setText("Record")

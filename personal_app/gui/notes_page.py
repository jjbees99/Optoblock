from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button


class NotesPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Notes", "Quick notes that autosave locally while you type.", "Notes")
        self.context = context
        self.note_id: int | None = None
        self._loading = False
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(400)
        self.timer.timeout.connect(self.save_now)
        split = QSplitter()
        left = QWidget(); left_layout = QVBoxLayout(left)
        self.notes = QListWidget(); self.notes.currentItemChanged.connect(self.select_note)
        add = QPushButton("New note"); add.clicked.connect(self.create_note)
        delete = danger_button("Delete note"); delete.clicked.connect(self.delete_note)
        left_layout.addWidget(self.notes, 1); left_layout.addWidget(add); left_layout.addWidget(delete)
        editor = QWidget(); editor_layout = QVBoxLayout(editor)
        self.title = QLineEdit(); self.title.setPlaceholderText("Note title")
        self.body = QTextEdit(); self.body.setPlaceholderText("Start typing — this note saves automatically…")
        self.status = QLineEdit("Saved locally"); self.status.setReadOnly(True); self.status.setFocusPolicy(Qt.NoFocus)
        editor_layout.addWidget(self.title); editor_layout.addWidget(self.body, 1); editor_layout.addWidget(self.status)
        split.addWidget(left); split.addWidget(editor); split.setSizes([260, 700])
        self.layout.addWidget(split, 1)
        self.title.textChanged.connect(self.schedule_save); self.body.textChanged.connect(self.schedule_save)
        self.refresh()

    def refresh(self) -> None:
        current = self.note_id
        self.notes.clear()
        for row in self.context.notes.list():
            item = QListWidgetItem(row["title"] or "Untitled note"); item.setData(Qt.UserRole, row["id"])
            self.notes.addItem(item)
            if row["id"] == current: self.notes.setCurrentItem(item)

    def create_note(self) -> None:
        self.save_now(); self.note_id = self.context.notes.create(); self.refresh()
        for i in range(self.notes.count()):
            if self.notes.item(i).data(Qt.UserRole) == self.note_id: self.notes.setCurrentRow(i); break
        self.title.setFocus()

    def select_note(self, item, _previous=None) -> None:
        self.save_now()
        if not item: return
        row = self.context.notes.get(item.data(Qt.UserRole))
        if not row: return
        self._loading = True; self.note_id = row["id"]
        self.title.setText(row["title"]); self.body.setPlainText(row["body"]); self._loading = False

    def schedule_save(self) -> None:
        if not self._loading and self.note_id is not None:
            self.status.setText("Saving…"); self.timer.start()

    def save_now(self) -> None:
        if self.note_id is None or self._loading: return
        self.timer.stop(); self.context.notes.save(self.note_id, self.title.text(), self.body.toPlainText())
        self.status.setText("Saved locally"); item = self.notes.currentItem()
        if item: item.setText(self.title.text().strip() or "Untitled note")

    def delete_note(self) -> None:
        if self.note_id is None: return
        if QMessageBox.question(self, "Delete note?", "Are you sure you want to delete this note? This cannot be undone.") != QMessageBox.Yes: return
        self.context.notes.delete(self.note_id); self.note_id = None; self._loading = True
        self.title.clear(); self.body.clear(); self._loading = False; self.refresh()

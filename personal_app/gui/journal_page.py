from __future__ import annotations

from PySide6.QtCore import QBuffer, QIODevice, QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QSlider, QSplitter, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button, subtle_button
from personal_app.logic.speech_service import SpeechService, SpeechServiceError


class DrawingCanvas(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(360)
        self.setCursor(Qt.CrossCursor)
        self.image = QImage(1000, 650, QImage.Format_ARGB32)
        self.image.fill(Qt.white)
        self.pen_color = QColor("#37352f")
        self.pen_width = 5
        self.tool = "pen"
        self.last_point = QPoint()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        target = self._target_rect()
        painter.drawImage(target, self.image)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.last_point = self._image_point(event.position().toPoint())
            if self.tool == "fill":
                self._flood_fill(self.last_point, self.pen_color); self.changed.emit(); self.update()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            if self.tool == "fill": return
            point = self._image_point(event.position().toPoint())
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.Antialiasing)
            colour = QColor(Qt.white) if self.tool == "eraser" else self.pen_color
            painter.setPen(QPen(colour, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.last_point, point)
            self.last_point = point
            self.changed.emit()
            self.update()

    def _image_point(self, point: QPoint) -> QPoint:
        target = self._target_rect()
        x = max(0, min(target.width() - 1, point.x() - target.x()))
        y = max(0, min(target.height() - 1, point.y() - target.y()))
        return QPoint(int(x * self.image.width() / max(1, target.width())), int(y * self.image.height() / max(1, target.height())))

    def _target_rect(self) -> QRect:
        scale = min(self.width() / self.image.width(), self.height() / self.image.height())
        width, height = int(self.image.width() * scale), int(self.image.height() * scale)
        return QRect((self.width() - width) // 2, (self.height() - height) // 2, width, height)

    def _flood_fill(self, start: QPoint, replacement: QColor) -> None:
        source = self.image.pixelColor(start)
        if source == replacement: return
        width, height = self.image.width(), self.image.height(); stack = [(start.x(), start.y())]
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= width or y >= height or self.image.pixelColor(x, y) != source: continue
            self.image.setPixelColor(x, y, replacement)
            stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

    def clear(self) -> None:
        self.image.fill(Qt.white)
        self.changed.emit()
        self.update()

    def png_bytes(self) -> bytes:
        data = bytearray()
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        self.image.save(buffer, "PNG")
        data.extend(buffer.data())
        return bytes(data)


class JournalPage(Compartment):
    transcription_ready = Signal(str)
    transcription_failed = Signal(str)
    def __init__(self, context: AppContext) -> None:
        super().__init__("Journal", "A small daily place for diary entries, poems, short stories and drawings.", "Journal")
        self.context = context
        self.speech = SpeechService()
        self._draft_timer = QTimer(self); self._draft_timer.setSingleShot(True); self._draft_timer.setInterval(500)
        self._draft_timer.timeout.connect(self.save_now)
        self._drawing_timer = QTimer(self); self._drawing_timer.setSingleShot(True); self._drawing_timer.setInterval(700)
        self._drawing_timer.timeout.connect(self._save_drawing_draft)
        self.transcription_ready.connect(self._append_transcript)
        self.transcription_failed.connect(self._voice_error)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._writing_tab(), "Write")
        self.tabs.addTab(self._drawing_tab(), "Draw")
        self.tabs.addTab(self._archive_tab(), "Archive")
        self.layout.addWidget(self.tabs, 1)
        self.refresh()
        self._restore_draft()
        self._restore_drawing_draft()

    def _writing_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        row = QHBoxLayout()
        self.kind = QComboBox(); self.kind.addItems(["Diary", "Poem", "Short story"])
        self.title = QLineEdit(); self.title.setPlaceholderText("Title (optional)")
        row.addWidget(self.kind); row.addWidget(self.title, 1)
        self.body = QTextEdit(); self.body.setPlaceholderText("Write whatever is here today…")
        self.mic = subtle_button("🎙 Start voice"); self.mic.clicked.connect(self.toggle_voice)
        save = QPushButton("Save entry"); save.clicked.connect(self.save_writing)
        self.title.textChanged.connect(self._draft_timer.start); self.body.textChanged.connect(self._draft_timer.start); self.kind.currentTextChanged.connect(self._draft_timer.start)
        buttons = QHBoxLayout(); buttons.addWidget(self.mic); buttons.addStretch(1); buttons.addWidget(save)
        layout.addLayout(row); layout.addWidget(self.body, 1); layout.addLayout(buttons)
        return page

    def _drawing_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        colour = subtle_button("Pen colour"); colour.clicked.connect(self.choose_colour)
        pen = subtle_button("Pen"); pen.clicked.connect(lambda: setattr(self.canvas, "tool", "pen"))
        fill = subtle_button("Fill bucket"); fill.clicked.connect(lambda: setattr(self.canvas, "tool", "fill"))
        eraser = subtle_button("Eraser"); eraser.clicked.connect(lambda: setattr(self.canvas, "tool", "eraser"))
        clear = subtle_button("Clear canvas"); clear.clicked.connect(self.canvas_clear)
        self.brush = QSlider(Qt.Horizontal); self.brush.setRange(1, 30); self.brush.setValue(5); self.brush.setMaximumWidth(150)
        self.drawing_title = QLineEdit(); self.drawing_title.setPlaceholderText("Drawing title (optional)")
        tools.addWidget(pen); tools.addWidget(fill); tools.addWidget(eraser); tools.addWidget(colour); tools.addWidget(QLabel("Brush")); tools.addWidget(self.brush); tools.addWidget(clear); tools.addWidget(self.drawing_title, 1)
        self.canvas = DrawingCanvas(); self.brush.valueChanged.connect(lambda value: setattr(self.canvas, "pen_width", value))
        self.canvas.changed.connect(self._drawing_timer.start); self.drawing_title.textChanged.connect(self._drawing_timer.start)
        save = QPushButton("Save drawing"); save.clicked.connect(self.save_drawing)
        layout.addLayout(tools); layout.addWidget(self.canvas, 1); layout.addWidget(save)
        return page

    def _archive_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        splitter = QSplitter()
        self.archive = QListWidget(); self.archive.currentItemChanged.connect(self.show_entry)
        preview = QWidget(); preview_layout = QVBoxLayout(preview)
        self.preview_title = QLabel("Select an entry"); self.preview_title.setObjectName("JournalPreviewTitle")
        self.preview_text = QTextEdit(); self.preview_text.setReadOnly(True)
        self.preview_image = QLabel(); self.preview_image.setAlignment(Qt.AlignCenter); self.preview_image.setMinimumHeight(200)
        delete = danger_button("Delete selected entry"); delete.clicked.connect(self.delete_selected)
        preview_layout.addWidget(self.preview_title); preview_layout.addWidget(self.preview_text, 1); preview_layout.addWidget(self.preview_image, 1); preview_layout.addWidget(delete)
        splitter.addWidget(self.archive); splitter.addWidget(preview); splitter.setSizes([300, 650])
        layout.addWidget(splitter)
        return page

    def save_writing(self) -> None:
        if not self.body.toPlainText().strip():
            QMessageBox.information(self, "Nothing to save", "Write a few words first."); return
        self.context.journal.add(self.kind.currentText(), self.title.text(), self.body.toPlainText())
        self.context.settings.set("journal_draft", "")
        self.title.clear(); self.body.clear(); self.refresh(); self.tabs.setCurrentIndex(2)

    def save_drawing(self) -> None:
        self.context.journal.add("Drawing", self.drawing_title.text(), drawing=self.canvas.png_bytes())
        self._drawing_timer.stop(); self.drawing_title.blockSignals(True); self.canvas.blockSignals(True)
        self.drawing_title.clear(); self.canvas.clear(); self.drawing_title.blockSignals(False); self.canvas.blockSignals(False)
        self.context.settings.set("journal_drawing_draft", "")
        self.refresh(); self.tabs.setCurrentIndex(2)

    def choose_colour(self) -> None:
        colour = QColorDialog.getColor(self.canvas.pen_color, self, "Choose pen colour")
        if colour.isValid(): self.canvas.pen_color = colour

    def canvas_clear(self) -> None:
        self.canvas.clear()

    def save_now(self) -> None:
        import json
        draft = {"type": self.kind.currentText(), "title": self.title.text(), "body": self.body.toPlainText()}
        self.context.settings.set("journal_draft", json.dumps(draft, ensure_ascii=False))

    def flush_pending(self) -> None:
        self.save_now()
        self._save_drawing_draft()

    def _restore_draft(self) -> None:
        import json
        raw = self.context.settings.get("journal_draft")
        if not raw: return
        try:
            draft = json.loads(raw); self.kind.setCurrentText(draft.get("type", "Diary")); self.title.setText(draft.get("title", "")); self.body.setPlainText(draft.get("body", ""))
        except (ValueError, TypeError): pass

    def _save_drawing_draft(self) -> None:
        import base64, json
        payload = {"title": self.drawing_title.text(), "png": base64.b64encode(self.canvas.png_bytes()).decode("ascii")}
        self.context.settings.set("journal_drawing_draft", json.dumps(payload))

    def _restore_drawing_draft(self) -> None:
        import base64, json
        raw = self.context.settings.get("journal_drawing_draft")
        if not raw: return
        try:
            draft = json.loads(raw); image = QImage(); image.loadFromData(base64.b64decode(draft["png"]), "PNG")
            if not image.isNull(): self.canvas.image = image; self.canvas.update()
            self.drawing_title.setText(draft.get("title", ""))
        except (ValueError, TypeError, KeyError): pass

    def toggle_voice(self) -> None:
        try:
            if not self.speech.is_recording:
                self.speech.start_recording(); self.mic.setText("■ Stop voice")
            else:
                path = self.speech.stop_recording(); self.mic.setText("Transcribing…"); self.mic.setEnabled(False)
                self.speech.transcribe_async(path, self.transcription_ready.emit, self.transcription_failed.emit)
        except SpeechServiceError as exc:
            self._voice_error(str(exc))

    def _append_transcript(self, text: str) -> None:
        cursor = self.body.textCursor()
        if self.body.toPlainText() and not self.body.toPlainText().endswith((" ", "\n")): cursor.insertText(" ")
        cursor.insertText(text); self.body.setTextCursor(cursor); self.mic.setText("🎙 Start voice"); self.mic.setEnabled(True); self.save_now()

    def _voice_error(self, message: str) -> None:
        self.mic.setText("🎙 Start voice"); self.mic.setEnabled(True); QMessageBox.warning(self, "Voice input", message)

    def refresh(self) -> None:
        if not hasattr(self, "archive"): return
        self.archive.clear()
        for row in self.context.journal.list():
            title = row["title"] or row["entry_type"]
            item = QListWidgetItem(f"{row['entry_date']}  ·  {row['entry_type']}\n{title}")
            item.setData(Qt.UserRole, row["id"]); self.archive.addItem(item)

    def show_entry(self, item, _previous=None) -> None:
        if not item: return
        row = self.context.journal.get(item.data(Qt.UserRole))
        if not row: return
        self.preview_title.setText(f"{row['entry_date']}  ·  {row['title'] or row['entry_type']}")
        self.preview_text.setVisible(bool(row["body"])); self.preview_text.setPlainText(row["body"] or "")
        self.preview_image.clear(); self.preview_image.setVisible(bool(row["drawing"]))
        if row["drawing"]:
            pixmap = QPixmap(); pixmap.loadFromData(row["drawing"])
            self.preview_image.setPixmap(pixmap.scaled(650, 430, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def delete_selected(self) -> None:
        item = self.archive.currentItem()
        if item and QMessageBox.question(self, "Delete journal entry?", "This cannot be undone.") == QMessageBox.Yes:
            self.context.journal.delete(item.data(Qt.UserRole)); self.preview_text.clear(); self.preview_image.clear(); self.refresh()

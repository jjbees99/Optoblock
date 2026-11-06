from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QPainter, QPen
from PySide6.QtWidgets import QDateEdit, QFrame, QHBoxLayout, QInputDialog, QLabel, QMenu, QPushButton, QScrollArea, QVBoxLayout, QWidget

from personal_app.gui.widgets import Compartment, subtle_button
from personal_app.gui.drag_payloads import TASK_MIME_TYPE, decode_task

DAY_START = 0
PIXELS_PER_HOUR = 72
LABEL_WIDTH = 48


class BlockWidget(QFrame):
    changed = Signal(int, int, int)
    renamed = Signal(int, str)
    removed = Signal(int)
    duplicated = Signal(int)
    notes_changed = Signal(int, str)

    def __init__(self, record: dict, parent=None):
        super().__init__(parent); self.record = record
        self.setToolTip("Drag to move · drag an edge to resize · double-click to rename")
        self.setStyleSheet(f"QFrame {{background:{record['colour']}; color:#102027; border-radius:5px; padding:3px; font-weight:600;}}")
        from PySide6.QtWidgets import QLabel
        self.label = QLabel(record["title"], self); self.label.setWordWrap(True); self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self); layout.setContentsMargins(6, 3, 6, 3); layout.addWidget(self.label)
        self._press = QPoint(); self._original = self.geometry(); self._mode = "move"

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = event.globalPosition().toPoint(); self._original = self.geometry()
            self._mode = "top" if event.position().y() < 7 else "bottom" if event.position().y() > self.height()-7 else "move"
            self.raise_()
            if isinstance(self.parentWidget(), Timeline):
                self.parentWidget().raise_overlays()

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton: return
        dy = event.globalPosition().toPoint().y() - self._press.y(); y, h = self._original.y(), self._original.height()
        if self._mode == "move": y += dy
        elif self._mode == "bottom": h += dy
        else: y += dy; h -= dy
        snap = PIXELS_PER_HOUR // 2
        y = max(0, round(y / snap) * snap); h = max(snap, round(h / snap) * snap)
        self.setGeometry(self.x(), y, self.width(), h)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            start = round(self.y() / PIXELS_PER_HOUR * 60)
            duration = round(self.height() / PIXELS_PER_HOUR * 60)
            self.changed.emit(self.record["id"], start, duration)

    def mouseDoubleClickEvent(self, event):
        text, ok = QInputDialog.getText(self, "Rename block", "What will you work on?", text=self.label.text())
        if ok and text.strip(): self.renamed.emit(self.record["id"], text.strip())

    def contextMenuEvent(self, event):
        menu = QMenu(self); rename = menu.addAction("Rename"); notes = menu.addAction("Edit notes…"); duplicate = menu.addAction("Duplicate"); menu.addSeparator(); delete = menu.addAction("Delete")
        chosen = menu.exec(event.globalPos())
        if chosen == rename: self.mouseDoubleClickEvent(event)
        elif chosen == notes:
            text, ok = QInputDialog.getMultiLineText(self, "Block notes", "Optional details", self.record.get("notes", ""))
            if ok: self.notes_changed.emit(self.record["id"], text)
        elif chosen == duplicate: self.duplicated.emit(self.record["id"])
        elif chosen == delete: self.removed.emit(self.record["id"])


class CurrentTimeIndicator(QWidget):
    """Transparent overlay that keeps the current-time line above planner blocks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.minute = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, _event):
        if self.minute is None:
            return
        y = self.minute * PIXELS_PER_HOUR // 60
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#ff7b72"), 2))
        painter.drawLine(LABEL_WIDTH, y, self.width(), y)


class Timeline(QWidget):
    create_requested = Signal(int, int)
    task_dropped = Signal(str, int, int)
    def __init__(self):
        super().__init__(); self.setMinimumHeight(24 * PIXELS_PER_HOUR); self.setMouseTracking(True); self.setAcceptDrops(True)
        self.now_minute = None; self._drag_start = None
        self.preview = QFrame(self)
        self.preview.setObjectName("PlannerDraft")
        self.preview.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.preview.setStyleSheet("QFrame#PlannerDraft { background: rgba(125, 211, 252, 105); border: 2px dashed #7dd3fc; border-radius: 5px; }")
        preview_layout = QVBoxLayout(self.preview); preview_layout.setContentsMargins(6, 3, 6, 3)
        self.preview_label = QLabel(); self.preview_label.setStyleSheet("color: #e8f7ff; font-weight: 700; background: transparent;")
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignTop)
        self.preview.hide()
        self.current_time_indicator = CurrentTimeIndicator(self)
        self.current_time_indicator.setGeometry(self.rect())
        self.current_time_indicator.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(TASK_MIME_TYPE):
            event.setDropAction(Qt.CopyAction); event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(TASK_MIME_TYPE):
            y = event.position().y()
            self._show_preview(y, y)
            title = decode_task(event.mimeData().data(TASK_MIME_TYPE))
            self.preview_label.setText(f"{self.preview_label.text()}  {title}")
            event.setDropAction(Qt.CopyAction); event.accept()

    def dragLeaveEvent(self, event):
        self.preview.hide(); event.accept()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(TASK_MIME_TYPE): return
        title = decode_task(event.mimeData().data(TASK_MIME_TYPE))
        minute, duration = self.selection(event.position().y(), event.position().y())
        self.preview.hide()
        if title: self.task_dropped.emit(title, minute, duration)
        event.setDropAction(Qt.CopyAction); event.accept()
    def paintEvent(self, _event):
        painter = QPainter(self); painter.setPen(QPen(QColor("#59636a"), 1))
        for minute in range(0, 24*60, 30):
            y = minute * PIXELS_PER_HOUR // 60
            painter.setPen(QColor("#78838a") if minute % 60 == 0 else QColor("#3e484e"))
            painter.drawLine(LABEL_WIDTH, y, self.width(), y)
            if minute % 60 == 0: painter.drawText(4, y + 13, f"{minute//60:02d}:00")
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.current_time_indicator.setGeometry(self.rect())
        self.raise_overlays()

    def set_now_minute(self, minute):
        self.now_minute = minute
        self.current_time_indicator.minute = minute
        self.current_time_indicator.update()
        self.raise_overlays()

    def raise_overlays(self):
        self.preview.raise_()
        self.current_time_indicator.raise_()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().x() >= LABEL_WIDTH:
            self._drag_start = event.position().y()
            self.setCursor(Qt.CrossCursor)
            self._show_preview(self._drag_start, self._drag_start)

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and event.buttons() & Qt.LeftButton:
            self._show_preview(self._drag_start, event.position().y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag_start is not None:
            start_y = self._drag_start
            minute, duration = self.selection(start_y, event.position().y())
            self._drag_start = None
            self.preview.hide(); self.unsetCursor()
            self.create_requested.emit(minute, duration)

    def _show_preview(self, first_y: float, current_y: float) -> None:
        minute, duration = self.selection(first_y, current_y)
        y = minute * PIXELS_PER_HOUR // 60
        height = max(PIXELS_PER_HOUR // 2, duration * PIXELS_PER_HOUR // 60)
        self.preview.setGeometry(LABEL_WIDTH + 6, y, max(80, self.width() - LABEL_WIDTH - 12), height)
        end = minute + duration
        self.preview_label.setText(f"{minute//60:02d}:{minute%60:02d} – {end//60:02d}:{end%60:02d}")
        self.preview.show(); self.preview.raise_()
        self.raise_overlays()

    @staticmethod
    def selection(first_y: float, current_y: float) -> tuple[int, int]:
        low, high = sorted((max(0, first_y), max(0, current_y)))
        start = round(low / PIXELS_PER_HOUR * 2) * 30
        end = round(high / PIXELS_PER_HOUR * 2) * 30
        start = max(0, min(1410, start))
        end = max(start + 30, min(1440, end))
        return start, end - start


class DayPlannerPage(Compartment):
    def __init__(self, context):
        super().__init__("Day Planner", module_name="Day Planner"); self.context = context; self.current_date = date.today(); self.blocks = []
        nav = QHBoxLayout(); prev = subtle_button("‹"); today = QPushButton("Today"); nxt = subtle_button("›")
        self.date_edit = QDateEdit(); self.date_edit.setCalendarPopup(True); self.date_edit.setDisplayFormat("ddd, d MMM")
        prev.clicked.connect(lambda: self._step(-1)); nxt.clicked.connect(lambda: self._step(1)); today.clicked.connect(self._today); self.date_edit.dateChanged.connect(self._date_changed)
        for widget in (prev, today, nxt, self.date_edit): nav.addWidget(widget)
        nav.addStretch(1); self.layout.addLayout(nav)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.timeline = Timeline(); self.scroll.setWidget(self.timeline); self.layout.addWidget(self.scroll, 1)
        self.timeline.create_requested.connect(self._create)
        self.timeline.task_dropped.connect(self._schedule_task)
        self.timer = QTimer(self); self.timer.timeout.connect(self._update_now); self.timer.start(30000)
        self._set_date(self.current_date); QTimer.singleShot(0, self._scroll_to_workday)

    def _set_date(self, value: date):
        self.current_date = value; self.date_edit.blockSignals(True); self.date_edit.setDate(QDate(value.year, value.month, value.day)); self.date_edit.blockSignals(False); self.refresh()
    def _step(self, days): self._set_date(self.current_date + timedelta(days=days))
    def _today(self): self._set_date(date.today()); self._scroll_to_workday()
    def _date_changed(self, value): self._set_date(date(value.year(), value.month(), value.day()))
    def _scroll_to_workday(self): self.scroll.verticalScrollBar().setValue(7 * PIXELS_PER_HOUR)
    def _update_now(self):
        now = datetime.now(); self.timeline.set_now_minute(now.hour*60+now.minute if self.current_date == date.today() else None)
    def refresh(self):
        for block in self.blocks: block.deleteLater()
        self.blocks = []
        for record in self.context.day_planner.list(self.current_date.isoformat()):
            block = BlockWidget(record, self.timeline); block.changed.connect(self._changed); block.renamed.connect(self._rename); block.removed.connect(self._delete); block.duplicated.connect(self._duplicate); block.notes_changed.connect(self._notes)
            block.setGeometry(LABEL_WIDTH+6, record["start_minute"]*PIXELS_PER_HOUR//60, max(80, self.timeline.width()-LABEL_WIDTH-12), max(30, record["duration_minutes"]*PIXELS_PER_HOUR//60)); block.show(); self.blocks.append(block)
        self._update_now()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for block in self.blocks: block.resize(max(80, self.timeline.width()-LABEL_WIDTH-12), block.height())
    def _create(self, minute, duration=30):
        text, ok = QInputDialog.getText(self, "New time block", f"{minute//60:02d}:{minute%60:02d}")
        if ok and text.strip(): self.context.day_planner.add(self.current_date.isoformat(), text.strip(), minute, duration); self.refresh()
    def _changed(self, block_id, start, duration): self.context.day_planner.update(block_id, start_minute=start, duration_minutes=duration); self.refresh()
    def _rename(self, block_id, title): self.context.day_planner.update(block_id, title=title); self.refresh()
    def _delete(self, block_id): self.context.day_planner.delete(block_id); self.refresh()
    def _duplicate(self, block_id): self.context.day_planner.duplicate(block_id); self.refresh()
    def _notes(self, block_id, notes): self.context.day_planner.update(block_id, notes=notes); self.refresh()
    def _schedule_task(self, title, minute, duration):
        self.context.day_planner.add(self.current_date.isoformat(), title, minute, duration)
        self.refresh()

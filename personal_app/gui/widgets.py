from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Compartment(QFrame):
    dropped = Signal(str, object)
    geometry_changed = Signal(str)

    def __init__(self, title: str, description: str = "", module_name: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Compartment")
        self.module_name = module_name or title
        self._drag_start = QPoint()
        self._global_start = QPoint()
        self._start_pos = QPoint()
        self._start_size = self.size()
        self._resize_edges: set[str] = set()
        self._grid_mode = False
        self.setMinimumSize(280, 210)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 7, 8, 8)
        self.layout.setSpacing(5)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setObjectName("CompartmentTitle")
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        resize_hint = QLabel("resize")
        resize_hint.setObjectName("ResizeGrip")
        resize_hint.setCursor(Qt.SizeFDiagCursor)
        resize_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        header.addWidget(label)
        header.addStretch(1)
        header.addWidget(resize_hint)
        self.resize_hint = resize_hint
        self.layout.addLayout(header)
        if description:
            desc = QLabel(description)
            desc.setObjectName("CompartmentDescription")
            desc.setWordWrap(True)
            self.layout.addWidget(desc)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            self._global_start = event.globalPosition().toPoint()
            self._start_pos = self.pos()
            self._start_size = self.size()
            self._resize_edges = self._resize_edges_at(self._drag_start)
            self.raise_()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._global_start
            parent = self.parentWidget()
            if self._resize_edges:
                x = self._start_pos.x()
                y = self._start_pos.y()
                width = self._start_size.width()
                height = self._start_size.height()
                if "right" in self._resize_edges:
                    width = self._start_size.width() + delta.x()
                if "bottom" in self._resize_edges:
                    height = self._start_size.height() + delta.y()
                if "left" in self._resize_edges:
                    x = self._start_pos.x() + delta.x()
                    width = self._start_size.width() - delta.x()
                if "top" in self._resize_edges:
                    y = self._start_pos.y() + delta.y()
                    height = self._start_size.height() - delta.y()
                x, y, width, height = self._clamp_resize(x, y, width, height)
                self.setGeometry(x, y, width, height)
            else:
                new_pos = self._start_pos + delta
                if parent:
                    new_pos.setX(max(0, min(new_pos.x(), parent.width() - self.width())))
                    new_pos.setY(max(0, min(new_pos.y(), parent.height() - self.height())))
                self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if event.button() == Qt.LeftButton:
            if self._resize_edges:
                self.geometry_changed.emit(self.module_name)
            else:
                self.dropped.emit(self.module_name, event.globalPosition().toPoint())
        super().mouseReleaseEvent(event)

    def _resize_edges_at(self, point: QPoint) -> set[str]:
        margin = 12
        edges = set()
        if point.x() <= margin:
            edges.add("left")
        elif point.x() >= self.width() - margin:
            edges.add("right")
        if point.y() <= margin:
            edges.add("top")
        elif point.y() >= self.height() - margin:
            edges.add("bottom")
        return edges

    def _clamp_resize(self, x: int, y: int, width: int, height: int) -> tuple[int, int, int, int]:
        parent = self.parentWidget()
        min_width = self.minimumWidth()
        min_height = self.minimumHeight()
        old_right = self._start_pos.x() + self._start_size.width()
        old_bottom = self._start_pos.y() + self._start_size.height()
        if width < min_width:
            if "left" in self._resize_edges:
                x = old_right - min_width
            width = min_width
        if height < min_height:
            if "top" in self._resize_edges:
                y = old_bottom - min_height
            height = min_height
        if parent:
            if x < 0:
                width += x
                x = 0
            if y < 0:
                height += y
                y = 0
            width = min(width, parent.width() - x)
            height = min(height, parent.height() - y)
        return x, y, max(min_width, width), max(min_height, height)

    def set_outline_colour(self, colour: str) -> None:
        self.setStyleSheet(
            f"""
            QFrame#Compartment {{
                background: #171d22;
                border: 1px solid {colour};
                border-radius: 9px;
            }}
            QFrame#Compartment[dragging="true"] {{
                border: 2px solid {colour};
            }}
            """
        )

    def set_grid_mode(self, enabled: bool = True) -> None:
        self._grid_mode = enabled
        self.resize_hint.setVisible(enabled)
        if enabled:
            self.setMinimumSize(80, 80)


class QuickAddBar(QWidget):
    added = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Quick add...")
        layout.addWidget(self.input, 1)
        for kind in ("Task", "Shopping", "Project", "Unwind"):
            button = QPushButton(kind)
            button.clicked.connect(lambda _=False, k=kind: self._emit(k))
            layout.addWidget(button)
        self.input.returnPressed.connect(lambda: self._emit("Task"))

    def _emit(self, kind: str) -> None:
        text = self.input.text().strip()
        if text:
            self.added.emit(kind, text)
            self.input.clear()


def subtle_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("Subtle")
    return button


def danger_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("Danger")
    return button

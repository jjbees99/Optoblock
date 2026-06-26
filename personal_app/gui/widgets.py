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
        self._resizing = False
        self.setMinimumSize(280, 210)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 12)
        self.layout.setSpacing(8)
        header = QHBoxLayout()
        grip = QLabel("::")
        grip.setObjectName("DragGrip")
        grip.setCursor(Qt.OpenHandCursor)
        label = QLabel(title)
        label.setObjectName("CompartmentTitle")
        resize_hint = QLabel("size")
        resize_hint.setObjectName("ResizeGrip")
        resize_hint.setCursor(Qt.SizeFDiagCursor)
        header.addWidget(grip)
        header.addWidget(label)
        header.addStretch(1)
        header.addWidget(resize_hint)
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
            self._resizing = self._is_resize_zone(self._drag_start)
            self.raise_()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._global_start
            parent = self.parentWidget()
            if self._resizing:
                width = max(self.minimumWidth(), self._start_size.width() + delta.x())
                height = max(self.minimumHeight(), self._start_size.height() + delta.y())
                if parent:
                    width = min(width, parent.width() - self.x())
                    height = min(height, parent.height() - self.y())
                self.resize(width, height)
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
            self.dropped.emit(self.module_name, event.globalPosition().toPoint())
            self.geometry_changed.emit(self.module_name)
        super().mouseReleaseEvent(event)

    def _is_resize_zone(self, point: QPoint) -> bool:
        return point.x() >= self.width() - 22 and point.y() >= self.height() - 22

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

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

    def __init__(self, title: str, description: str = "", module_name: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Compartment")
        self.module_name = module_name or title
        self._drag_start = QPoint()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 12)
        self.layout.setSpacing(8)
        header = QHBoxLayout()
        grip = QLabel("::")
        grip.setObjectName("DragGrip")
        grip.setCursor(Qt.OpenHandCursor)
        label = QLabel(title)
        label.setObjectName("CompartmentTitle")
        header.addWidget(grip)
        header.addWidget(label)
        header.addStretch(1)
        self.layout.addLayout(header)
        if description:
            desc = QLabel(description)
            desc.setObjectName("CompartmentDescription")
            desc.setWordWrap(True)
            self.layout.addWidget(desc)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            self.raise_()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if event.button() == Qt.LeftButton:
            self.dropped.emit(self.module_name, event.globalPosition().toPoint())
        super().mouseReleaseEvent(event)


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

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button, subtle_button


class UnwindPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Unwind", "Low-pressure recovery and creative routines, with suggestions when you need one.", "Unwind")
        self.context = context
        self.name = QLineEdit()
        self.name.setPlaceholderText("New unwind activity")
        self.kind = QComboBox()
        self.kind.addItems(["low energy", "creative", "physical", "social", "recovery"])
        self.time = QComboBox()
        self.time.addItems(["5 min", "15 min", "30 min", "1 hour+"])
        add_row = QHBoxLayout()
        add = QPushButton("Add")
        add.clicked.connect(self.add)
        for widget in (self.name, self.kind, self.time, add):
            add_row.addWidget(widget)
        self.list_widget = QListWidget()
        controls = QHBoxLayout()
        done = subtle_button("Done today")
        suggest = subtle_button("Suggest something")
        reset = subtle_button("Daily reset")
        delete = danger_button("Delete")
        done.clicked.connect(self.toggle)
        suggest.clicked.connect(self.suggest)
        reset.clicked.connect(self.reset)
        delete.clicked.connect(self.delete)
        for button in (done, suggest, reset, delete):
            controls.addWidget(button)
        self.suggestion = QLabel()
        self.layout.addLayout(add_row)
        self.layout.addWidget(self.list_widget, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.suggestion)
        self.refresh()

    def selected(self) -> dict | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None

    def refresh(self) -> None:
        self.list_widget.clear()
        for row in self.context.unwind.list():
            marker = "[x]" if row["done_today"] else "[ ]"
            item = QListWidgetItem(f"{marker} {row['name']} | {row['activity_type']} | {row['estimated_time']}")
            item.setData(256, row)
            self.list_widget.addItem(item)

    def add(self) -> None:
        if self.name.text().strip():
            self.context.unwind.add(self.name.text().strip(), self.kind.currentText(), self.time.currentText())
            self.name.clear()
            self.refresh()

    def toggle(self) -> None:
        row = self.selected()
        if row:
            self.context.unwind.set_done(row["id"], not row["done_today"])
            self.refresh()

    def suggest(self) -> None:
        row = self.context.unwind.suggest()
        self.suggestion.setText(f"Try: {row['name']} ({row['estimated_time']})" if row else "No matching suggestion right now.")

    def reset(self) -> None:
        self.context.unwind.reset_daily()
        self.refresh()

    def delete(self) -> None:
        row = self.selected()
        if row:
            self.context.unwind.delete(row["id"])
            self.refresh()

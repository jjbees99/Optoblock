from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QHBoxLayout,
    QVBoxLayout,
)


class FormDialog(QDialog):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.form = QFormLayout()
        buttons = QHBoxLayout()
        save = QPushButton("Save")
        cancel = QPushButton("Cancel")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addLayout(buttons)


class TaskDialog(FormDialog):
    def __init__(self, row: dict | None = None) -> None:
        super().__init__("Task")
        self.name = QLineEdit(row.get("name", "") if row else "")
        self.description = QTextEdit(row.get("description", "") if row else "")
        self.description.setFixedHeight(80)
        self.category = QLineEdit(row.get("category", "") if row else "")
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("yyyy-MM-dd")
        self.due_date.setSpecialValueText("No due date")
        self.due_date.setMinimumDate(QDate(2000, 1, 1))
        self.due_date.setDate(QDate.fromString(row.get("due_date", ""), "yyyy-MM-dd") if row and row.get("due_date") else QDate.currentDate())
        self.priority = QComboBox()
        self.priority.addItems(["Low", "Medium", "High"])
        self.priority.setCurrentText(row.get("priority", "Medium") if row else "Medium")
        self.form.addRow("Name", self.name)
        self.form.addRow("Description", self.description)
        self.form.addRow("Category", self.category)
        self.form.addRow("Due date", self.due_date)
        self.form.addRow("Priority", self.priority)

    def values(self) -> tuple[str, str, str, str, str]:
        due = self.due_date.date().toString("yyyy-MM-dd")
        return self.name.text().strip(), self.description.toPlainText().strip(), self.category.text().strip(), due, self.priority.currentText()


class ProjectDialog(FormDialog):
    def __init__(self, row: dict | None = None) -> None:
        super().__init__("Project")
        self.title_input = QLineEdit(row.get("title", "") if row else "")
        self.description = QTextEdit(row.get("description", "") if row else "")
        self.description.setFixedHeight(80)
        self.category = QLineEdit(row.get("category", "") if row else "")
        self.status = QComboBox()
        self.status.addItems(["Idea", "Planning", "In Progress", "Paused", "Completed", "Archived"])
        self.status.setCurrentText(row.get("status", "Idea") if row else "Idea")
        self.next_action = QLineEdit(row.get("next_action", "") if row else "")
        self.next_done = QCheckBox("Next action done")
        self.next_done.setChecked(bool(row.get("next_action_done", 0)) if row else False)
        self.form.addRow("Title", self.title_input)
        self.form.addRow("Description", self.description)
        self.form.addRow("Category", self.category)
        self.form.addRow("Status", self.status)
        self.form.addRow("Next action", self.next_action)
        self.form.addRow("", self.next_done)

    def values(self) -> tuple[str, str, str, str, str, bool]:
        return (
            self.title_input.text().strip(),
            self.description.toPlainText().strip(),
            self.category.text().strip(),
            self.status.currentText(),
            self.next_action.text().strip(),
            self.next_done.isChecked(),
        )


class ShoppingDialog(FormDialog):
    def __init__(self) -> None:
        super().__init__("Shopping item")
        self.name = QLineEdit()
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999)
        self.category = QLineEdit()
        self.list_type = QComboBox()
        self.list_type.addItems(["Grocery", "Amazon"])
        self.form.addRow("Item", self.name)
        self.form.addRow("Quantity", self.quantity)
        self.form.addRow("Category", self.category)
        self.form.addRow("List", self.list_type)

    def values(self) -> tuple[str, int, str, str]:
        return self.name.text().strip(), self.quantity.value(), self.category.text().strip(), self.list_type.currentText()

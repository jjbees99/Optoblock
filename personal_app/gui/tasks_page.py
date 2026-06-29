from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button


TASK_COLUMNS = ["Done", "Name", "Description", "Category", "Due Date", "Priority", "Status"]


class TasksPage(Compartment):
    archive_changed = Signal()

    def __init__(self, context: AppContext) -> None:
        super().__init__("To-Do List", "Spreadsheet-style task planning: edit cells, choose priority/status, then save.", "Tasks")
        self.context = context
        self.table = QTableWidget(0, len(TASK_COLUMNS))
        self.table.setHorizontalHeaderLabels(TASK_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        controls = QHBoxLayout()
        add = QPushButton("Add")
        save = subtle_button("Save")
        archive_done = subtle_button("Archive done")
        remove = subtle_button("Remove")
        add.clicked.connect(self.add_row)
        save.clicked.connect(self.save)
        archive_done.clicked.connect(self.archive_completed)
        remove.clicked.connect(self.delete_row)
        for button in (add, save, archive_done, remove):
            controls.addWidget(button)
        controls.addStretch(1)
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for row in self.context.tasks.list("All"):
            if row["status"] == "Archived":
                continue
            self.add_row(
                [
                    row["status"] == "Completed",
                    row["name"],
                    row["description"],
                    row["category"],
                    row["due_date"],
                    row["priority"],
                    row["status"],
                ]
            )

    def add_row(self, values: list | None = None) -> None:
        values = values or [False, "", "", "", "", "Medium", "Active"]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        done = QTableWidgetItem("")
        done.setFlags(done.flags() | Qt.ItemIsUserCheckable)
        done.setCheckState(Qt.Checked if values[0] else Qt.Unchecked)
        self.table.setItem(row_index, 0, done)

        for col, value in enumerate(values[1:5], start=1):
            self.table.setItem(row_index, col, QTableWidgetItem(str(value)))

        priority = QComboBox()
        priority.addItems(["Low", "Medium", "High"])
        priority.setCurrentText(values[5] or "Medium")
        self.table.setCellWidget(row_index, 5, priority)

        status = QComboBox()
        status.addItems(["Active", "Completed", "Archived"])
        status.setCurrentText(values[6] or "Active")
        self.table.setCellWidget(row_index, 6, status)

    def save(self) -> None:
        rows = []
        for row in range(self.table.rowCount()):
            name = self._cell(row, 1)
            if not name:
                continue
            done = self.table.item(row, 0).checkState() == Qt.Checked
            status = self._combo(row, 6)
            if done and status == "Active":
                status = "Completed"
            rows.append(
                {
                    "name": name,
                    "description": self._cell(row, 2),
                    "category": self._cell(row, 3),
                    "due_date": self._cell(row, 4),
                    "priority": self._combo(row, 5),
                    "status": status,
                    "completed_at": datetime.now().isoformat(timespec="seconds") if status == "Completed" else "",
                }
            )
        rows.extend(self.context.tasks.list("Archived"))
        self.context.tasks.replace_all(rows)
        self.refresh()

    def archive_completed(self) -> None:
        self.save()
        self.context.tasks.archive_completed()
        self.refresh()
        self.archive_changed.emit()

    def delete_row(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.save()

    def _cell(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

    def _combo(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        return widget.currentText() if isinstance(widget, QComboBox) else ""

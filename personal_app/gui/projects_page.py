from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button


PROJECT_COLUMNS = ["Colour", "Title", "Description", "Category", "Status", "Next Action", "Action Done"]
PROJECT_COLOURS = {
    "Red": "#e15b64",
    "Orange": "#f2a65a",
    "Yellow": "#f4d35e",
    "Green": "#63d471",
    "Blue": "#5aa9e6",
}


class ProjectsPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Projects", "Spreadsheet project board with status, next actions, and five colour progress markers.", "Projects")
        self.context = context
        self.table = QTableWidget(0, len(PROJECT_COLUMNS))
        self.table.setHorizontalHeaderLabels(PROJECT_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        controls = QHBoxLayout()
        add = QPushButton("Add")
        save = subtle_button("Save")
        convert = subtle_button("To task")
        archive = subtle_button("Archive")
        add.clicked.connect(self.add_row)
        save.clicked.connect(self.save)
        convert.clicked.connect(self.convert)
        archive.clicked.connect(self.archive_row)
        for button in (add, save, convert, archive):
            controls.addWidget(button)
        controls.addStretch(1)

        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for row in self.context.projects.list(include_archived=True):
            self.add_row(
                [
                    row.get("progress_colour") or "Red",
                    row["title"],
                    row["description"],
                    row["category"],
                    row["status"],
                    row["next_action"],
                    bool(row["next_action_done"]),
                ]
            )

    def add_row(self, values: list | None = None) -> None:
        values = values or ["Red", "", "", "", "Idea", "", False]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        colour = QComboBox()
        colour.addItems(list(PROJECT_COLOURS))
        colour.setCurrentText(values[0] if values[0] in PROJECT_COLOURS else "Red")
        colour.currentTextChanged.connect(lambda _text, row=row_index: self.paint_colour_cell(row))
        self.table.setCellWidget(row_index, 0, colour)

        for col, value in enumerate(values[1:4], start=1):
            self.table.setItem(row_index, col, QTableWidgetItem(str(value)))

        status = QComboBox()
        status.addItems(["Idea", "Planning", "In Progress", "Paused", "Completed", "Archived"])
        status.setCurrentText(values[4] or "Idea")
        self.table.setCellWidget(row_index, 4, status)

        self.table.setItem(row_index, 5, QTableWidgetItem(str(values[5])))
        done = QTableWidgetItem("")
        done.setFlags(done.flags() | Qt.ItemIsUserCheckable)
        done.setCheckState(Qt.Checked if values[6] else Qt.Unchecked)
        self.table.setItem(row_index, 6, done)
        self.paint_colour_cell(row_index)

    def paint_colour_cell(self, row: int) -> None:
        combo = self.table.cellWidget(row, 0)
        if not isinstance(combo, QComboBox):
            return
        colour_name = combo.currentText()
        colour = PROJECT_COLOURS.get(colour_name, PROJECT_COLOURS["Red"])
        combo.setStyleSheet(f"QComboBox {{ background: {colour}; color: #071010; font-weight: 700; }}")

    def save(self) -> None:
        rows = []
        for row in range(self.table.rowCount()):
            title = self._cell(row, 1)
            if not title:
                continue
            rows.append(
                {
                    "progress_colour": self._combo(row, 0) or "Red",
                    "title": title,
                    "description": self._cell(row, 2),
                    "category": self._cell(row, 3),
                    "status": self._combo(row, 4) or "Idea",
                    "next_action": self._cell(row, 5),
                    "next_action_done": int(self.table.item(row, 6).checkState() == Qt.Checked),
                }
            )
        self.context.projects.replace_all(rows)
        self.refresh()

    def convert(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        title = self._cell(row, 1)
        action = self._cell(row, 5)
        if action:
            self.context.tasks.add(action, f"From project: {title}", self._cell(row, 3), "", "Medium")
            self.table.item(row, 6).setCheckState(Qt.Checked)
            self.save()

    def archive_row(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            status = self.table.cellWidget(row, 4)
            if isinstance(status, QComboBox):
                status.setCurrentText("Archived")
            self.save()

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

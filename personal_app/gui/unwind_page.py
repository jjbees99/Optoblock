from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button


UNWIND_COLUMNS = ["Done", "Activity", "Category", "Time"]
CATEGORIES = ["low energy", "creative", "physical", "social", "recovery"]
TIMES = ["5 min", "15 min", "30 min", "1 hour+"]


class UnwindPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Unwind", "Spreadsheet reset list with category and time dropdowns for calm choices.", "Unwind")
        self.context = context
        self.table = QTableWidget(0, len(UNWIND_COLUMNS))
        self.table.setHorizontalHeaderLabels(UNWIND_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All categories", *CATEGORIES])
        self.category_filter.currentTextChanged.connect(self.refresh)

        controls = QHBoxLayout()
        add = QPushButton("Add")
        save = subtle_button("Save")
        done = subtle_button("Done today")
        suggest = subtle_button("Suggest")
        reset = subtle_button("Reset")
        add.clicked.connect(self.add_row)
        save.clicked.connect(self.save)
        done.clicked.connect(self.toggle)
        suggest.clicked.connect(self.suggest)
        reset.clicked.connect(self.reset)
        for button in (add, save, done, suggest, reset):
            controls.addWidget(button)
        controls.addStretch(1)

        self.suggestion = QLabel()
        self.suggestion.setObjectName("CompartmentDescription")
        self.layout.addWidget(self.category_filter)
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.suggestion)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        active_filter = self.category_filter.currentText() if hasattr(self, "category_filter") else "All categories"
        for row in self.context.unwind.list():
            if active_filter != "All categories" and row["activity_type"] != active_filter:
                continue
            self.add_row([bool(row["done_today"]), row["name"], row["activity_type"], row["estimated_time"]])

    def add_row(self, values: list | None = None) -> None:
        values = values or [False, "", "recovery", "15 min"]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        done = QTableWidgetItem("")
        done.setFlags(done.flags() | Qt.ItemIsUserCheckable)
        done.setCheckState(Qt.Checked if values[0] else Qt.Unchecked)
        self.table.setItem(row_index, 0, done)
        self.table.setItem(row_index, 1, QTableWidgetItem(str(values[1])))

        category = QComboBox()
        category.addItems(CATEGORIES)
        category.setCurrentText(values[2] if values[2] in CATEGORIES else "recovery")
        self.table.setCellWidget(row_index, 2, category)

        time = QComboBox()
        time.addItems(TIMES)
        time.setCurrentText(values[3] if values[3] in TIMES else "15 min")
        self.table.setCellWidget(row_index, 3, time)

    def save(self) -> None:
        rows = []
        active_filter = self.category_filter.currentText()
        for row in range(self.table.rowCount()):
            name = self._cell(row, 1)
            if not name:
                continue
            rows.append(
                {
                    "done_today": int(self.table.item(row, 0).checkState() == Qt.Checked),
                    "name": name,
                    "activity_type": self._combo(row, 2) or "recovery",
                    "estimated_time": self._combo(row, 3) or "15 min",
                }
            )
        if active_filter != "All categories":
            rows.extend(row for row in self.context.unwind.list() if row["activity_type"] != active_filter)
        self.context.unwind.replace_all(rows)
        self.refresh()

    def toggle(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
            self.save()

    def suggest(self) -> None:
        self.save()
        row = self.context.unwind.suggest()
        self.suggestion.setText(f"Try: {row['name']} ({row['activity_type']}, {row['estimated_time']})" if row else "No matching suggestion right now.")

    def reset(self) -> None:
        self.save()
        self.context.unwind.reset_daily()
        self.refresh()

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

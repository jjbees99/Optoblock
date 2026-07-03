from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button, subtle_button


COLUMNS = ["Date", "Type", "Category", "Description", "Amount", "Account"]


class FinancePage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Financial Tracker", "Spreadsheet-style income, spending, categories, accounts, and balance.", "Finance")
        self.context = context
        self._loading = False
        self._save_timer = QTimer(self); self._save_timer.setSingleShot(True); self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self.save)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(480)
        self.table.itemChanged.connect(self._schedule_save)

        controls = QHBoxLayout()
        add = QPushButton("Add new")
        add_many = subtle_button("Add 10 rows")
        delete = danger_button("Delete row")
        save = subtle_button("Save sheet")
        add.clicked.connect(self.add_row)
        add_many.clicked.connect(lambda: [self.add_row() for _ in range(10)])
        delete.clicked.connect(self.delete_row)
        save.clicked.connect(self.save)
        for button in (add, add_many, delete, save):
            controls.addWidget(button)
        controls.addStretch(1)

        self.totals = QLabel()
        self.totals.setObjectName("TotalsLabel")
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.totals)
        self.refresh()

    def refresh(self) -> None:
        self._save_timer.stop(); self._loading = True
        self.table.setRowCount(0)
        for row in self.context.finance.list():
            self.add_row(
                [
                    row["entry_date"],
                    row["entry_type"],
                    row["category"],
                    row["description"],
                    f"{float(row['amount'] or 0):.2f}",
                    row["account"],
                ]
            )
        self.update_totals()
        self._loading = False

    def add_row(self, values: list[str] | None = None) -> None:
        values = values or ["", "Expense", "", "", "0.00", ""]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        for col, value in enumerate(values):
            if col == 1:
                combo = QComboBox()
                combo.addItems(["Expense", "Income"])
                combo.setCurrentText("Income" if str(value).strip().lower() == "income" else "Expense")
                self.table.setCellWidget(row_index, col, combo)
                combo.currentTextChanged.connect(self._schedule_save)
                continue
            item = QTableWidgetItem(str(value))
            if col == 4:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, col, item)
        if values == ["", "Expense", "", "", "0.00", ""]: self._schedule_save()

    def delete_row(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.save()

    def save(self) -> None:
        if self._loading: return
        self._save_timer.stop()
        rows = []
        for row in range(self.table.rowCount()):
            values = [self._cell(row, col) for col in range(len(COLUMNS))]
            if not any(values):
                continue
            rows.append(
                {
                    "entry_date": values[0],
                    "entry_type": values[1],
                    "category": values[2],
                    "description": values[3],
                    "amount": values[4] or 0,
                    "account": values[5],
                }
            )
        self.context.finance.replace_all(rows)
        self.update_totals()

    def save_now(self) -> None:
        self.save()

    def _schedule_save(self, *_args) -> None:
        if not self._loading: self._save_timer.start()

    def update_totals(self) -> None:
        totals = self.context.finance.totals()
        self.totals.setText(f"Income: GBP {totals['income']:.2f}    Expenses: GBP {totals['expenses']:.2f}    Balance: GBP {totals['balance']:.2f}")

    def _cell(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        if isinstance(widget, QComboBox):
            return widget.currentText()
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

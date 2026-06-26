from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, danger_button, subtle_button


COLUMNS = ["Date", "Type", "Category", "Description", "Amount", "Account"]


class FinancePage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Financial Tracker", "Spreadsheet-style income, spending, categories, accounts, and balance.", "Finance")
        self.context = context
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        controls = QHBoxLayout()
        add = QPushButton("Add row")
        delete = danger_button("Delete row")
        save = subtle_button("Save sheet")
        add.clicked.connect(self.add_row)
        delete.clicked.connect(self.delete_row)
        save.clicked.connect(self.save)
        for button in (add, delete, save):
            controls.addWidget(button)
        controls.addStretch(1)

        self.totals = QLabel()
        self.totals.setObjectName("TotalsLabel")
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.totals)
        self.refresh()

    def refresh(self) -> None:
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
                continue
            item = QTableWidgetItem(str(value))
            if col == 4:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index, col, item)

    def delete_row(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.save()

    def save(self) -> None:
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

    def update_totals(self) -> None:
        totals = self.context.finance.totals()
        self.totals.setText(f"Income: GBP {totals['income']:.2f}    Expenses: GBP {totals['expenses']:.2f}    Balance: GBP {totals['balance']:.2f}")

    def _cell(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        if isinstance(widget, QComboBox):
            return widget.currentText()
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

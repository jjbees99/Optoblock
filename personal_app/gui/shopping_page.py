from urllib.parse import quote
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button


SHOPPING_COLUMNS = ["Bought", "Item", "Quantity", "Category", "List"]


class ShoppingPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Shopping", "Spreadsheet shopping list for groceries and Amazon, with email handoff.", "Shopping")
        self.context = context
        self.table = QTableWidget(0, len(SHOPPING_COLUMNS))
        self.table.setHorizontalHeaderLabels(SHOPPING_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(24)

        controls = QHBoxLayout()
        add = QPushButton("Add")
        save = subtle_button("Save")
        move = subtle_button("Move")
        archive = subtle_button("Archive bought")
        email = subtle_button("Email")
        add.clicked.connect(self.add_row)
        save.clicked.connect(self.save)
        move.clicked.connect(self.move)
        archive.clicked.connect(self.archive)
        email.clicked.connect(self.email_list)
        for button in (add, save, move, archive, email):
            controls.addWidget(button)
        controls.addStretch(1)

        self.notice = QLabel()
        self.notice.setObjectName("CompartmentDescription")
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.notice)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for row in self.context.shopping.list(include_archived=False):
            self.add_row([bool(row["bought"]), row["name"], row["quantity"], row["category"], row["list_type"]])

    def add_row(self, values: list | None = None) -> None:
        values = values or [False, "", 1, "", "Grocery"]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        bought = QTableWidgetItem("")
        bought.setFlags(bought.flags() | Qt.ItemIsUserCheckable)
        bought.setCheckState(Qt.Checked if values[0] else Qt.Unchecked)
        self.table.setItem(row_index, 0, bought)

        self.table.setItem(row_index, 1, QTableWidgetItem(str(values[1])))
        quantity = QTableWidgetItem(str(values[2] or 1))
        quantity.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row_index, 2, quantity)
        self.table.setItem(row_index, 3, QTableWidgetItem(str(values[3])))

        list_type = QComboBox()
        list_type.addItems(["Grocery", "Amazon"])
        list_type.setCurrentText(values[4] if values[4] in ("Grocery", "Amazon") else "Grocery")
        self.table.setCellWidget(row_index, 4, list_type)

    def save(self) -> None:
        rows = []
        for row in range(self.table.rowCount()):
            name = self._cell(row, 1)
            if not name:
                continue
            rows.append(
                {
                    "bought": int(self.table.item(row, 0).checkState() == Qt.Checked),
                    "name": name,
                    "quantity": self._quantity(row),
                    "category": self._cell(row, 3),
                    "list_type": self._combo(row, 4) or "Grocery",
                    "archived": 0,
                }
            )
        self.context.shopping.replace_all(rows)
        self.refresh()

    def toggle(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
            self.save()

    def move(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            combo = self.table.cellWidget(row, 4)
            if isinstance(combo, QComboBox):
                combo.setCurrentText("Amazon" if combo.currentText() == "Grocery" else "Grocery")
            self.save()

    def archive(self) -> None:
        self.save()
        self.context.shopping.archive_bought()
        self.refresh()

    def clear(self) -> None:
        self.save()
        self.context.shopping.clear_bought()
        self.refresh()

    def delete_row(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.save()

    def email_list(self) -> None:
        self.save()
        recipient = "jakebees00@gmail.com"
        subject_text = "Optoblock shopping list"
        body_text = self.context.shopping.email_body()
        QGuiApplication.clipboard().setText(body_text)
        backup_path = Path.home() / "Documents" / "optoblock-shopping-list.txt"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(body_text, encoding="utf-8")
        subject = quote(subject_text)
        body = quote(body_text)
        url = QUrl(f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient}&su={subject}&body={body}")
        opened = QDesktopServices.openUrl(url)
        if opened:
            self.notice.setText("Opened Gmail in your browser. The list is also copied to clipboard and saved in Documents.")
        else:
            self.notice.setText(f"Could not open Gmail, but the list is copied and saved to {backup_path}.")

    def _cell(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

    def _combo(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        return widget.currentText() if isinstance(widget, QComboBox) else ""

    def _quantity(self, row: int) -> int:
        try:
            return max(1, int(self._cell(row, 2)))
        except ValueError:
            return 1

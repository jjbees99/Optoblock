from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button
from personal_app.gui.column_preferences import configure_columns


CONFIG = {
    "Bills & Renewals": ("bills", ["Title", "Amount", "Due date", "Recurrence", "Status", "Notes"],
        {3: ["One-off", "Weekly", "Monthly", "Yearly"], 4: ["Upcoming", "Paid", "Cancelled"]}),
    "Documents": ("documents", ["Title", "Category", "Note", "Expiry date", "Location / reference"],
        {1: ["ID", "Housing", "University/work", "Medical", "Finance", "Travel", "Other"]}),
    "Errands & Appointments": ("errands", ["Title", "Date / time", "Location", "Priority", "Status", "Notes"],
        {3: ["Low", "Medium", "High"], 4: ["Not started", "Planned", "Done"]}),
    "Follow-Up": ("follow_ups", ["Person / organisation", "Reason", "Method", "Due date", "Status", "Notes"],
        {2: ["Email", "Call", "Message", "In person"], 4: ["Waiting", "Needs reply", "Completed"]}),
    "Travel & Plans": ("travel_plans", ["Title", "Start date", "End date", "Destination", "Transport", "Checklist (; separated)", "Budget", "Notes", "Status"],
        {8: ["Active", "Completed"]}),
    "Home / Flat / Living": ("home_items", ["Title", "Category", "Due date", "Repeat", "Status", "Notes"],
        {1: ["Cleaning", "Repair", "Laundry", "Supplies", "Bills", "Other"], 4: ["Not started", "Planned", "Done"]}),
}


class LifeAdminPage(Compartment):
    archive_changed = Signal()

    def __init__(self, context: AppContext, module_name: str) -> None:
        table_name, headers, combos = CONFIG[module_name]
        super().__init__(module_name, self._description(module_name), module_name)
        self.context, self.table_name, self.headers, self.combos = context, table_name, headers, combos
        self._loading = False
        self._save_timer = QTimer(self); self._save_timer.setSingleShot(True); self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(lambda: self.save(False))
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search this module...")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.search, 1)
        self.group_label = QLabel()
        filters.addWidget(self.group_label)
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self._schedule_save)
        configure_columns(self.table, context, module_name, headers)
        controls = QHBoxLayout()
        actions = [("Add new", self.add_row)]
        if self.table_name != "documents":
            actions.append((self._action_text(), self.mark_done))
        actions.append(("Archive selected", self.archive_selected))
        for text, handler in actions:
            button = QPushButton(text) if text == "Add new" else subtle_button(text)
            button.clicked.connect(handler)
            controls.addWidget(button)
        controls.addStretch(1)
        self.layout.addLayout(filters)
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.refresh()

    @staticmethod
    def _description(name: str) -> str:
        descriptions = {
            "Documents": "Store references and locations only — never passwords or sensitive document contents.",
            "Errands & Appointments": "Today, upcoming and completed real-world admin.",
            "Travel & Plans": "Trips, transport, budgets and lightweight packing/admin checklists.",
        }
        return descriptions.get(name, "Keep this area current; archive finished items when they no longer need attention.")

    def _action_text(self) -> str:
        return "Mark paid" if self.table_name == "bills" else "Mark completed"

    def refresh(self, *_args) -> None:
        self._save_timer.stop(); self._loading = True
        self.table.setRowCount(0)
        rows = self.context.life_admin.list(self.table_name, search=self.search.text() if hasattr(self, "search") else "")
        if self.table_name == "errands":
            groups = {"Today": 0, "Upcoming": 0, "Done": 0}
            today = date.today().isoformat()
            for row in rows:
                groups["Done" if row["status"] == "Done" else "Today" if row["event_at"][:10] == today else "Upcoming"] += 1
            self.group_label.setText("  ".join(f"{k}: {v}" for k, v in groups.items()))
        for record in rows:
            values = [record[column] for column in self.context.life_admin.TABLES[self.table_name]]
            self.add_row(values, record["id"])
        self._loading = False

    def add_row(self, values=None, item_id=None) -> None:
        values = list(values or ["" for _ in self.headers])
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(len(self.headers)):
            value = values[col] if col < len(values) else ""
            if col in self.combos:
                widget = QComboBox()
                widget.addItems(self.combos[col])
                widget.setCurrentText(str(value) if value else self.combos[col][0])
                widget.currentTextChanged.connect(self._schedule_save)
                self.table.setCellWidget(row, col, widget)
            else:
                item = QTableWidgetItem(str(value))
                if col == 0 and item_id:
                    item.setData(Qt.UserRole, item_id)
                self.table.setItem(row, col, item)
        self._highlight(row, values)

    def save(self, refresh: bool = True) -> None:
        if self._loading: return
        self._save_timer.stop()
        columns = self.context.life_admin.TABLES[self.table_name]
        rows = []
        for row in range(self.table.rowCount()):
            values = [self._value(row, col) for col in range(len(columns))]
            if not values[0]:
                continue
            if self.table_name == "travel_plans" and values[5] and not values[5].startswith("["):
                values[5] = "; ".join(part.strip() for part in values[5].split(";") if part.strip())
            rows.append(dict(zip(columns, values)))
        self.context.life_admin.replace_active(self.table_name, rows)
        if refresh: self.refresh()

    def _schedule_save(self, *_args) -> None:
        if not self._loading: self._save_timer.start()

    def mark_done(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        status_col = next((col for col, name in enumerate(self.headers) if name == "Status"), None)
        if status_col is None:
            return
        status = "Paid" if self.table_name == "bills" else "Completed" if self.table_name in ("follow_ups", "travel_plans") else "Done"
        widget = self.table.cellWidget(row, status_col)
        if isinstance(widget, QComboBox):
            widget.setCurrentText(status)
        self.save()

    def archive_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        item_id = item.data(Qt.UserRole) if item else None
        if item_id:
            self.context.life_admin.archive(self.table_name, int(item_id))
            self.refresh()
            self.archive_changed.emit()

    def _value(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        if isinstance(widget, QComboBox):
            return widget.currentText()
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

    def _highlight(self, row: int, values: list) -> None:
        status_col = next((col for col, name in enumerate(self.headers) if name == "Status"), None)
        if status_col is not None and status_col < len(values) and str(values[status_col]) in ("Paid", "Cancelled", "Completed", "Done"):
            return
        date_col = 2 if self.table_name in ("bills", "home_items") else 3 if self.table_name == "follow_ups" else None
        if date_col is None or date_col >= len(values) or not values[date_col]:
            return
        try:
            due = date.fromisoformat(str(values[date_col])[:10])
        except ValueError:
            return
        colour = QColor("#7f1d1d") if due < date.today() else QColor("#78350f") if due <= date.today() + timedelta(days=7) else None
        if colour:
            for col in range(len(self.headers)):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(colour)

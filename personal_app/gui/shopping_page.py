from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTabWidget, QWidget, QVBoxLayout

from personal_app.app import AppContext
from personal_app.gui.dialogs import ShoppingDialog
from personal_app.gui.widgets import Compartment, danger_button, subtle_button


class ShoppingPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Shopping", "Two tick-off lists for groceries and Amazon/general purchases.", "Shopping")
        self.context = context
        self.tabs = QTabWidget()
        self.lists: dict[str, QListWidget] = {}
        for name in ("Grocery", "Amazon"):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            list_widget = QListWidget()
            layout.addWidget(list_widget)
            self.tabs.addTab(widget, name)
            self.lists[name] = list_widget
        controls = QHBoxLayout()
        add = QPushButton("Add")
        toggle = subtle_button("Bought")
        move = subtle_button("Move list")
        archive = subtle_button("Archive bought")
        clear = subtle_button("Clear bought")
        email = subtle_button("Email list")
        delete = danger_button("Delete")
        add.clicked.connect(self.add)
        toggle.clicked.connect(self.toggle)
        move.clicked.connect(self.move)
        archive.clicked.connect(self.archive)
        clear.clicked.connect(self.clear)
        email.clicked.connect(self.email_list)
        delete.clicked.connect(self.delete)
        for button in (add, toggle, move, archive, clear, email, delete):
            controls.addWidget(button)
        self.notice = QLabel()
        self.notice.setObjectName("CompartmentDescription")
        self.layout.addWidget(self.tabs, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.notice)
        self.refresh()

    def selected(self) -> dict | None:
        current = self.lists[self.tabs.tabText(self.tabs.currentIndex())]
        item = current.currentItem()
        return item.data(256) if item else None

    def refresh(self) -> None:
        for list_type, widget in self.lists.items():
            widget.clear()
            for row in self.context.shopping.list(list_type):
                marker = "[x]" if row["bought"] else "[ ]"
                text = f"{marker} {row['quantity']} x {row['name']} | {row['category']}"
                item = QListWidgetItem(text)
                item.setData(256, row)
                widget.addItem(item)

    def add(self) -> None:
        dialog = ShoppingDialog()
        if dialog.exec():
            name, quantity, category, list_type = dialog.values()
            if name:
                self.context.shopping.add(name, quantity, category, list_type)
                self.refresh()

    def toggle(self) -> None:
        row = self.selected()
        if row:
            self.context.shopping.set_bought(row["id"], not row["bought"])
            self.refresh()

    def move(self) -> None:
        row = self.selected()
        if row:
            self.context.shopping.move(row["id"])
            self.refresh()

    def archive(self) -> None:
        self.context.shopping.archive_bought()
        self.refresh()

    def clear(self) -> None:
        self.context.shopping.clear_bought()
        self.refresh()

    def delete(self) -> None:
        row = self.selected()
        if row:
            self.context.shopping.delete(row["id"])
            self.refresh()

    def email_list(self) -> None:
        recipient = "jakebees00@gmail.com"
        subject = quote("Optoblock shopping list")
        body = quote(self.context.shopping.email_body())
        url = QUrl(f"mailto:{recipient}?subject={subject}&body={body}")
        opened = QDesktopServices.openUrl(url)
        self.notice.setText("Opened your email app with the shopping list ready to send." if opened else "Could not open the default email app.")

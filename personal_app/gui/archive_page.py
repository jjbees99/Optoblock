from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QPushButton

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment


class ArchivePage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Archive", "Park old tasks and restore anything that becomes relevant again.", "Archive")
        self.context = context
        self.list_widget = QListWidget()
        restore = QPushButton("Restore selected task")
        restore.clicked.connect(self.restore)
        self.layout.addWidget(QLabel("Archived tasks and shopping/project records stay in the database."))
        self.layout.addWidget(self.list_widget, 1)
        self.layout.addWidget(restore)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        for row in self.context.tasks.list("Archived"):
            item = QListWidgetItem(f"Task: {row['name']} | {row['priority']} | {row['category']}")
            item.setData(256, row)
            self.list_widget.addItem(item)

    def restore(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self.context.tasks.restore(item.data(256)["id"])
            self.refresh()

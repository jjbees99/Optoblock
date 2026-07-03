from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment


class ArchivePage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Archive", "Search archived items from every module and restore them in place.", "Archive")
        self.context = context
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search archive...")
        self.search.textChanged.connect(self.refresh)
        self.list_widget = QListWidget()
        restore = QPushButton("Restore selected task")
        restore.clicked.connect(self.restore)
        self.layout.addWidget(QLabel("Each item keeps its original module."))
        self.layout.addWidget(self.search)
        self.layout.addWidget(self.list_widget, 1)
        self.layout.addWidget(restore)
        self.refresh()

    def refresh(self, *_args) -> None:
        self.list_widget.clear()
        needle = self.search.text().casefold() if hasattr(self, "search") else ""
        def add(kind, module, row, text):
            label = f"{module}: {text}"
            if not needle or needle in label.casefold():
                item = QListWidgetItem(label)
                item.setData(256, (kind, row))
                self.list_widget.addItem(item)
        for row in self.context.tasks.list("Archived"):
            add("task", "To-Do List", row, f"{row['name']} | {row['priority']} | {row['category']}")
        for row in self.context.brain_dump.archived():
            add("note", "Inbox", row, row["body"])
        for row in self.context.projects.list(include_archived=True):
            if row["status"] == "Archived":
                add("project", "Projects", row, row["title"])
        for row in self.context.shopping.list(include_archived=True):
            if row["archived"]:
                add("shopping", "Shopping", row, row["name"])
        labels = {"bills": "Bills & Renewals", "documents": "Documents", "errands": "Errands & Appointments",
                  "follow_ups": "Follow-Up", "travel_plans": "Travel & Plans", "home_items": "Home / Flat / Living"}
        for table, module in labels.items():
            for row in self.context.life_admin.list(table, archived=True):
                add(table, module, row, row.get("title") or row.get("contact") or "Untitled")

    def restore(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            kind, row = item.data(256)
            if kind == "note":
                self.context.brain_dump.restore(row["id"])
            elif kind == "task":
                self.context.tasks.restore(row["id"])
            elif kind == "project":
                self.context.db.execute("UPDATE projects SET status='Idea' WHERE id=?", (row["id"],))
            elif kind == "shopping":
                self.context.db.execute("UPDATE shopping_items SET archived=0 WHERE id=?", (row["id"],))
            else:
                self.context.life_admin.restore(kind, row["id"])
            self.refresh()

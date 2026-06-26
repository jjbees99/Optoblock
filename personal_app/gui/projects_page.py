from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton

from personal_app.app import AppContext
from personal_app.gui.dialogs import ProjectDialog
from personal_app.gui.widgets import Compartment, danger_button, subtle_button


class ProjectsPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Projects", "Capture future ideas, track status, and turn next actions into tasks.", "Projects")
        self.context = context
        self.list_widget = QListWidget()
        controls = QHBoxLayout()
        add = QPushButton("Add")
        edit = subtle_button("Edit")
        convert = subtle_button("Next action to task")
        archive = subtle_button("Archive")
        delete = danger_button("Delete")
        add.clicked.connect(self.add)
        edit.clicked.connect(self.edit)
        convert.clicked.connect(self.convert)
        archive.clicked.connect(self.archive)
        delete.clicked.connect(self.delete)
        for button in (add, edit, convert, archive, delete):
            controls.addWidget(button)
        self.layout.addWidget(self.list_widget, 1)
        self.layout.addLayout(controls)
        self.refresh()

    def selected(self) -> dict | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None

    def refresh(self) -> None:
        self.list_widget.clear()
        for row in self.context.projects.list():
            done = "done" if row["next_action_done"] else "open"
            text = f"{row['title']} | {row['category']} | {row['status']} | next: {row['next_action']} ({done})"
            item = QListWidgetItem(text)
            item.setData(256, row)
            self.list_widget.addItem(item)

    def add(self) -> None:
        dialog = ProjectDialog()
        if dialog.exec():
            title, desc, category, status, next_action, _done = dialog.values()
            if title:
                self.context.projects.add(title, desc, category, status, next_action)
                self.refresh()

    def edit(self) -> None:
        row = self.selected()
        if not row:
            return
        dialog = ProjectDialog(row)
        if dialog.exec():
            values = dialog.values()
            if values[0]:
                self.context.projects.update(row["id"], *values)
                self.refresh()

    def convert(self) -> None:
        row = self.selected()
        if row:
            self.context.projects.convert_next_action(row["id"], self.context.tasks)
            self.refresh()

    def archive(self) -> None:
        row = self.selected()
        if row:
            self.context.projects.archive(row["id"])
            self.refresh()

    def delete(self) -> None:
        row = self.selected()
        if row:
            self.context.projects.delete(row["id"])
            self.refresh()

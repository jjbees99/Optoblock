from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button


class DashboardPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Today / Dashboard", "Your daily focus, live totals, next action, and unwind nudge.", "Dashboard")
        self.context = context
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.focus = QTextEdit()
        self.focus.setPlaceholderText("Today focus")
        self.focus.setFixedHeight(90)
        self.focus.setText(context.settings.get("daily_focus") or "")
        self.focus.textChanged.connect(self._save_focus)
        refresh = subtle_button("Refresh")
        refresh.clicked.connect(self.refresh)
        self.layout.addWidget(self.summary)
        self.layout.addWidget(self.focus)
        self.layout.addWidget(refresh)
        self.refresh()

    def _save_focus(self) -> None:
        self.context.settings.set("daily_focus", self.focus.toPlainText().strip())

    def refresh(self) -> None:
        tasks = self.context.tasks.stats()
        shopping = self.context.shopping.stats()
        suggestion = self.context.unwind.suggest()
        suggest_text = suggestion["name"] if suggestion else "No unwind ideas left today."
        highs = ", ".join(row["name"] for row in tasks["high"]) or "None"
        self.summary.setText(
            f"Active tasks: {tasks['active']}\n"
            f"Completed tasks: {tasks['completed']}\n"
            f"Completed this week: {tasks['week_done']}\n"
            f"High priority: {highs}\n"
            f"Next project action: {self.context.projects.next_action()}\n"
            f"Grocery still needed: {shopping['grocery']}\n"
            f"Amazon still needed: {shopping['amazon']}\n"
            f"Shopping bought: {shopping['bought']}\n"
            f"Projects in progress: {self.context.projects.in_progress_count()}\n"
            f"Suggested unwind: {suggest_text}"
        )


class BrainDumpPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Brain Dump", "Drop messy thoughts here, then turn the useful ones into plans later.", "Brain Dump")
        self.context = context
        self.text = QTextEdit()
        self.text.setPlaceholderText("Messy thoughts, loose ideas, reminders...")
        save = subtle_button("Save brain dump")
        save.clicked.connect(self.save)
        self.items = QLabel()
        self.items.setWordWrap(True)
        self.layout.addWidget(self.text)
        self.layout.addWidget(save)
        self.layout.addWidget(self.items)
        self.refresh()

    def save(self) -> None:
        body = self.text.toPlainText().strip()
        if body:
            self.context.brain_dump.add(body)
            self.text.clear()
            self.refresh()

    def refresh(self) -> None:
        rows = self.context.brain_dump.list()[:5]
        self.items.setText("\n\n".join(row["body"] for row in rows) or "No saved brain dumps yet.")

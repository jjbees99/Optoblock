from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from personal_app.app import AppContext
from personal_app.gui.dashboard_board import DashboardBoard
from personal_app.gui.module_registry import MODULE_OUTLINES, MODULE_TITLES, module_factory
from personal_app.gui.styles import NOTION_DARK, NOTION_LIGHT


PRIMARY_MODULES = [
    "Dashboard", "Tasks", "Projects", "Shopping", "Brain Dump Scanner",
    "Bills & Renewals", "Documents", "Errands & Appointments", "Follow-Up",
    "Travel & Plans", "Home / Flat / Living", "Journal", "Notes", "Archive",
]
MORE_MODULES = ["Finance", "Recipes", "Focus Timer", "Voice Brain Dump", "Unwind", "Settings"]


class MainWindow(QMainWindow):
    """Focused workspace shell; module implementations remain independent and reusable."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.widgets_by_module: dict[str, QWidget] = {}
        self.nav_rows: dict[int, str] = {}
        self._page_transition: QParallelAnimationGroup | None = None
        self._transition_widget: QWidget | None = None
        self.setWindowTitle("Optoblock — Life Admin")
        self.resize(1280, 820)
        self.setMinimumSize(900, 620)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(244)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 22, 12, 18)
        side.setSpacing(10)
        brand = QLabel("Optoblock")
        brand.setObjectName("AppName")
        caption = QLabel("Life Admin OS")
        caption.setObjectName("SidebarCaption")
        side.addWidget(brand)
        side.addWidget(caption)

        self.navigation = QListWidget()
        self.navigation.setObjectName("SidebarNav")
        self.navigation.setFocusPolicy(Qt.NoFocus)
        self._add_section("Workspace", PRIMARY_MODULES)
        self._add_section("More", MORE_MODULES)
        self.navigation.currentRowChanged.connect(self._navigation_changed)
        side.addWidget(self.navigation, 1)
        self.theme_toggle = QPushButton()
        self.theme_toggle.setObjectName("ThemeToggle")
        self.theme_toggle.clicked.connect(self.toggle_theme)
        side.addWidget(self.theme_toggle)
        footer = QLabel("Everything stays on this device")
        footer.setObjectName("SidebarFooter")
        side.addWidget(footer)

        content = QFrame()
        content.setObjectName("ContentArea")
        self.content = content
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(44, 34, 44, 36)
        content_layout.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.setObjectName("PageStack")
        content_layout.addWidget(self.stack)
        shell.addWidget(sidebar)
        shell.addWidget(content, 1)

        self.apply_theme()
        first_row = next(row for row, name in self.nav_rows.items() if name == "Dashboard")
        self.navigation.setCurrentRow(first_row)
        if not self.context.journal.completed_today():
            QTimer.singleShot(500, self._show_journal_reminder)

    def _add_section(self, title: str, modules: list[str]) -> None:
        heading = QListWidgetItem(title.upper())
        heading.setFlags(Qt.NoItemFlags)
        heading.setData(Qt.UserRole, "section")
        self.navigation.addItem(heading)
        for module in modules:
            item = QListWidgetItem(self._display_name(module))
            item.setData(Qt.UserRole, module)
            colour = MODULE_OUTLINES.get(module, "#cbd5e1")
            marker = QPixmap(9, 22)
            marker.fill(Qt.transparent)
            from PySide6.QtGui import QPainter
            painter = QPainter(marker)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(colour)); painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(1, 3, 5, 16, 2, 2); painter.end()
            item.setIcon(QIcon(marker))
            self.navigation.addItem(item)
            self.nav_rows[self.navigation.count() - 1] = module

    @staticmethod
    def _display_name(module: str) -> str:
        aliases = {
            "Tasks": "To-Do", "Brain Dump Scanner": "Brain Dump",
            "Documents": "Documents", "Follow-Up": "Follow-Ups",
            "Home / Flat / Living": "Home / Flat",
        }
        return aliases.get(module, MODULE_TITLES[module])

    def _navigation_changed(self, row: int) -> None:
        module = self.nav_rows.get(row)
        if not module:
            return
        colour = MODULE_OUTLINES.get(module, "#cbd5e1")
        self.content.setStyleSheet(f"QFrame#ContentArea {{ border: 3px solid {colour}; border-radius: 10px; }}")
        widget = self.widgets_by_module.get(module)
        if widget is None:
            if module == "Dashboard":
                widget = DashboardBoard(self.context, self.refresh_destination_modules)
            else:
                widget = module_factory(self.context, module, self.refresh_appearance)()
                widget.module_name = module
                widget.set_grid_mode(False)
            if hasattr(widget, "items_added"):
                widget.items_added.connect(self.refresh_destination_modules)
            if hasattr(widget, "archive_changed"):
                widget.archive_changed.connect(lambda: self.refresh_module("Archive"))
            self.widgets_by_module[module] = widget
            self.stack.addWidget(widget)
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()
        self.stack.setCurrentWidget(widget)
        self._animate_page(widget)

    def _animate_page(self, widget: QWidget) -> None:
        """Fade and slide the active page in, without blocking rapid navigation."""
        if self._page_transition is not None:
            self._page_transition.stop()
        if self._transition_widget is not None:
            self._transition_widget.setGraphicsEffect(None)

        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)

        destination = widget.pos()
        # Some pages expose domain actions named ``move`` (for example Shopping),
        # so call QWidget's geometry method explicitly rather than the override.
        QWidget.move(widget, destination + QPoint(28, 0))

        fade = QPropertyAnimation(effect, b"opacity", widget)
        fade.setDuration(260)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        slide = QPropertyAnimation(widget, b"pos", widget)
        slide.setDuration(320)
        slide.setStartValue(destination + QPoint(28, 0))
        slide.setEndValue(destination)
        slide.setEasingCurve(QEasingCurve.OutCubic)

        transition = QParallelAnimationGroup(self)
        transition.addAnimation(fade)
        transition.addAnimation(slide)
        transition.finished.connect(lambda w=widget, e=effect: self._finish_page_transition(w, e))
        self._page_transition = transition
        self._transition_widget = widget
        transition.start()

    def _finish_page_transition(self, widget: QWidget, effect: QGraphicsOpacityEffect) -> None:
        if widget.graphicsEffect() is effect:
            effect.setOpacity(1.0)
            widget.setGraphicsEffect(None)
        if self._transition_widget is widget:
            self._transition_widget = None
            self._page_transition = None

    def _show_journal_reminder(self) -> None:
        if self.context.journal.completed_today():
            return
        reminder = QMessageBox(self)
        reminder.setWindowTitle("Your daily journal")
        reminder.setText("A small moment for today")
        reminder.setInformativeText("Add a few words, a poem, a story, or a drawing. There is no minimum.")
        open_button = reminder.addButton("Open journal", QMessageBox.AcceptRole)
        reminder.addButton("Later", QMessageBox.RejectRole)
        reminder.exec()
        if reminder.clickedButton() is open_button:
            row = next((row for row, name in self.nav_rows.items() if name == "Journal"), None)
            if row is not None:
                self.navigation.setCurrentRow(row)

    def refresh_destination_modules(self, counts: dict[str, int]) -> None:
        destinations = {
            "To-Do": "Tasks", "Reminder Candidate": "Tasks", "Shopping": "Shopping",
            "Projects / Learning": "Projects", "Projects": "Projects", "Archive / Notes": "Archive",
            "Inbox": "Brain Dump Scanner", "Follow-Up": "Follow-Up",
            "Bills & Renewals": "Bills & Renewals", "Errands & Appointments": "Errands & Appointments",
        }
        for category, module in destinations.items():
            if counts.get(category):
                self.refresh_module(module)

    def refresh_module(self, module: str) -> None:
        widget = self.widgets_by_module.get(module)
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()

    def apply_theme(self) -> None:
        # The workspace deliberately uses one calm visual language; the accent remains user-configurable.
        accent = self.context.settings.get("accent_color") or "#37352f"
        dark = self.context.settings.get("workspace_theme") == "Dark"
        stylesheet = NOTION_DARK if dark else NOTION_LIGHT
        self.setStyleSheet(stylesheet.replace("__ACCENT__", accent))
        self.theme_toggle.setText("Light mode" if dark else "Dark mode")

    def toggle_theme(self) -> None:
        current = self.context.settings.get("workspace_theme") or "Light"
        self.context.settings.set("workspace_theme", "Light" if current == "Dark" else "Dark")
        self.apply_theme()

    def refresh_appearance(self) -> None:
        self.apply_theme()

    def closeEvent(self, event) -> None:
        for widget in self.widgets_by_module.values():
            save = (getattr(widget, "flush_pending", None) or getattr(widget, "save_now", None)
                    or getattr(widget, "save_without_refresh", None))
            if callable(save): save()
        board = self.widgets_by_module.get("Dashboard")
        board_save = getattr(board, "_save_project", None)
        if callable(board_save):
            board_save()
        self.context.db.write_readable_snapshot()
        super().closeEvent(event)

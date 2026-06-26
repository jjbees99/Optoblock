from collections.abc import Callable
import json

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from personal_app.app import AppContext
from personal_app.gui.archive_page import ArchivePage
from personal_app.gui.dashboard_page import BrainDumpPage, DashboardPage
from personal_app.gui.finance_page import FinancePage
from personal_app.gui.projects_page import ProjectsPage
from personal_app.gui.recipes_page import RecipesPage
from personal_app.gui.settings_page import SettingsPage
from personal_app.gui.shopping_page import ShoppingPage
from personal_app.gui.styles import DARK, LIGHT
from personal_app.gui.tasks_page import TasksPage
from personal_app.gui.unwind_page import UnwindPage


MODULES = ["Dashboard", "Tasks", "Projects", "Finance", "Shopping", "Recipes", "Unwind", "Brain Dump", "Archive", "Settings"]


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.setWindowTitle("Optoblock")
        self.resize(1320, 860)
        self.module_checks: dict[str, QCheckBox] = {}
        self.active_modules = context.settings.startup_modules() or ["Dashboard", "Tasks", "Projects", "Finance"]
        self.root = QWidget()
        self.root.setObjectName("Root")
        self.setCentralWidget(self.root)
        self.outer = QVBoxLayout(self.root)
        self.outer.setContentsMargins(18, 14, 18, 18)
        self.outer.setSpacing(12)
        self._build_top_bar()
        self.table = QFrame()
        self.table.setObjectName("Table")
        self.table.setMinimumHeight(680)
        self.outer.addWidget(self.table, 1)
        self.widgets_by_module: dict[str, QWidget] = {}
        self.apply_theme()
        self.rebuild_table()

    def _build_top_bar(self) -> None:
        top = QHBoxLayout()
        top.addStretch(1)

        picker = QToolButton()
        picker.setText("Workspace")
        picker.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(picker)
        for module in MODULES:
            check = QCheckBox(module)
            check.setChecked(module in self.active_modules)
            check.stateChanged.connect(self._module_changed)
            action = QWidgetAction(menu)
            action.setDefaultWidget(check)
            menu.addAction(action)
            self.module_checks[module] = check
        picker.setMenu(menu)
        top.addWidget(picker)
        self.outer.addLayout(top)

    def _module_changed(self) -> None:
        self.active_modules = [name for name, check in self.module_checks.items() if check.isChecked()]
        if not self.active_modules:
            self.active_modules = ["Dashboard"]
            self.module_checks["Dashboard"].setChecked(True)
        self.save_layout()
        self.rebuild_table()

    def save_layout(self) -> None:
        self.context.settings.set_startup_modules(self.active_modules)

    def module_factory(self, name: str) -> Callable[[], QWidget]:
        return {
            "Dashboard": lambda: DashboardPage(self.context),
            "Tasks": lambda: TasksPage(self.context),
            "Projects": lambda: ProjectsPage(self.context),
            "Finance": lambda: FinancePage(self.context),
            "Shopping": lambda: ShoppingPage(self.context),
            "Recipes": lambda: RecipesPage(self.context),
            "Unwind": lambda: UnwindPage(self.context),
            "Brain Dump": lambda: BrainDumpPage(self.context),
            "Archive": lambda: ArchivePage(self.context),
            "Settings": lambda: SettingsPage(self.context, self.apply_theme),
        }[name]

    def rebuild_table(self) -> None:
        for widget in list(self.widgets_by_module.values()):
            widget.deleteLater()
        self.widgets_by_module.clear()
        geometries = self.load_geometries()
        for index, module in enumerate(self.active_modules):
            widget = self.module_factory(module)()
            widget.dropped.connect(self.swap_module_at_drop)
            widget.geometry_changed.connect(self.save_widget_geometry)
            widget.setParent(self.table)
            x, y, width, height = geometries.get(module, self.default_geometry(index))
            widget.setGeometry(x, y, width, height)
            widget.show()
            self.widgets_by_module[module] = widget

    def column_count(self) -> int:
        count = len(self.active_modules)
        if count <= 2:
            return count or 1
        if count <= 6:
            return 3
        return 4

    def swap_module_at_drop(self, source: str, global_pos) -> None:
        target = self.childAt(self.mapFromGlobal(global_pos))
        while target and not hasattr(target, "module_name"):
            target = target.parentWidget()
        if not target or target.module_name == source:
            return
        try:
            source_index = self.active_modules.index(source)
            target_index = self.active_modules.index(target.module_name)
        except ValueError:
            return
        self.active_modules[source_index], self.active_modules[target_index] = self.active_modules[target_index], self.active_modules[source_index]
        self.save_layout()

    def default_geometry(self, index: int) -> tuple[int, int, int, int]:
        width = 390
        height = 300
        gap = 16
        columns = max(1, min(3, max(1, self.table.width() // (width + gap))))
        return 18 + (index % columns) * (width + gap), 18 + (index // columns) * (height + gap), width, height

    def load_geometries(self) -> dict[str, tuple[int, int, int, int]]:
        raw = self.context.settings.get("workspace_geometries") or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return {name: tuple(values) for name, values in data.items() if isinstance(values, list) and len(values) == 4}

    def save_widget_geometry(self, module: str) -> None:
        widget = self.widgets_by_module.get(module)
        if not widget:
            return
        data = {name: list(values) for name, values in self.load_geometries().items()}
        data[module] = [widget.x(), widget.y(), widget.width(), widget.height()]
        self.context.settings.set("workspace_geometries", json.dumps(data))

    def apply_theme(self) -> None:
        theme = self.context.settings.get("theme") or "Dark"
        stylesheet = DARK if theme == "Dark" else LIGHT
        accent = self.context.settings.get("accent_color") or "#63d4c7"
        table = self.context.settings.get("table_color") or "#1f2a2e"
        stylesheet = stylesheet.replace("__ACCENT__", accent).replace("__TABLE__", table)
        self.setStyleSheet(stylesheet)

    def refresh_appearance(self) -> None:
        self.apply_theme()
        self.rebuild_table()

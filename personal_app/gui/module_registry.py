from collections.abc import Callable

from PySide6.QtWidgets import QWidget

from personal_app.app import AppContext
from personal_app.gui.archive_page import ArchivePage
from personal_app.gui.dashboard_page import BrainDumpPage, DashboardPage
from personal_app.gui.finance_page import FinancePage
from personal_app.gui.focus_timer_page import FocusTimerPage
from personal_app.gui.projects_page import ProjectsPage
from personal_app.gui.recipes_page import RecipesPage
from personal_app.gui.settings_page import SettingsPage
from personal_app.gui.shopping_page import ShoppingPage
from personal_app.gui.tasks_page import TasksPage
from personal_app.gui.unwind_page import UnwindPage
from personal_app.gui.voice_brain_dump_page import VoiceBrainDumpPage


MODULE_TITLES = {
    "Dashboard": "Dashboard",
    "Tasks": "To-Do List",
    "Projects": "Projects",
    "Finance": "Finance",
    "Focus Timer": "Focus Timer",
    "Shopping": "Shopping List",
    "Recipes": "Recipes",
    "Unwind": "Unwind List",
    "Brain Dump Scanner": "Brain Dump Scanner",
    "Voice Brain Dump": "Voice Brain Dump",
    "Archive": "Archive",
    "Settings": "Settings",
}

MODULE_OUTLINES = {
    "Dashboard": "#7dd3fc",
    "Tasks": "#f9a8d4",
    "Projects": "#facc15",
    "Finance": "#86efac",
    "Focus Timer": "#fb7185",
    "Shopping": "#fdba74",
    "Recipes": "#c4b5fd",
    "Unwind": "#93c5fd",
    "Brain Dump Scanner": "#f0abfc",
    "Voice Brain Dump": "#5eead4",
    "Archive": "#cbd5e1",
    "Settings": "#67e8f9",
}


def module_factory(context: AppContext, name: str, theme_changed=None) -> Callable[[], QWidget]:
    factories = {
        "Dashboard": lambda: DashboardPage(context),
        "Tasks": lambda: TasksPage(context),
        "Projects": lambda: ProjectsPage(context),
        "Finance": lambda: FinancePage(context),
        "Focus Timer": FocusTimerPage,
        "Shopping": lambda: ShoppingPage(context),
        "Recipes": lambda: RecipesPage(context),
        "Unwind": lambda: UnwindPage(context),
        "Brain Dump Scanner": lambda: BrainDumpPage(context),
        "Voice Brain Dump": lambda: VoiceBrainDumpPage(context),
        "Archive": lambda: ArchivePage(context),
        "Settings": lambda: SettingsPage(context, theme_changed),
    }
    return factories[name]

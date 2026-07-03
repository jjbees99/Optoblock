from dataclasses import dataclass

from personal_app.data.database import Database
from personal_app.logic.brain_dump_manager import BrainDumpManager
from personal_app.logic.finance_manager import FinanceManager
from personal_app.logic.life_admin_manager import LifeAdminManager
from personal_app.logic.journal_manager import JournalManager
from personal_app.logic.notes_manager import NotesManager
from personal_app.logic.project_manager import ProjectManager
from personal_app.logic.recipe_manager import RecipeManager
from personal_app.logic.settings_manager import SettingsManager
from personal_app.logic.shopping_manager import ShoppingManager
from personal_app.logic.storage_manager import StorageManager
from personal_app.logic.task_manager import TaskManager
from personal_app.logic.unwind_manager import UnwindManager


@dataclass
class AppContext:
    db: Database
    settings: SettingsManager
    tasks: TaskManager
    projects: ProjectManager
    shopping: ShoppingManager
    recipes: RecipeManager
    unwind: UnwindManager
    brain_dump: BrainDumpManager
    finance: FinanceManager
    storage: StorageManager
    life_admin: LifeAdminManager
    journal: JournalManager
    notes: NotesManager

    @classmethod
    def create(cls) -> "AppContext":
        db = Database()
        db.initialize()
        settings = SettingsManager(db)
        tasks = TaskManager(db)
        projects = ProjectManager(db)
        shopping = ShoppingManager(db)
        recipes = RecipeManager(shopping)
        unwind = UnwindManager(db)
        brain_dump = BrainDumpManager(db)
        finance = FinanceManager(db)
        storage = StorageManager(db)
        life_admin = LifeAdminManager(db)
        journal = JournalManager(db)
        notes = NotesManager(db)
        unwind.ensure_defaults()
        db.write_readable_snapshot()
        return cls(db, settings, tasks, projects, shopping, recipes, unwind, brain_dump, finance, storage, life_admin, journal, notes)

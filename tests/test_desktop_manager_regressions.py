import tempfile
import unittest
from pathlib import Path

from personal_app.data.database import Database
from personal_app.logic.brain_dump_manager import BrainDumpManager
from personal_app.logic.life_admin_manager import LifeAdminManager
from personal_app.logic.notes_manager import NotesManager
from personal_app.logic.project_manager import ProjectManager
from personal_app.logic.shopping_manager import ShoppingManager
from personal_app.logic.task_manager import TaskManager
from personal_app.logic.unwind_manager import UnwindManager


class DesktopManagerRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "desktop.sqlite3")
        self.db.initialize()

    def tearDown(self):
        self.db.checkpoint()
        self.tmp.cleanup()

    def test_projects_archive_delete_and_convert(self):
        projects, tasks = ProjectManager(self.db), TaskManager(self.db)
        project_id = projects.add("Project", next_action="Call supplier")
        projects.convert_next_action(project_id, tasks)
        self.assertEqual(tasks.list("Active")[0]["name"], "Call supplier")
        projects.archive(project_id)
        self.assertEqual(projects.list(include_archived=True)[0]["status"], "Archived")
        projects.delete(project_id)
        self.assertEqual(projects.list(include_archived=True), [])

    def test_shopping_archive_and_delete(self):
        shopping = ShoppingManager(self.db)
        bought_id = shopping.add("Milk")
        delete_id = shopping.add("Bread")
        shopping.set_bought(bought_id, True)
        shopping.archive_bought()
        self.assertTrue(self.db.one("SELECT archived FROM shopping_items WHERE id=?", (bought_id,))["archived"])
        shopping.delete(delete_id)
        self.assertIsNone(self.db.one("SELECT id FROM shopping_items WHERE id=?", (delete_id,)))

    def test_notes_brain_dump_life_admin_and_unwind(self):
        notes = NotesManager(self.db)
        notes.notes_dir = Path(self.tmp.name) / "notes"
        note_id = notes.create(); notes.save(note_id, "Edited", "Body")
        self.assertEqual(notes.get(note_id)["title"], "Edited")
        notes.delete(note_id); self.assertIsNone(notes.get(note_id))

        brain = BrainDumpManager(self.db)
        brain_id = brain.add("Thought"); brain.archive(brain_id)
        self.assertEqual(brain.archived()[0]["id"], brain_id)
        brain.restore(brain_id); self.assertEqual(brain.list()[0]["id"], brain_id)

        life = LifeAdminManager(self.db)
        bill_id = life.add("bills", title="Bill")
        life.update_field("bills", bill_id, "status", "Paid")
        life.archive("bills", bill_id); self.assertEqual(life.list("bills", archived=True)[0]["status"], "Paid")
        life.restore("bills", bill_id); self.assertEqual(life.list("bills")[0]["id"], bill_id)

        unwind = UnwindManager(self.db)
        unwind_id = unwind.add("Walk"); unwind.set_done(unwind_id, True)
        self.assertTrue(unwind.list()[0]["done_today"])
        unwind.reset_daily(); self.assertFalse(unwind.list()[0]["done_today"])
        unwind.delete(unwind_id); self.assertEqual(unwind.list(), [])

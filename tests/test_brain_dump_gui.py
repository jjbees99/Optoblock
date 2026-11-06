import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from personal_app.data.database import Database
from personal_app.gui.dashboard_page import BrainDumpPage
from personal_app.logic.brain_dump_manager import BrainDumpManager
from personal_app.logic.life_admin_manager import LifeAdminManager
from personal_app.logic.project_manager import ProjectManager
from personal_app.logic.settings_manager import SettingsManager
from personal_app.logic.shopping_manager import ShoppingManager


class Context:
    pass


class BrainDumpGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db = Database(Path(self.tmp.name) / "brain-dump.sqlite3")
        db.initialize()
        self.db = db
        context = Context()
        context.db = db
        context.settings = SettingsManager(db)
        context.brain_dump = BrainDumpManager(db)
        context.shopping = ShoppingManager(db)
        context.projects = ProjectManager(db)
        context.life_admin = LifeAdminManager(db)
        self.context = context
        self.page = BrainDumpPage(context)

    def tearDown(self):
        self.page.deleteLater()
        self.db.checkpoint()
        self.tmp.cleanup()

    def test_inbox_capture_and_refresh(self):
        self.page.destination.setCurrentText("Inbox")
        self.page.text.setPlainText("A genuine thought")
        self.page.save()
        self.assertEqual(self.context.brain_dump.list()[0]["body"], "A genuine thought")
        self.assertIn("A genuine thought", self.page.items.text())

    def test_auto_sort_and_voice_text_flow(self):
        self.page.destination.setCurrentText("Auto-sort")
        self.page.text.setPlainText("Research a garden project")
        self.page.save()
        self.assertEqual(self.context.projects.list()[0]["title"], "Research a garden project")
        self.page._voice_ready("Spoken thought")
        self.assertEqual(self.page.text.toPlainText(), "Spoken thought")
        self.assertTrue(self.page.voice.isEnabled())

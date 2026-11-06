import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QApplication

from personal_app.data.database import Database
from personal_app.gui.tasks_page import TasksPage
from personal_app.logic.settings_manager import SettingsManager
from personal_app.logic.task_manager import TaskManager


class Context:
    pass


class TaskArchiveGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "tasks.sqlite3")
        self.db.initialize()
        self.context = Context()
        self.context.db = self.db
        self.context.tasks = TaskManager(self.db)
        self.context.settings = SettingsManager(self.db)
        self.page = TasksPage(self.context)

    def tearDown(self):
        self.page.deleteLater()
        self.db.checkpoint()
        self.tmp.cleanup()

    def _select_rows(self, rows):
        self.page.table.clearSelection()
        for row in rows:
            self.page.table.selectionModel().select(
                self.page.table.model().index(row, 0),
                QItemSelectionModel.Select | QItemSelectionModel.Rows,
            )

    def test_archive_one_preserves_id_and_restore(self):
        task_id = self.context.tasks.add("Task A")
        self.page.refresh()
        self._select_rows([0])
        self.page.archive_selected()
        self.assertEqual(self.context.tasks.list("Active"), [])
        archived = self.context.tasks.list("Archived")
        self.assertEqual(archived[0]["id"], task_id)
        self.context.tasks.restore(task_id)
        self.assertEqual(self.context.tasks.list("Active")[0]["id"], task_id)

    def test_archive_multiple_selected_gui_rows(self):
        ids = [self.context.tasks.add(name) for name in ("A", "B", "C")]
        self.page.refresh()
        row_by_id = {self.page.table.item(row, 0).data(256): row for row in range(self.page.table.rowCount())}
        self._select_rows([row_by_id[ids[0]], row_by_id[ids[2]]])
        self.page.archive_selected()
        self.assertEqual({row["id"] for row in self.context.tasks.list("Active")}, {ids[1]})
        self.assertEqual({row["id"] for row in self.context.tasks.list("Archived")}, {ids[0], ids[2]})

    def test_archive_completed_and_filter(self):
        active_id = self.context.tasks.add("Active")
        done_id = self.context.tasks.add("Done")
        self.context.tasks.complete(done_id, True)
        self.page.refresh()
        self.page.filter.setCurrentText("Completed")
        self.assertEqual(self.page.table.rowCount(), 1)
        self.assertEqual(self.page.table.item(0, 0).data(256), done_id)
        self.page.archive_completed()
        self.assertEqual(self.context.tasks.list("Archived")[0]["id"], done_id)
        self.assertEqual(self.context.tasks.list("Active")[0]["id"], active_id)

    def test_remote_add_does_not_clear_selection_then_desktop_archive(self):
        ids = [self.context.tasks.add(name) for name in ("A", "B", "C")]
        self.page.refresh()
        row_b = next(row for row in range(self.page.table.rowCount()) if self.page.table.item(row, 0).data(256) == ids[1])
        self._select_rows([row_b])
        phone_id = self.context.tasks.add("PHONE TEST TASK")
        self.page.request_remote_refresh()
        self.assertTrue(self.page.table.selectionModel().hasSelection())
        self.page.table.item(next(row for row in range(self.page.table.rowCount()) if self.page.table.item(row, 0).data(256) == ids[0]), 1).setText("A edited")
        self.page.archive_selected()
        rows = {row["id"]: row for row in self.context.tasks.list("All")}
        self.assertEqual(rows[ids[0]]["name"], "A edited")
        self.assertEqual(rows[ids[1]]["status"], "Archived")
        self.assertEqual(rows[ids[2]]["status"], "Active")
        self.assertEqual(rows[phone_id]["status"], "Active")

    def test_add_edit_complete_incomplete_and_delete_through_gui(self):
        self.page.add_row()
        row = self.page.table.rowCount() - 1
        self.page.table.item(row, 1).setText("Desktop GUI task")
        self.page.table.item(row, 2).setText("Edited description")
        self.page.table.cellWidget(row, 5).setCurrentText("High")
        self.page.table.item(row, 0).setCheckState(Qt.Checked)
        self.page.save()
        task_id = self.page.table.item(row, 0).data(256)
        saved = self.db.one("SELECT * FROM tasks WHERE id=?", (task_id,))
        self.assertEqual((saved["name"], saved["description"], saved["priority"], saved["status"]),
                         ("Desktop GUI task", "Edited description", "High", "Completed"))
        self.page.table.item(row, 0).setCheckState(Qt.Unchecked)
        self.page.table.cellWidget(row, 6).setCurrentText("Active")
        self.page.save()
        self.assertEqual(self.db.one("SELECT status FROM tasks WHERE id=?", (task_id,))["status"], "Active")
        self._select_rows([row])
        self.page.table.setCurrentCell(row, 0)
        self.page.delete_row()
        self.assertIsNone(self.db.one("SELECT id FROM tasks WHERE id=?", (task_id,)))

import tempfile
import unittest
from pathlib import Path

from personal_app.data.database import Database
from personal_app.logic.day_planner_manager import DayPlannerManager
from personal_app.logic.day_planner_manager import PLANNER_COLOURS


class DayPlannerManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Database(Path(self.temp.name) / "test.sqlite3")
        self.db.initialize()
        self.manager = DayPlannerManager(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_blocks_are_kept_per_date_and_ordered(self):
        self.manager.add("2026-08-13", "Lunch", 720, 60)
        early = self.manager.add("2026-08-13", "Deep work", 540, 90)
        self.manager.add("2026-08-14", "Tomorrow", 600)
        rows = self.manager.list("2026-08-13")
        self.assertEqual([row["title"] for row in rows], ["Deep work", "Lunch"])
        self.manager.update(early, title="Thesis", start_minute=600, duration_minutes=120, notes="Chapter 2")
        self.assertEqual(self.manager.list("2026-08-13")[0]["notes"], "Chapter 2")

    def test_duplicate_and_delete(self):
        block_id = self.manager.add("2026-08-13", "Gym", 1080, 60)
        self.manager.duplicate(block_id)
        self.assertEqual(len(self.manager.list("2026-08-13")), 2)
        self.manager.delete(block_id)
        self.assertEqual(len(self.manager.list("2026-08-13")), 1)

    def test_new_and_duplicated_blocks_receive_different_colours(self):
        first = self.manager.add("2026-08-13", "Thesis", 540)
        self.manager.add("2026-08-13", "Lunch", 720)
        self.manager.duplicate(first)
        colours = [row["colour"] for row in self.manager.list("2026-08-13")]
        self.assertEqual(len(set(colours)), 3)
        self.assertTrue(set(colours).issubset(PLANNER_COLOURS))

    def test_legacy_single_colour_schedule_is_migrated(self):
        for title, minute in (("One", 540), ("Two", 600), ("Three", 660)):
            self.db.execute(
                "INSERT INTO planner_blocks(plan_date,title,start_minute,colour) VALUES(?,?,?,?)",
                ("2026-08-15", title, minute, "#7dd3fc"),
            )
        self.manager.ensure_varied_colours()
        colours = [row["colour"] for row in self.manager.list("2026-08-15")]
        self.assertEqual(len(set(colours)), 3)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from personal_app.data.models import DashboardModule
from personal_app.logic.dashboard_layout import DashboardLayout
from personal_app.logic.dashboard_storage import DashboardStorage


class DashboardLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = DashboardModule("tasks", "To-Do List", "Tasks", 0, 0)
        self.layout = DashboardLayout([self.module])

    def test_rejects_overlap(self) -> None:
        other = DashboardModule("projects", "Projects", "Projects", 1, 0)
        self.layout.modules.append(other)

        self.assertFalse(self.layout.place("tasks", 1, 0, 1, 1))
        self.assertEqual((self.module.x, self.module.y), (0, 0))

    def test_rejects_out_of_bounds_resize(self) -> None:
        self.assertFalse(self.layout.place("tasks", 2, 2, 2, 2))

    def test_allows_structured_resize(self) -> None:
        self.assertTrue(self.layout.place("tasks", 0, 0, 2, 2))
        self.assertEqual((self.module.width, self.module.height), (2, 2))

    def test_finds_first_available_slot(self) -> None:
        self.assertEqual(self.layout.first_available(), (1, 0))

    def test_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = DashboardStorage(Path(directory) / "layout.json")
            storage.save(self.layout.modules)
            loaded = storage.load()

        self.assertEqual(loaded, self.layout.modules)

    def test_profile_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = DashboardStorage(Path(directory) / "layout.json")
            profiles = {
                "Focus Work": self.layout.modules,
                "Unwinding": [DashboardModule("unwind", "Unwind", "Unwind", 0, 0, 2, 2)],
            }
            storage.save_profiles("Unwinding", profiles)
            active, loaded = storage.load_profiles()

        self.assertEqual(active, "Unwinding")
        self.assertEqual(loaded, profiles)

    def test_legacy_layout_migrates_to_focus_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = DashboardStorage(Path(directory) / "layout.json")
            storage.save(self.layout.modules)
            active, loaded = storage.load_profiles()

        self.assertEqual(active, "Focus Work")
        self.assertEqual(loaded["Focus Work"], self.layout.modules)


if __name__ == "__main__":
    unittest.main()

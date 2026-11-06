import unittest

from personal_app.gui.day_planner_page import PIXELS_PER_HOUR, Timeline


class TimelineSelectionTests(unittest.TestCase):
    def test_drag_draws_requested_duration(self):
        start, duration = Timeline.selection(9 * PIXELS_PER_HOUR, 10.5 * PIXELS_PER_HOUR)
        self.assertEqual((start, duration), (540, 90))

    def test_upward_drag_uses_earlier_time(self):
        start, duration = Timeline.selection(12 * PIXELS_PER_HOUR, 10 * PIXELS_PER_HOUR)
        self.assertEqual((start, duration), (600, 120))

    def test_click_creates_minimum_half_hour(self):
        start, duration = Timeline.selection(8 * PIXELS_PER_HOUR, 8 * PIXELS_PER_HOUR)
        self.assertEqual((start, duration), (480, 30))


if __name__ == "__main__":
    unittest.main()

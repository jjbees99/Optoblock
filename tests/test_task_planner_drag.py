import unittest

from personal_app.gui.drag_payloads import decode_task, encode_task


class TaskPlannerDragTests(unittest.TestCase):
    def test_task_title_round_trip_preserves_unicode(self):
        self.assertEqual(decode_task(encode_task("  Read résumé notes  ")), "Read résumé notes")


if __name__ == "__main__":
    unittest.main()

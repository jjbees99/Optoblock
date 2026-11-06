import unittest

from personal_app.gui.main_window import MainWindow


class JournalStartupTests(unittest.TestCase):
    def test_journal_reminder_popup_is_not_installed(self):
        self.assertFalse(hasattr(MainWindow, "_show_journal_reminder"))

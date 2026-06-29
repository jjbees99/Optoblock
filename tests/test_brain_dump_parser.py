import tempfile
import unittest
from pathlib import Path

from personal_app.logic.brain_dump_parser import BrainDumpParser
from personal_app.logic.voice_brain_dump_manager import TranscriptStorage


class BrainDumpParserTests(unittest.TestCase):
    def test_example_is_split_and_classified(self) -> None:
        transcript = "Tomorrow I need to email Nicolas, check the DAQ channels, buy pasta, and look into ROS alternatives."

        items = BrainDumpParser().parse(transcript)
        values = {(item.category, item.text) for item in items}

        self.assertIn(("Reminder Candidate", "Tomorrow"), values)
        self.assertIn(("To-Do", "Email Nicolas"), values)
        self.assertIn(("To-Do", "Check the DAQ channels"), values)
        self.assertIn(("Shopping", "Pasta"), values)
        self.assertIn(("Projects / Learning", "Look into ROS alternatives"), values)

    def test_unclear_text_becomes_archive_note(self) -> None:
        item = BrainDumpParser().parse("An idea without a clear action")[0]
        self.assertEqual(item.category, "Archive / Notes")

    def test_conversational_actions_are_split_and_normalized(self) -> None:
        transcript = "Hey so I'm thinking about buying some milk and I have to email Sarah"

        items = BrainDumpParser().parse(transcript)

        self.assertEqual(
            [(item.category, item.text) for item in items],
            [("Shopping", "Milk"), ("To-Do", "Email Sarah")],
        )

    def test_and_inside_one_shopping_item_is_not_split(self) -> None:
        items = BrainDumpParser().parse("I need to buy milk and bread")

        self.assertEqual(
            [(item.category, item.text) for item in items],
            [("Shopping", "Milk"), ("Shopping", "Bread")],
        )

    def test_comma_separated_shopping_list_becomes_individual_nouns(self) -> None:
        items = BrainDumpParser().parse("I need to buy milk, eggs and bread")

        self.assertEqual(
            [(item.category, item.text) for item in items],
            [("Shopping", "Milk"), ("Shopping", "Eggs"), ("Shopping", "Bread")],
        )

    def test_reported_speech_before_action_is_removed(self) -> None:
        items = BrainDumpParser().parse("I said I think I want to email Sarah")

        self.assertEqual([(item.category, item.text) for item in items], [("To-Do", "Email Sarah")])

    def test_transcript_is_saved_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = TranscriptStorage(Path(directory)).save("A transcript")
            contents = path.read_text(encoding="utf-8")
        self.assertIn('"transcript": "A transcript"', contents)


if __name__ == "__main__":
    unittest.main()

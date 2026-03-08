import unittest
from datetime import date
from importlib import import_module
from unittest.mock import patch

from nuvola.cli.main import choose_student, prompt_homework_range, prompt_topic_range
from nuvola.domain.models import Student


class CliHelpersTest(unittest.TestCase):
    def setUp(self):
        self.students = [
            Student("1", "ALUNNO", "UNO", "3A", "2025"),
            Student("2", "ALUNNO", "DUE", "5B", "2025"),
        ]
        self.cli_module = import_module("nuvola.cli.main")

    def test_choose_student_uses_preferred_student_without_prompt(self):
        student = choose_student(self.students, preferred_student_id="2")
        self.assertEqual(student.id, "2")

    def test_topic_range_uses_last_week_defaults(self):
        answers = iter(["", ""])
        with patch.object(self.cli_module, "default_lesson_topics_range", return_value=(date(2026, 3, 2), date(2026, 3, 8))):
            start_date, end_date = prompt_topic_range(input_fn=lambda _: next(answers), output=lambda _: None)
        self.assertEqual(start_date, date(2026, 3, 2))
        self.assertEqual(end_date, date(2026, 3, 8))

    def test_homework_range_defaults_to_today_plus_14_days(self):
        answers = iter(["", ""])
        with patch.object(
            self.cli_module,
            "default_homework_range",
            return_value=(date(2026, 3, 8), date(2026, 3, 22)),
        ):
            start_date, end_date = prompt_homework_range(
                self.students[0],
                input_fn=lambda _: next(answers),
                output=lambda _: None,
            )
        self.assertEqual(start_date, date(2026, 3, 8))
        self.assertEqual(end_date, date(2026, 3, 22))


if __name__ == "__main__":
    unittest.main()

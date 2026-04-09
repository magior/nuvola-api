import unittest
from datetime import date

from nuvola.application.dates import (
    default_homework_range,
    default_lesson_topics_range,
    last_week_range,
    parse_user_date,
    school_year_end_date,
)
from nuvola.domain.models import Student


class DatesTest(unittest.TestCase):
    def test_parse_user_date_accepts_supported_formats(self):
        self.assertEqual(parse_user_date("08-03-2026"), date(2026, 3, 8))
        self.assertEqual(parse_user_date("2026-03-08"), date(2026, 3, 8))

    def test_last_week_range_is_inclusive(self):
        start_date, end_date = last_week_range(today=date(2026, 3, 8))
        self.assertEqual(start_date, date(2026, 3, 2))
        self.assertEqual(end_date, date(2026, 3, 8))

    def test_school_year_end_date(self):
        self.assertEqual(school_year_end_date("2025"), date(2026, 8, 31))

    def test_default_homework_range_uses_today_and_plus_14_days(self):
        student = Student("STUDENTE-DEMO-A", "ALUNNO", "UNO", "3A", "2025")
        self.assertEqual(
            default_homework_range(student, today=date(2026, 3, 8)),
            (date(2026, 3, 8), date(2026, 3, 22)),
        )

    def test_default_lesson_topics_range_is_last_7_days(self):
        self.assertEqual(
            default_lesson_topics_range(today=date(2026, 3, 8)),
            (date(2026, 3, 2), date(2026, 3, 8)),
        )


if __name__ == "__main__":
    unittest.main()

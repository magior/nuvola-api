import json
import unittest
from pathlib import Path

from nuvola.adapters.legacy_student_api.adapter import LegacyStudentApiAdapter
from nuvola.application.reports import render_homework, render_lesson_topics, render_subject_grades

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"


class ReportsTest(unittest.TestCase):
    def test_render_subject_grades_shows_objective_details(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "subject_grades_detail.json").read_text(encoding="utf-8"))
        subject = adapter._map_subjects(payload)[0]

        report = render_subject_grades([subject])

        self.assertIn("31-01-2026 | * | ORALE | docente: DOCENTE REDATTO", report)
        self.assertIn("descrizione: Monomi", report)
        self.assertIn("* Conoscenze: 8", report)

    def test_render_homework_shows_dates_and_teacher(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "homework_day.json").read_text(encoding="utf-8"))
        homework = adapter._map_homework(payload)

        report = render_homework(homework)

        self.assertIn("dataConsegna: 22-01-2026", report)
        self.assertIn("dataAssegnazione: 16-01-2026", report)
        self.assertIn("docente: DOCENTE REDATTO", report)
        self.assertIn("nomeArgomento: Divisioni", report)

    def test_render_lesson_topics_shows_order_and_cosignatures(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "lesson_topics_range.json").read_text(encoding="utf-8"))
        topics = adapter._map_lesson_topics(payload)

        report = render_lesson_topics(topics)

        self.assertIn("cofirme: DOCENTE SUPPORTO (SOSTEGNO, firmato)", report)
        self.assertLess(report.find("1a ora 08:30-09:30"), report.find("2a ora 09:30-10:30"))


if __name__ == "__main__":
    unittest.main()

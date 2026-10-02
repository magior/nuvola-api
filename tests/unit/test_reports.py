import json
import unittest
from pathlib import Path

from nuvola.adapters.legacy_student_api.adapter import LegacyStudentApiAdapter
from nuvola.application.reports import (
    render_homework,
    render_lesson_topics,
    render_noticeboard_document,
    render_noticeboard_documents,
    render_subject_grades,
)

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"
STUDENT_FIXTURES = FIXTURES / "student_readonly"


class ReportsTest(unittest.TestCase):
    def test_render_subject_grades_shows_objective_details(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "subject_grades_detail.json").read_text(encoding="utf-8"))
        subject = adapter._map_subjects(payload)[0]

        report = render_subject_grades([subject])

        self.assertIn("31-01-2026 | * | ORALE | docente: DOCENTE TEST 4", report)
        self.assertIn("descrizione: Monomi", report)
        self.assertIn("* Conoscenze: 8", report)

    def test_render_homework_shows_dates_and_teacher(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "homework_day.json").read_text(encoding="utf-8"))
        homework = adapter._map_homework(payload)

        report = render_homework(homework)

        self.assertIn("dataConsegna: 22-01-2026", report)
        self.assertIn("dataAssegnazione: 16-01-2026", report)
        self.assertIn("docente: DOCENTE TEST 1", report)
        self.assertIn("nomeArgomento: Ripasso unita", report)

    def test_render_lesson_topics_shows_order_and_cosignatures(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((FIXTURES / "lesson_topics_range.json").read_text(encoding="utf-8"))
        topics = adapter._map_lesson_topics(payload)

        report = render_lesson_topics(topics)

        self.assertIn("cofirme: DOCENTE TEST SUPPORTO (SOSTEGNO, firmato)", report)
        self.assertLess(report.find("1a ora 08:30-09:30"), report.find("2a ora 09:30-10:30"))

    def test_render_noticeboard_documents_marks_unread(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((STUDENT_FIXTURES / "noticeboard_documents.json").read_text(encoding="utf-8"))
        documents = adapter._map_noticeboard_documents(payload, "12")

        report = render_noticeboard_documents(documents)

        self.assertIn("  1  20-01-2026 | Circolare di prova A", report)
        self.assertIn("  3* 10-01-2026 | Circolare di prova C", report)
        self.assertIn("(* = non letto)", report)
        self.assertNotIn("Documenti 1-", report)

    def test_render_noticeboard_documents_numbers_pages_from_offset(self):
        adapter = LegacyStudentApiAdapter()
        payload = {"count": 40, "data": [{"id": 1, "oggetto": "A"}, {"id": 2, "oggetto": "B"}]}
        documents = adapter._map_noticeboard_documents(payload, "12")

        report = render_noticeboard_documents(documents, start=26)

        self.assertIn("Documenti 26-27 di 40.", report)
        self.assertIn(" 26  - | A", report)
        self.assertIn(" 27  - | B", report)

    def test_render_noticeboard_document_lists_attachments(self):
        adapter = LegacyStudentApiAdapter()
        payload = json.loads((STUDENT_FIXTURES / "noticeboard_document_detail.json").read_text(encoding="utf-8"))
        document = adapter._map_noticeboard_document(payload, "12")

        report = render_noticeboard_document(document)

        self.assertIn("protocollo: 0000103 del 10-01-2026", report)
        self.assertIn("ufficio: UFFICIO DEMO", report)
        self.assertIn("1: circolare-demo.pdf", report)
        self.assertNotIn("responsabile:", report)


if __name__ == "__main__":
    unittest.main()

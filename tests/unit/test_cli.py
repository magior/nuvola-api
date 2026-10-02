import tempfile
import unittest
from datetime import date
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

from nuvola.cli.main import choose_student, prompt_homework_range, prompt_topic_range, run_noticeboards, save_attachment
from nuvola.domain.models import (
    NoticeboardAttachment,
    NoticeboardDocument,
    NoticeboardItem,
    NotificationCounts,
    Student,
)


def _document(document_id, attachments=(), total=None):
    return NoticeboardDocument(
        id=document_id,
        board_id="12",
        subject=f"Documento {document_id}",
        category=None,
        registry_number=None,
        registry_date=None,
        published_at=None,
        archived_at=None,
        is_read=False,
        requires_adhesion=False,
        adhesion_deadline=None,
        attachments=list(attachments),
        raw={"_collection_count": total} if total is not None else {},
    )


class _NoticeboardService:
    def __init__(self):
        self.calls = []
        self.attachment = NoticeboardAttachment(id="uuid-1", name="circolare.pdf", mime_type="application/pdf")

    def get_notification_counts(self, session, student_id):
        return NotificationCounts(events=0, noticeboards=2)

    def list_noticeboards(self, session, student_id):
        return [NoticeboardItem(id="12", name="COMUNICAZIONI", item_count=None)]

    def list_noticeboard_documents(self, session, student_id, board_id, include_archived=False, limit=25, offset=0):
        self.calls.append(("list", board_id, include_archived, offset))
        if offset == 0:
            return [_document("9001", total=3), _document("9002", total=3)]
        return [_document("9003", total=3)]

    def get_noticeboard_document(self, session, student_id, board_id, document_id):
        self.calls.append(("detail", board_id, document_id))
        return _document(document_id, attachments=[self.attachment])

    def download_attachment(self, session, student_id, attachment_id):
        self.calls.append(("download", attachment_id))
        return b"%PDF"


class CliHelpersTest(unittest.TestCase):
    def setUp(self):
        self.students = [
            Student("STUDENTE-DEMO-A", "ALUNNO", "UNO", "3A", "2025"),
            Student("STUDENTE-DEMO-B", "ALUNNO", "DUE", "5B", "2025"),
        ]
        self.cli_module = import_module("nuvola.cli.main")

    def test_choose_student_uses_preferred_student_without_prompt(self):
        student = choose_student(self.students, preferred_student_id="STUDENTE-DEMO-B")
        self.assertEqual(student.id, "STUDENTE-DEMO-B")

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


class NoticeboardCliTest(unittest.TestCase):
    def setUp(self):
        self.student = Student("STUDENTE-DEMO-A", "ALUNNO", "UNO", "3A", "2025")

    def test_run_noticeboards_browses_document_and_downloads_attachment(self):
        service = _NoticeboardService()
        answers = iter(["a", "n", "3", "1", "", "p", ""])
        outputs = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_noticeboards(
                service,
                session=None,
                active_student=self.student,
                download_dir=Path(tmp_dir),
                input_fn=lambda _: next(answers),
                output=outputs.append,
            )
            self.assertEqual((Path(tmp_dir) / "circolare.pdf").read_bytes(), b"%PDF")

        self.assertEqual(
            service.calls,
            [
                ("list", "12", False, 0),
                ("list", "12", True, 0),
                ("list", "12", True, 2),
                ("detail", "12", "9003"),
                ("download", "uuid-1"),
                ("list", "12", True, 2),
                ("list", "12", True, 0),
            ],
        )
        self.assertTrue(any("non letti in bacheca: 2" in line for line in outputs))

    def test_save_attachment_strips_paths_and_avoids_overwrite(self):
        attachment = NoticeboardAttachment(id="uuid-1", name="../../evil.pdf", mime_type=None)
        with tempfile.TemporaryDirectory() as tmp_dir:
            directory = Path(tmp_dir)
            first = save_attachment(b"1", attachment, directory)
            second = save_attachment(b"2", attachment, directory)

            self.assertEqual(first, directory / "evil.pdf")
            self.assertEqual(second, directory / "evil (1).pdf")
            self.assertEqual(second.read_bytes(), b"2")

    def test_save_attachment_falls_back_to_id_without_name(self):
        attachment = NoticeboardAttachment(id="uuid-1", name="..", mime_type=None)
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = save_attachment(b"x", attachment, Path(tmp_dir))

        self.assertEqual(target.name, "uuid-1.bin")


if __name__ == "__main__":
    unittest.main()

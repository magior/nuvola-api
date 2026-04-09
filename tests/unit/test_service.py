import tempfile
import unittest
from pathlib import Path

from nuvola.adapters.storage.file_session_store import FileSessionStore
from nuvola.application.service import NuvolaService
from nuvola.domain.models import SessionContext, Student


class FakeBackend:
    backend_name = "legacy_student"

    def authenticate(self, username, password, tenant=None):
        return SessionContext(backend=self.backend_name, token="TOKEN", tenant=tenant)

    def list_students(self, session):
        return [
            Student("STUDENTE-DEMO-A", "ALUNNO", "UNO", "3A", "2025"),
            Student("STUDENTE-DEMO-B", "ALUNNO", "DUE", "5B", "2025"),
        ]

    def list_grade_periods(self, session, student_id):
        return []

    def list_subject_grades(self, session, student_id, period_id):
        return []

    def list_homework(self, session, student_id, start_date, end_date):
        return []

    def list_lesson_topics(self, session, student_id, start_date, end_date):
        return []


class ServiceTest(unittest.TestCase):
    def test_login_persists_token_before_student_choice(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileSessionStore(Path(tmp_dir) / ".nuvola-session.json")
            service = NuvolaService({"legacy_student": FakeBackend()}, store)
            session = service.login("user", "pass")

            loaded = store.load()
            self.assertEqual(session.token, "TOKEN")
            self.assertEqual(loaded.token, "TOKEN")
            self.assertIsNone(loaded.student_id)

    def test_select_student_updates_session(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileSessionStore(Path(tmp_dir) / ".nuvola-session.json")
            service = NuvolaService({"legacy_student": FakeBackend()}, store)
            session = SessionContext(backend="legacy_student", token="TOKEN")

            updated = service.select_student(session, "STUDENTE-DEMO-B")

            self.assertEqual(updated.student_id, "STUDENTE-DEMO-B")
            self.assertEqual(store.load().student_id, "STUDENTE-DEMO-B")


if __name__ == "__main__":
    unittest.main()

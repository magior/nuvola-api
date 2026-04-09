import tempfile
import unittest
from pathlib import Path

from nuvola.adapters.tenant_api.adapter import TenantApiAdapter
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

    def list_latest_grades(self, session, student_id, limit=10):
        return ["latest_grades", student_id, limit]

    def list_subject_grades(self, session, student_id, period_id):
        return []

    def list_homework(self, session, student_id, start_date, end_date):
        return []

    def list_lesson_topics(self, session, student_id, start_date, end_date):
        return []

    def get_student_menu_options(self, session, student_id):
        return {"compito_accesso_lista": True}

    def list_absences(self, session, student_id, limit=10):
        return ["absences", student_id, limit]

    def list_notes(self, session, student_id, limit=10):
        return ["notes", student_id, limit]

    def list_class_events(self, session, student_id, page=1, limit=25, ordering="data_inizio_desc", only_planner_visible=None):
        return ["class_events", student_id, page, limit, ordering, only_planner_visible]

    def list_subject_events(self, session, student_id, page=1, limit=25, ordering="data_inizio_desc"):
        return ["subject_events", student_id, page, limit, ordering]

    def list_student_events(self, session, student_id, page=1, limit=25, ordering="data_inizio_desc"):
        return ["student_events", student_id, page, limit, ordering]

    def list_payments(self, session, student_id, status="daPagare", page=1, limit=10):
        return ["payments", student_id, status, page, limit]

    def list_noticeboards(self, session, student_id, limit=1000):
        return ["noticeboards", student_id, limit]

    def list_questionnaires(self, session, student_id):
        return ["questionnaires", student_id]

    def list_fillable_forms(self, session, student_id):
        return ["fillable_forms", student_id]

    def list_booked_meetings(self, session, student_id):
        return ["booked_meetings", student_id]

    def list_teacher_materials(self, session, student_id):
        return ["teacher_materials", student_id]


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

    def test_public_read_only_methods_passthrough_to_backend(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileSessionStore(Path(tmp_dir) / ".nuvola-session.json")
            service = NuvolaService({"legacy_student": FakeBackend()}, store)
            session = SessionContext(backend="legacy_student", token="TOKEN")

            self.assertEqual(service.get_student_menu_options(session, "1"), {"compito_accesso_lista": True})
            self.assertEqual(service.list_latest_grades(session, "1", limit=4), ["latest_grades", "1", 4])
            self.assertEqual(service.list_absences(session, "1", limit=5), ["absences", "1", 5])
            self.assertEqual(service.list_notes(session, "1", limit=3), ["notes", "1", 3])
            self.assertEqual(
                service.list_class_events(session, "1", page=2, limit=7, ordering="x", only_planner_visible=True),
                ["class_events", "1", 2, 7, "x", True],
            )
            self.assertEqual(
                service.list_subject_events(session, "1", page=3, limit=8, ordering="y"),
                ["subject_events", "1", 3, 8, "y"],
            )
            self.assertEqual(
                service.list_student_events(session, "1", page=4, limit=9, ordering="z"),
                ["student_events", "1", 4, 9, "z"],
            )
            self.assertEqual(service.list_payments(session, "1", status="pagato", page=5, limit=6), ["payments", "1", "pagato", 5, 6])
            self.assertEqual(service.list_noticeboards(session, "1", limit=11), ["noticeboards", "1", 11])
            self.assertEqual(service.list_questionnaires(session, "1"), ["questionnaires", "1"])
            self.assertEqual(service.list_fillable_forms(session, "1"), ["fillable_forms", "1"])
            self.assertEqual(service.list_booked_meetings(session, "1"), ["booked_meetings", "1"])
            self.assertEqual(service.list_teacher_materials(session, "1"), ["teacher_materials", "1"])

    def test_tenant_adapter_exposes_read_only_surface_with_not_implemented(self):
        adapter = TenantApiAdapter()
        session = SessionContext(backend="tenant", token="TOKEN", tenant="demo")

        with self.assertRaises(NotImplementedError):
            adapter.list_latest_grades(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.get_student_menu_options(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_absences(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_notes(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_class_events(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_subject_events(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_student_events(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_payments(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_noticeboards(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_questionnaires(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_fillable_forms(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_booked_meetings(session, "1")
        with self.assertRaises(NotImplementedError):
            adapter.list_teacher_materials(session, "1")


if __name__ == "__main__":
    unittest.main()

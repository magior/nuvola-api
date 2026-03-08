import json
import unittest
from pathlib import Path

from nuvola.adapters.legacy_student_api.adapter import LegacyStudentApiAdapter
from nuvola.domain.models import SessionContext

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"


class _FakeCookies:
    def __init__(self, token=None):
        self._token = token

    def get(self, name):
        if name == "nuvola":
            return self._token
        return None


class _FakeResponse:
    def __init__(self, text="", json_payload=None, cookie=None, history=None):
        self.text = text
        self._json_payload = json_payload
        self.cookies = _FakeCookies(cookie)
        self.history = history or []

    def raise_for_status(self):
        return None

    def json(self):
        return self._json_payload


class _FakeSession:
    def __init__(self):
        self.cookies = _FakeCookies("SESSION_COOKIE")
        self.calls = []

    def get(self, url, headers=None, cookies=None, params=None):
        self.calls.append(("GET", url, headers, cookies, params))
        if url == "https://nuvola.test":
            return _FakeResponse(
                text=(
                    "<html><form>"
                    "<input type='hidden' name='_csrf_token' value='csrf-token'>"
                    "</form></html>"
                )
            )
        if url.endswith("/api-studente/v1/login-from-web"):
            return _FakeResponse(json_payload={"token": "BEARER_TOKEN"})
        if url.endswith("/api-studente/v1/alunno/1000/compito/elenco/09-03-2026/15-03-2026"):
            payload = json.loads((FIXTURES / "homework_range.json").read_text(encoding="utf-8"))
            return _FakeResponse(json_payload=payload)
        raise AssertionError(f"URL non gestito: {url}")

    def post(self, url, data=None):
        self.calls.append(("POST", url, data))
        return _FakeResponse(cookie=None)


class LegacyStudentApiAdapterTest(unittest.TestCase):
    def setUp(self):
        self.adapter = LegacyStudentApiAdapter()

    def test_authenticate_runs_web_login_then_login_from_web(self):
        session = _FakeSession()
        adapter = LegacyStudentApiAdapter(session=session, base_url="https://nuvola.test")

        context = adapter.authenticate("user", "pass")

        self.assertEqual(context.backend, "legacy_student")
        self.assertEqual(context.token, "BEARER_TOKEN")
        self.assertEqual(
            session.calls,
            [
                ("GET", "https://nuvola.test", None, None, None),
                (
                    "POST",
                    "https://nuvola.test/login_check",
                    {
                        "_username": "user",
                        "_password": "pass",
                        "_csrf_token": "csrf-token",
                    },
                ),
                ("GET", "https://nuvola.test/api-studente/v1/login-from-web", None, {"nuvola": "SESSION_COOKIE"}, None),
            ],
        )

    def test_map_homework_collects_extra_dates(self):
        payload = json.loads((FIXTURES / "homework_day.json").read_text(encoding="utf-8"))

        items = self.adapter._map_homework(payload)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Completare la scheda di ripasso A")
        self.assertEqual(items[0].extra_dates["dataPromemoria"], "2026-01-20T00:00:00+01:00")

    def test_list_homework_uses_range_endpoint_with_context(self):
        from datetime import date

        session = _FakeSession()
        adapter = LegacyStudentApiAdapter(session=session, base_url="https://nuvola.test")

        items = adapter.list_homework(
            SessionContext(backend="legacy_student", token="BEARER_TOKEN"),
            "1000",
            date(2026, 3, 9),
            date(2026, 3, 15),
        )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].subject, "ITALIANO")
        self.assertEqual(items[1].subject, "SCIENZE")
        self.assertEqual(
            session.calls,
            [
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/1000/compito/elenco/09-03-2026/15-03-2026",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "1000"},
                )
            ],
        )

    def test_map_lesson_topics_keeps_cosignatures_and_ordering(self):
        payload = json.loads((FIXTURES / "lesson_topics_range.json").read_text(encoding="utf-8"))

        entries = self.adapter._map_lesson_topics(payload)

        self.assertEqual([entry.hour_number for entry in entries], [1, 2])
        self.assertEqual(entries[0].cosignatures[0].teacher, "DOCENTE TEST SUPPORTO")

    def test_map_subjects_keeps_objective_details_for_star_grades(self):
        payload = json.loads((FIXTURES / "subject_grades_detail.json").read_text(encoding="utf-8"))

        subjects = self.adapter._map_subjects(payload)

        self.assertEqual(subjects[0].entries[0].value, "*")
        self.assertEqual(subjects[0].entries[0].objectives[0].name, "Conoscenze")


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from nuvola.adapters.legacy_student_api.adapter import LegacyStudentApiAdapter
from nuvola.domain.models import SessionContext

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"
STUDENT_FIXTURES = FIXTURES / "student_readonly"


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
        self.fixture_map = {
            "https://nuvola.test/api-studente/v1/alunno/9009/voti": STUDENT_FIXTURES / "latest_grades.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/assenze": STUDENT_FIXTURES / "absences.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/note": STUDENT_FIXTURES / "notes.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/eventi-classe": STUDENT_FIXTURES / "class_events.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/eventi-classe-materia": STUDENT_FIXTURES / "subject_events.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/eventi-alunno": STUDENT_FIXTURES / "student_events.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/pagamenti": STUDENT_FIXTURES / "payments.json",
            "https://nuvola.test/api-studente/v1/bacheche-digitali": STUDENT_FIXTURES / "noticeboards.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/questionari": STUDENT_FIXTURES / "questionnaires.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/moduli-compilabili": STUDENT_FIXTURES / "fillable_forms.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/colloqui/prenotati": STUDENT_FIXTURES / "booked_meetings.json",
            "https://nuvola.test/api-studente/v1/materiali-per-docente": STUDENT_FIXTURES / "teacher_materials.json",
            "https://nuvola.test/api-studente/v1/alunno/9009/menu": None,
        }

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
        if url.endswith("/api-studente/v1/alunno/9009/compito/elenco/09-03-2026/15-03-2026"):
            payload = json.loads((FIXTURES / "homework_range.json").read_text(encoding="utf-8"))
            return _FakeResponse(json_payload=payload)
        if url.endswith("/api-studente/v1/alunno/9009/menu"):
            return _FakeResponse(
                json_payload={
                    "opzioni": [
                        {"opzione": "compito_accesso_lista", "impostazione": True},
                        {"opzione": "voto_accesso_sezione_abilitato", "impostazione": False},
                    ]
                }
            )
        fixture_path = self.fixture_map.get(url)
        if fixture_path:
            return _FakeResponse(json_payload=json.loads(fixture_path.read_text(encoding="utf-8")))
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
            "9009",
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
                    "https://nuvola.test/api-studente/v1/alunno/9009/compito/elenco/09-03-2026/15-03-2026",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
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

    def test_get_student_menu_options_maps_known_entries(self):
        session = _FakeSession()
        adapter = LegacyStudentApiAdapter(session=session, base_url="https://nuvola.test")

        options = adapter.get_student_menu_options(
            SessionContext(backend="legacy_student", token="BEARER_TOKEN"),
            "9009",
        )

        self.assertEqual(
            options,
            {
                "compito_accesso_lista": True,
                "voto_accesso_sezione_abilitato": False,
            },
        )
        self.assertEqual(
            session.calls,
            [
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/menu",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
                )
            ],
        )

    def test_list_latest_grades_uses_home_endpoint_and_maps_entries(self):
        session = _FakeSession()
        adapter = LegacyStudentApiAdapter(session=session, base_url="https://nuvola.test")

        items = adapter.list_latest_grades(
            SessionContext(backend="legacy_student", token="BEARER_TOKEN"),
            "9009",
            limit=4,
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].subject, "MATERIA TEST")
        self.assertEqual(items[0].subject_id, "524")
        self.assertEqual(items[0].period_id, "134")
        self.assertEqual(items[0].entry.math_value, "9.25")
        self.assertEqual(items[0].entry.objectives[0].name, "conoscenze")
        self.assertEqual(items[0].raw["nomeMateria"], "MATERIA TEST")
        self.assertEqual(
            session.calls,
            [
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/voti",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "limit": 4},
                )
            ],
        )

    def test_map_menu_options_handles_missing_non_list_and_malformed_items(self):
        self.assertEqual(self.adapter._map_menu_options({}), {})
        self.assertEqual(self.adapter._map_menu_options({"opzioni": "nope"}), {})
        self.assertEqual(
            self.adapter._map_menu_options(
                {
                    "opzioni": [
                        None,
                        {},
                        {"opzione": ""},
                        {"opzione": "nota_accesso_sezione_abilitato", "impostazione": True},
                    ]
                }
            ),
            {"nota_accesso_sezione_abilitato": True},
        )

    def test_read_only_student_endpoints_use_expected_paths_and_params(self):
        session = _FakeSession()
        adapter = LegacyStudentApiAdapter(session=session, base_url="https://nuvola.test")
        context = SessionContext(backend="legacy_student", token="BEARER_TOKEN")

        absences = adapter.list_absences(context, "9009", limit=5)
        notes = adapter.list_notes(context, "9009", limit=7)
        class_events = adapter.list_class_events(context, "9009")
        planner_events = adapter.list_class_events(context, "9009", only_planner_visible=True)
        subject_events = adapter.list_subject_events(context, "9009", page=2, limit=11, ordering="custom_desc")
        student_events = adapter.list_student_events(context, "9009", page=3, limit=12, ordering="student_desc")
        payments = adapter.list_payments(context, "9009", status="pagato", page=4, limit=6)
        noticeboards = adapter.list_noticeboards(context, "9009", limit=99)
        questionnaires = adapter.list_questionnaires(context, "9009")
        fillable_forms = adapter.list_fillable_forms(context, "9009")
        booked_meetings = adapter.list_booked_meetings(context, "9009")
        teacher_materials = adapter.list_teacher_materials(context, "9009")

        self.assertEqual(absences[0].kind, "ASSENZA")
        self.assertEqual(absences[0].raw["descrizione"], "Assenza per l'intera giornata")
        self.assertEqual(notes[0].teacher, "DOCENTE TEST 2")
        self.assertEqual(class_events[0].scope, "class")
        self.assertEqual(planner_events[0].title, "Assemblea di classe")
        self.assertEqual(subject_events[0].scope, "subject")
        self.assertEqual(student_events[0].scope, "student")
        self.assertEqual(payments[0].amount, "35.50")
        self.assertEqual(noticeboards[0].item_count, 3)
        self.assertEqual(noticeboards[0].actions[0]["name"], "read")
        self.assertEqual(questionnaires[0].status, "APERTO")
        self.assertEqual(fillable_forms[0].title, "Autorizzazione uscita")
        self.assertEqual(booked_meetings[0].teacher, "DOCENTE TEST 3")
        self.assertEqual(teacher_materials[0].attachments[0]["nome"], "relazione.pdf")
        self.assertEqual(
            session.calls,
            [
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/assenze",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "limit": 5},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/note",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "limit": 7},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/eventi-classe",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "filter[ordinamento]": "data_inizio_desc", "page": 1, "limit": 25},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/eventi-classe",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "soloVisibiliPlanner": "true"},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/eventi-classe-materia",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "filter[ordinamento]": "custom_desc", "page": 2, "limit": 11},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/eventi-alunno",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "filter[ordinamento]": "student_desc", "page": 3, "limit": 12},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/pagamenti",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009", "filter[stato]": "pagato", "page": 4, "limit": 6},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/bacheche-digitali",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"fields": "id,nome", "metadata": "count,actions", "limit": 99, "contextAlunno": "9009"},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/questionari",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/moduli-compilabili",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/alunno/9009/colloqui/prenotati",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
                ),
                (
                    "GET",
                    "https://nuvola.test/api-studente/v1/materiali-per-docente",
                    {"authorization": "Bearer BEARER_TOKEN"},
                    None,
                    {"contextAlunno": "9009"},
                ),
            ],
        )

    def test_map_payments_handles_real_world_field_names(self):
        payments = self.adapter._map_payments(
            {
                "valori": [
                    {
                        "id": "x1",
                        "tassa": "Quota viaggio",
                        "statoPagamento": "DA PAGARE",
                        "importo": "18,00 €",
                        "dataScadenzaRata": "2026-06-03T00:00:00+02:00",
                    }
                ]
            }
        )

        self.assertEqual(payments[0].title, "Quota viaggio")
        self.assertEqual(payments[0].status, "DA PAGARE")
        self.assertEqual(payments[0].amount, "18,00 €")
        self.assertEqual(payments[0].due_date.isoformat(), "2026-06-03T00:00:00+02:00")

    def test_map_noticeboards_keeps_collection_metadata_in_raw(self):
        noticeboards = self.adapter._map_noticeboards(
            {
                "count": 1,
                "actions": [{"name": "read"}],
                "data": [{"id": 6, "nome": "COMUNICAZIONI"}],
            }
        )

        self.assertEqual(noticeboards[0].name, "COMUNICAZIONI")
        self.assertEqual(noticeboards[0].actions[0]["name"], "read")
        self.assertEqual(noticeboards[0].raw["_collection_count"], 1)


if __name__ == "__main__":
    unittest.main()

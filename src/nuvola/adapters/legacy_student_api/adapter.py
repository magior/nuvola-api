"""Adapter per gli endpoint legacy `api-studente/v1`."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from nuvola.application.dates import format_api_date, parse_api_datetime
from nuvola.domain.models import (
    AbsenceItem,
    BookedMeetingItem,
    EventItem,
    FillableFormItem,
    GradeEntry,
    GradeObjective,
    GradePeriod,
    HomeworkItem,
    LessonCoSignature,
    LessonTopicEntry,
    LatestGradeItem,
    NoteItem,
    NoticeboardItem,
    PaymentItem,
    QuestionnaireItem,
    SessionContext,
    Student,
    SubjectGrades,
    TeacherMaterialItem,
)

STANDARD_HOMEWORK_DATE_KEYS = {"dataAssegnazione", "dataConsegna"}


class LegacyStudentApiAdapter:
    backend_name = "legacy_student"
    _csrf_patterns = (
        re.compile(r'name=["\']_csrf_token["\'][^>]*value=["\']([^"\']+)["\']'),
        re.compile(r'value=["\']([^"\']+)["\'][^>]*name=["\']_csrf_token["\']'),
    )

    def __init__(self, session: Optional[Any] = None, base_url: str = "https://nuvola.madisoft.it"):
        self.session = session
        self.base_url = base_url.rstrip("/")

    def _session(self) -> Any:
        if self.session is not None:
            return self.session
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "Il pacchetto 'requests' e' necessario per usare il backend legacy_student."
            ) from exc
        self.session = requests.Session()
        return self.session

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _headers(self, token: str) -> Dict[str, str]:
        return {"authorization": "Bearer " + token}

    def _get_json(self, path: str, *, headers=None, cookies=None, params=None) -> dict:
        response = self._session().get(
            self._url(path),
            headers=headers,
            cookies=cookies,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def _extract_cookie(self, response: Any) -> Optional[str]:
        token = response.cookies.get("nuvola")
        if token:
            return token
        session = self._session()
        token = session.cookies.get("nuvola") if getattr(session, "cookies", None) is not None else None
        if token:
            return token
        for history_response in reversed(getattr(response, "history", [])):
            token = history_response.cookies.get("nuvola")
            if token:
                return token
        return None

    def _extract_csrf_token(self, html: str) -> str:
        for pattern in self._csrf_patterns:
            match = pattern.search(html)
            if match:
                return match.group(1)
        raise RuntimeError("Token CSRF non trovato nella pagina di login.")

    def _map_students(self, payload: dict) -> List[Student]:
        students = []
        for item in payload.get("valori", []):
            students.append(
                Student(
                    id=str(item["id"]),
                    first_name=item["nome"],
                    last_name=item["cognome"],
                    class_name=item["classe"],
                    school_year=str(item["annoScolastico"]),
                )
            )
        return students

    def _map_periods(self, payload: dict) -> List[GradePeriod]:
        return [
            GradePeriod(id=str(item["id"]), name=item["nome"])
            for item in payload.get("valori", [])
        ]

    def _map_subjects(self, payload: dict) -> List[SubjectGrades]:
        subjects = []
        for item in payload.get("valori", []):
            entries = []
            for vote in item.get("voti", []):
                entries.append(self._map_grade_entry(vote))
            subjects.append(
                SubjectGrades(
                    subject_id=str(item.get("id", "")),
                    subject=item.get("materia", "-"),
                    grade_count=int(item.get("conteggioVoti", len(entries) or 0)),
                    average=str(item.get("media")) if item.get("media") is not None else None,
                    entries=entries,
                )
            )
        return subjects

    def _map_grade_entry(self, vote: dict) -> GradeEntry:
        objectives = [
            GradeObjective(
                name=objective.get("nome", "-"),
                value=objective.get("valutazione", "-"),
                description=objective.get("descrizione"),
            )
            for objective in vote.get("obiettivi", [])
        ]
        return GradeEntry(
            date=parse_api_datetime(vote.get("data")),
            value=vote.get("valutazione", "-"),
            teacher=vote.get("docente"),
            kind=vote.get("tipologia"),
            description=vote.get("descrizione"),
            weight=vote.get("peso"),
            objective_name=vote.get("nomeObiettivo"),
            math_value=vote.get("valutazioneMatematica"),
            in_average=vote.get("faMedia"),
            objectives=objectives,
        )

    def _map_latest_grades(self, payload: object) -> List[LatestGradeItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                LatestGradeItem(
                    subject_id=str(item.get("idMateria", "")),
                    subject=self._first_non_empty(item, "nomeMateria", "materia") or "-",
                    period_id=str(item.get("idFrazioneTemporale", "")),
                    entry=self._map_grade_entry(item),
                    raw=dict(item),
                )
            )
        return items

    def _map_homework(self, payload: dict) -> List[HomeworkItem]:
        items = []
        for item in payload.get("valori", []):
            extra_dates = {}
            for key, value in item.items():
                if "data" in key.lower() and key not in STANDARD_HOMEWORK_DATE_KEYS and value:
                    extra_dates[key] = value

            description = item.get("descrizioneCompito")
            if isinstance(description, list):
                values = [part for part in description if part]
                description = " | ".join(values) if values else "Niente Compiti"
            elif not description:
                description = "Niente Compiti"

            items.append(
                HomeworkItem(
                    subject=item.get("materia", "-"),
                    description=description,
                    due_date=parse_api_datetime(item.get("dataConsegna")),
                    assigned_date=parse_api_datetime(item.get("dataAssegnazione")),
                    teacher=item.get("docente"),
                    topic_name=item.get("nomeArgomento"),
                    extra_dates=extra_dates,
                )
            )
        return items

    def _map_lesson_topics(self, payload: dict) -> List[LessonTopicEntry]:
        entries = []
        for day_group in payload.get("valori", []):
            class_name = day_group.get("classe", "-")
            class_id = str(day_group.get("classeId", ""))
            for hour in day_group.get("ore", []):
                day_value = parse_api_datetime(hour.get("giorno"))
                if day_value is None:
                    continue
                for topic in hour.get("argomenti", []):
                    cosignatures = [
                        LessonCoSignature(
                            teacher=item.get("docente", ""),
                            role=item.get("compresenza", ""),
                            signed=bool(item.get("firmato")),
                        )
                        for item in topic.get("cofirme", [])
                    ]
                    entries.append(
                        LessonTopicEntry(
                            lesson_id=str(topic.get("id", "")),
                            class_name=class_name,
                            class_id=class_id,
                            day=day_value.date(),
                            hour_number=int(hour.get("numeroOra", 0)),
                            starts_at=hour.get("inizioOra", ""),
                            ends_at=hour.get("fineOra", ""),
                            subject=topic.get("materia", "-"),
                            teacher=topic.get("docente"),
                            lesson_type=topic.get("tipo"),
                            topic_name=topic.get("nomeArgomento", ""),
                            annotations=topic.get("annotazioni"),
                            extended_description=topic.get("descrizioneEstesa"),
                            co_presence=topic.get("compresenza"),
                            attachments=list(topic.get("allegati", [])),
                            cosignatures=cosignatures,
                            videos=list(topic.get("video_youtube", [])),
                        )
                    )
        return sorted(entries, key=lambda item: (item.day, item.hour_number, item.subject, item.topic_name))

    def _payload_items(self, payload: object) -> List[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("valori", "items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    @staticmethod
    def _as_dict(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _first_non_empty(item: dict, *keys: str) -> Optional[str]:
        for key in keys:
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    def _first_datetime(self, item: dict, *keys: str):
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value:
                try:
                    return parse_api_datetime(value)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _safe_int(value: object) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _map_menu_options(self, payload: dict) -> dict[str, object]:
        raw_options = payload.get("opzioni")
        if not isinstance(raw_options, list):
            return {}
        options: dict[str, object] = {}
        for item in raw_options:
            if not isinstance(item, dict):
                continue
            option_name = item.get("opzione")
            if not option_name:
                continue
            options[str(option_name)] = item.get("impostazione")
        return options

    def _map_absences(self, payload: object) -> List[AbsenceItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                AbsenceItem(
                    id=str(item.get("id", "")),
                    day=self._first_datetime(item, "giorno", "data", "dataEvento", "dataInizio"),
                    kind=self._first_non_empty(item, "tipo", "tipologia", "stato", "categoria"),
                    description=self._first_non_empty(item, "descrizione", "motivazione", "note", "titolo"),
                    raw=dict(item),
                )
            )
        return items

    def _map_notes(self, payload: object) -> List[NoteItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                NoteItem(
                    id=str(item.get("id", "")),
                    day=self._first_datetime(item, "giorno", "data", "dataNota"),
                    kind=self._first_non_empty(item, "tipo", "tipologia", "categoria"),
                    teacher=self._first_non_empty(item, "docente", "insegnante", "autore"),
                    description=self._first_non_empty(item, "descrizione", "testo", "nota", "oggetto", "titolo"),
                    raw=dict(item),
                )
            )
        return items

    def _map_events(self, payload: object, scope: str) -> List[EventItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                EventItem(
                    id=str(item.get("id", "")),
                    scope=scope,
                    title=self._first_non_empty(item, "titolo", "nome", "oggetto", "descrizioneBreve", "descrizione"),
                    starts_at=self._first_datetime(item, "dataInizio", "inizio", "data", "giorno"),
                    ends_at=self._first_datetime(item, "dataFine", "fine"),
                    description=self._first_non_empty(item, "descrizione", "testo", "contenuto"),
                    raw=dict(item),
                )
            )
        return items

    def _map_payments(self, payload: object) -> List[PaymentItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                PaymentItem(
                    id=str(item.get("id", "")),
                    title=self._first_non_empty(item, "titolo", "tassa", "causale", "descrizione", "nome"),
                    status=self._first_non_empty(item, "statoPagamento", "stato", "status"),
                    amount=self._first_non_empty(item, "importoTotale", "importo", "ammontare"),
                    due_date=self._first_datetime(item, "dataScadenzaRata", "scadenza", "dataScadenza", "data"),
                    raw=dict(item),
                )
            )
        return items

    def _map_noticeboards(self, payload: object) -> List[NoticeboardItem]:
        top_level = self._as_dict(payload)
        top_level_actions = top_level.get("actions")
        actions_fallback = top_level_actions if isinstance(top_level_actions, list) else []
        items = []
        for item in self._payload_items(payload):
            metadata = self._as_dict(item.get("metadata"))
            actions_value = item.get("actions", metadata.get("actions"))
            actions = actions_value if isinstance(actions_value, list) else []
            raw = dict(item)
            if "count" in top_level:
                raw.setdefault("_collection_count", top_level.get("count"))
            if actions_fallback:
                raw.setdefault("_collection_actions", actions_fallback)
            items.append(
                NoticeboardItem(
                    id=str(item.get("id", "")),
                    name=self._first_non_empty(item, "nome", "titolo", "name"),
                    item_count=self._safe_int(item.get("count", metadata.get("count", item.get("conteggio")))),
                    actions=[action for action in (actions or actions_fallback) if isinstance(action, dict)],
                    raw=raw,
                )
            )
        return items

    def _map_questionnaires(self, payload: object) -> List[QuestionnaireItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                QuestionnaireItem(
                    id=str(item.get("id", "")),
                    title=self._first_non_empty(item, "titolo", "nome", "oggetto"),
                    status=self._first_non_empty(item, "stato", "status"),
                    deadline=self._first_datetime(item, "scadenza", "dataScadenza", "termine"),
                    raw=dict(item),
                )
            )
        return items

    def _map_fillable_forms(self, payload: object) -> List[FillableFormItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                FillableFormItem(
                    id=str(item.get("id", "")),
                    title=self._first_non_empty(item, "titolo", "nome", "oggetto"),
                    status=self._first_non_empty(item, "stato", "status"),
                    deadline=self._first_datetime(item, "scadenza", "dataScadenza", "termine"),
                    raw=dict(item),
                )
            )
        return items

    def _map_booked_meetings(self, payload: object) -> List[BookedMeetingItem]:
        items = []
        for item in self._payload_items(payload):
            items.append(
                BookedMeetingItem(
                    id=str(item.get("id", "")),
                    teacher=self._first_non_empty(item, "docente", "insegnante", "teacher"),
                    starts_at=self._first_datetime(item, "dataInizio", "inizio", "startAt"),
                    ends_at=self._first_datetime(item, "dataFine", "fine", "endAt"),
                    status=self._first_non_empty(item, "stato", "status"),
                    raw=dict(item),
                )
            )
        return items

    def _map_teacher_materials(self, payload: object) -> List[TeacherMaterialItem]:
        items = []
        for item in self._payload_items(payload):
            attachments = item.get("allegati", item.get("attachments", []))
            items.append(
                TeacherMaterialItem(
                    id=str(item.get("id", "")),
                    title=self._first_non_empty(item, "titolo", "oggetto", "nome"),
                    teacher=self._first_non_empty(item, "docente", "insegnante", "teacher"),
                    subject=self._first_non_empty(item, "materia", "subject"),
                    created_at=self._first_datetime(item, "dataCreazione", "createdAt", "data"),
                    attachments=[value for value in attachments if isinstance(value, dict)] if isinstance(attachments, list) else [],
                    raw=dict(item),
                )
            )
        return items

    def authenticate(self, username: str, password: str, tenant: Optional[str] = None) -> SessionContext:
        login_page = self._session().get(self.base_url)
        login_page.raise_for_status()
        csrf_token = self._extract_csrf_token(login_page.text)

        response = self._session().post(
            self._url("/login_check"),
            data={
                "_username": username,
                "_password": password,
                "_csrf_token": csrf_token,
            },
        )
        response.raise_for_status()
        session_token = self._extract_cookie(response)
        cookies = {"nuvola": session_token} if session_token else None
        payload = self._get_json("/api-studente/v1/login-from-web", cookies=cookies)
        token = payload.get("token")
        if not token:
            raise RuntimeError("Nuvola non ha restituito un token API.")
        return SessionContext(backend=self.backend_name, token=token, tenant=tenant)

    def list_students(self, session: SessionContext) -> List[Student]:
        payload = self._get_json("/api-studente/v1/alunni", headers=self._headers(session.token))
        students = self._map_students(payload)
        if not students:
            raise ValueError("Nessun alunno associato al token corrente.")
        return students

    def list_grade_periods(self, session: SessionContext, student_id: str) -> List[GradePeriod]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/frazioni-temporali",
            headers=self._headers(session.token),
        )
        return self._map_periods(payload)

    def list_latest_grades(self, session: SessionContext, student_id: str, limit: int = 10) -> List[LatestGradeItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/voti",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id, "limit": limit},
        )
        return self._map_latest_grades(payload)

    def list_subject_grades(
        self,
        session: SessionContext,
        student_id: str,
        period_id: str,
    ) -> List[SubjectGrades]:
        summary_payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/frazione-temporale/{period_id}/voti/materie",
            headers=self._headers(session.token),
        )
        subjects = self._map_subjects(summary_payload)
        detailed = []
        for subject in subjects:
            if not subject.subject_id or subject.grade_count == 0:
                detailed.append(subject)
                continue
            try:
                payload = self._get_json(
                    (
                        f"/api-studente/v1/alunno/{student_id}/frazione-temporale/{period_id}/"
                        f"voti/materia/{subject.subject_id}"
                    ),
                    headers=self._headers(session.token),
                    params={"contextAlunno": student_id},
                )
            except Exception:
                detailed.append(subject)
                continue
            mapped = self._map_subjects(payload)
            detailed.append(mapped[0] if mapped else subject)
        return detailed

    def list_homework(self, session: SessionContext, student_id: str, start_date, end_date) -> List[HomeworkItem]:
        payload = self._get_json(
            (
                f"/api-studente/v1/alunno/{student_id}/compito/elenco/"
                f"{format_api_date(start_date)}/{format_api_date(end_date)}"
            ),
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        items = self._map_homework(payload)
        return sorted(
            items,
            key=lambda item: (
                item.due_date.isoformat() if item.due_date else "",
                item.subject,
                item.description,
            ),
        )

    def list_lesson_topics(self, session: SessionContext, student_id: str, start_date, end_date) -> List[LessonTopicEntry]:
        payload = self._get_json(
            (
                f"/api-studente/v1/alunno/{student_id}/argomento-lezione/elenco/"
                f"{format_api_date(start_date)}/{format_api_date(end_date)}"
            ),
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_lesson_topics(payload)

    def get_student_menu_options(self, session: SessionContext, student_id: str) -> dict[str, object]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/menu",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_menu_options(payload)

    def list_absences(self, session: SessionContext, student_id: str, limit: int = 10) -> List[AbsenceItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/assenze",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id, "limit": limit},
        )
        return self._map_absences(payload)

    def list_notes(self, session: SessionContext, student_id: str, limit: int = 10) -> List[NoteItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/note",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id, "limit": limit},
        )
        return self._map_notes(payload)

    def list_class_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
        only_planner_visible: Optional[bool] = None,
    ) -> List[EventItem]:
        params = {"contextAlunno": student_id}
        if only_planner_visible is None:
            params.update({"filter[ordinamento]": ordering, "page": page, "limit": limit})
        else:
            params["soloVisibiliPlanner"] = "true" if only_planner_visible else "false"
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/eventi-classe",
            headers=self._headers(session.token),
            params=params,
        )
        return self._map_events(payload, scope="class")

    def list_subject_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/eventi-classe-materia",
            headers=self._headers(session.token),
            params={
                "contextAlunno": student_id,
                "filter[ordinamento]": ordering,
                "page": page,
                "limit": limit,
            },
        )
        return self._map_events(payload, scope="subject")

    def list_student_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/eventi-alunno",
            headers=self._headers(session.token),
            params={
                "contextAlunno": student_id,
                "filter[ordinamento]": ordering,
                "page": page,
                "limit": limit,
            },
        )
        return self._map_events(payload, scope="student")

    def list_payments(
        self,
        session: SessionContext,
        student_id: str,
        status: str = "daPagare",
        page: int = 1,
        limit: int = 10,
    ) -> List[PaymentItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/pagamenti",
            headers=self._headers(session.token),
            params={
                "contextAlunno": student_id,
                "filter[stato]": status,
                "page": page,
                "limit": limit,
            },
        )
        return self._map_payments(payload)

    def list_noticeboards(self, session: SessionContext, student_id: str, limit: int = 1000) -> List[NoticeboardItem]:
        payload = self._get_json(
            "/api-studente/v1/bacheche-digitali",
            headers=self._headers(session.token),
            params={
                "fields": "id,nome",
                "metadata": "count,actions",
                "limit": limit,
                "contextAlunno": student_id,
            },
        )
        return self._map_noticeboards(payload)

    def list_questionnaires(self, session: SessionContext, student_id: str) -> List[QuestionnaireItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/questionari",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_questionnaires(payload)

    def list_fillable_forms(self, session: SessionContext, student_id: str) -> List[FillableFormItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/moduli-compilabili",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_fillable_forms(payload)

    def list_booked_meetings(self, session: SessionContext, student_id: str) -> List[BookedMeetingItem]:
        payload = self._get_json(
            f"/api-studente/v1/alunno/{student_id}/colloqui/prenotati",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_booked_meetings(payload)

    def list_teacher_materials(self, session: SessionContext, student_id: str) -> List[TeacherMaterialItem]:
        payload = self._get_json(
            "/api-studente/v1/materiali-per-docente",
            headers=self._headers(session.token),
            params={"contextAlunno": student_id},
        )
        return self._map_teacher_materials(payload)

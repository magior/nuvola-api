"""Adapter per gli endpoint legacy `api-studente/v1`."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from nuvola.application.dates import format_api_date, parse_api_datetime
from nuvola.domain.models import (
    GradeEntry,
    GradeObjective,
    GradePeriod,
    HomeworkItem,
    LessonCoSignature,
    LessonTopicEntry,
    SessionContext,
    Student,
    SubjectGrades,
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
                objectives = [
                    GradeObjective(
                        name=objective.get("nome", "-"),
                        value=objective.get("valutazione", "-"),
                        description=objective.get("descrizione"),
                    )
                    for objective in vote.get("obiettivi", [])
                ]
                entries.append(
                    GradeEntry(
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
                )
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

from __future__ import annotations

from typing import Dict, List, Optional

from nuvola.domain.contracts import BackendAdapter, SessionStore
from nuvola.domain.models import GradePeriod, HomeworkItem, LessonTopicEntry, SessionContext, Student, SubjectGrades


def resolve_backend(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    name: Optional[str] = None,
) -> BackendAdapter:
    backend_name = name or default_backend
    try:
        return backends[backend_name]
    except KeyError as exc:
        raise ValueError(f"Backend non supportato: {backend_name}") from exc


def login(
    backends: Dict[str, BackendAdapter],
    session_store: SessionStore,
    default_backend: str,
    username: str,
    password: str,
    backend: Optional[str] = None,
    tenant: Optional[str] = None,
) -> SessionContext:
    adapter = resolve_backend(backends, default_backend, backend)
    session = adapter.authenticate(username, password, tenant=tenant)
    session_store.save(session)
    return session


def resume_session(session_store: SessionStore) -> Optional[SessionContext]:
    return session_store.load()


def persist_session(session_store: SessionStore, session: SessionContext) -> None:
    session_store.save(session)


def clear_session(session_store: SessionStore) -> None:
    session_store.clear()


def select_student(session_store: SessionStore, session: SessionContext, student_id: str) -> SessionContext:
    updated = session.with_student(student_id)
    session_store.save(updated)
    return updated


def list_students(backends: Dict[str, BackendAdapter], default_backend: str, session: SessionContext) -> List[Student]:
    return resolve_backend(backends, default_backend, session.backend).list_students(session)


def list_grade_periods(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> List[GradePeriod]:
    return resolve_backend(backends, default_backend, session.backend).list_grade_periods(session, student_id)


def list_subject_grades(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    period_id: str,
) -> List[SubjectGrades]:
    return resolve_backend(backends, default_backend, session.backend).list_subject_grades(
        session,
        student_id,
        period_id,
    )


def list_homework(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    start_date,
    end_date,
) -> List[HomeworkItem]:
    return resolve_backend(backends, default_backend, session.backend).list_homework(
        session,
        student_id,
        start_date,
        end_date,
    )


def list_lesson_topics(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    start_date,
    end_date,
) -> List[LessonTopicEntry]:
    return resolve_backend(backends, default_backend, session.backend).list_lesson_topics(
        session,
        student_id,
        start_date,
        end_date,
    )

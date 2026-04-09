from __future__ import annotations

from typing import Dict, List, Optional

from nuvola.domain.contracts import BackendAdapter, SessionStore
from nuvola.domain.models import (
    AbsenceItem,
    BookedMeetingItem,
    EventItem,
    FillableFormItem,
    GradePeriod,
    HomeworkItem,
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


def list_latest_grades(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    limit: int = 10,
) -> List[LatestGradeItem]:
    return resolve_backend(backends, default_backend, session.backend).list_latest_grades(
        session,
        student_id,
        limit=limit,
    )


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


def get_student_menu_options(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> dict[str, object]:
    return resolve_backend(backends, default_backend, session.backend).get_student_menu_options(session, student_id)


def list_absences(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    limit: int = 10,
) -> List[AbsenceItem]:
    return resolve_backend(backends, default_backend, session.backend).list_absences(session, student_id, limit=limit)


def list_notes(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    limit: int = 10,
) -> List[NoteItem]:
    return resolve_backend(backends, default_backend, session.backend).list_notes(session, student_id, limit=limit)


def list_class_events(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    page: int = 1,
    limit: int = 25,
    ordering: str = "data_inizio_desc",
    only_planner_visible: Optional[bool] = None,
) -> List[EventItem]:
    return resolve_backend(backends, default_backend, session.backend).list_class_events(
        session,
        student_id,
        page=page,
        limit=limit,
        ordering=ordering,
        only_planner_visible=only_planner_visible,
    )


def list_subject_events(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    page: int = 1,
    limit: int = 25,
    ordering: str = "data_inizio_desc",
) -> List[EventItem]:
    return resolve_backend(backends, default_backend, session.backend).list_subject_events(
        session,
        student_id,
        page=page,
        limit=limit,
        ordering=ordering,
    )


def list_student_events(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    page: int = 1,
    limit: int = 25,
    ordering: str = "data_inizio_desc",
) -> List[EventItem]:
    return resolve_backend(backends, default_backend, session.backend).list_student_events(
        session,
        student_id,
        page=page,
        limit=limit,
        ordering=ordering,
    )


def list_payments(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    status: str = "daPagare",
    page: int = 1,
    limit: int = 10,
) -> List[PaymentItem]:
    return resolve_backend(backends, default_backend, session.backend).list_payments(
        session,
        student_id,
        status=status,
        page=page,
        limit=limit,
    )


def list_noticeboards(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
    limit: int = 1000,
) -> List[NoticeboardItem]:
    return resolve_backend(backends, default_backend, session.backend).list_noticeboards(
        session,
        student_id,
        limit=limit,
    )


def list_questionnaires(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> List[QuestionnaireItem]:
    return resolve_backend(backends, default_backend, session.backend).list_questionnaires(session, student_id)


def list_fillable_forms(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> List[FillableFormItem]:
    return resolve_backend(backends, default_backend, session.backend).list_fillable_forms(session, student_id)


def list_booked_meetings(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> List[BookedMeetingItem]:
    return resolve_backend(backends, default_backend, session.backend).list_booked_meetings(session, student_id)


def list_teacher_materials(
    backends: Dict[str, BackendAdapter],
    default_backend: str,
    session: SessionContext,
    student_id: str,
) -> List[TeacherMaterialItem]:
    return resolve_backend(backends, default_backend, session.backend).list_teacher_materials(session, student_id)

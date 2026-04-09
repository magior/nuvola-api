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

from . import use_cases


class NuvolaService:
    def __init__(
        self,
        backends: Dict[str, BackendAdapter],
        session_store: SessionStore,
        default_backend: str = "legacy_student",
    ):
        self.backends = backends
        self.session_store = session_store
        self.default_backend = default_backend

    def _backend(self, name: str) -> BackendAdapter:
        return use_cases.resolve_backend(self.backends, self.default_backend, name)

    def login(
        self,
        username: str,
        password: str,
        backend: Optional[str] = None,
        tenant: Optional[str] = None,
    ) -> SessionContext:
        return use_cases.login(
            self.backends,
            self.session_store,
            self.default_backend,
            username,
            password,
            backend=backend,
            tenant=tenant,
        )

    def resume_session(self) -> Optional[SessionContext]:
        return use_cases.resume_session(self.session_store)

    def clear_session(self) -> None:
        use_cases.clear_session(self.session_store)

    def persist_session(self, session: SessionContext) -> None:
        use_cases.persist_session(self.session_store, session)

    def select_student(self, session: SessionContext, student_id: str) -> SessionContext:
        return use_cases.select_student(self.session_store, session, student_id)

    def list_students(self, session: SessionContext) -> List[Student]:
        return use_cases.list_students(self.backends, self.default_backend, session)

    def list_grade_periods(self, session: SessionContext, student_id: str) -> List[GradePeriod]:
        return use_cases.list_grade_periods(self.backends, self.default_backend, session, student_id)

    def list_latest_grades(
        self,
        session: SessionContext,
        student_id: str,
        limit: int = 10,
    ) -> List[LatestGradeItem]:
        return use_cases.list_latest_grades(self.backends, self.default_backend, session, student_id, limit=limit)

    def list_subject_grades(
        self,
        session: SessionContext,
        student_id: str,
        period_id: str,
    ) -> List[SubjectGrades]:
        return use_cases.list_subject_grades(
            self.backends,
            self.default_backend,
            session,
            student_id,
            period_id,
        )

    def list_homework(
        self,
        session: SessionContext,
        student_id: str,
        start_date,
        end_date,
    ) -> List[HomeworkItem]:
        return use_cases.list_homework(
            self.backends,
            self.default_backend,
            session,
            student_id,
            start_date,
            end_date,
        )

    def list_lesson_topics(
        self,
        session: SessionContext,
        student_id: str,
        start_date,
        end_date,
    ) -> List[LessonTopicEntry]:
        return use_cases.list_lesson_topics(
            self.backends,
            self.default_backend,
            session,
            student_id,
            start_date,
            end_date,
        )

    def get_student_menu_options(self, session: SessionContext, student_id: str) -> dict[str, object]:
        return use_cases.get_student_menu_options(self.backends, self.default_backend, session, student_id)

    def list_absences(self, session: SessionContext, student_id: str, limit: int = 10) -> List[AbsenceItem]:
        return use_cases.list_absences(self.backends, self.default_backend, session, student_id, limit=limit)

    def list_notes(self, session: SessionContext, student_id: str, limit: int = 10) -> List[NoteItem]:
        return use_cases.list_notes(self.backends, self.default_backend, session, student_id, limit=limit)

    def list_class_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
        only_planner_visible: Optional[bool] = None,
    ) -> List[EventItem]:
        return use_cases.list_class_events(
            self.backends,
            self.default_backend,
            session,
            student_id,
            page=page,
            limit=limit,
            ordering=ordering,
            only_planner_visible=only_planner_visible,
        )

    def list_subject_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        return use_cases.list_subject_events(
            self.backends,
            self.default_backend,
            session,
            student_id,
            page=page,
            limit=limit,
            ordering=ordering,
        )

    def list_student_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        return use_cases.list_student_events(
            self.backends,
            self.default_backend,
            session,
            student_id,
            page=page,
            limit=limit,
            ordering=ordering,
        )

    def list_payments(
        self,
        session: SessionContext,
        student_id: str,
        status: str = "daPagare",
        page: int = 1,
        limit: int = 10,
    ) -> List[PaymentItem]:
        return use_cases.list_payments(
            self.backends,
            self.default_backend,
            session,
            student_id,
            status=status,
            page=page,
            limit=limit,
        )

    def list_noticeboards(
        self,
        session: SessionContext,
        student_id: str,
        limit: int = 1000,
    ) -> List[NoticeboardItem]:
        return use_cases.list_noticeboards(
            self.backends,
            self.default_backend,
            session,
            student_id,
            limit=limit,
        )

    def list_questionnaires(self, session: SessionContext, student_id: str) -> List[QuestionnaireItem]:
        return use_cases.list_questionnaires(self.backends, self.default_backend, session, student_id)

    def list_fillable_forms(self, session: SessionContext, student_id: str) -> List[FillableFormItem]:
        return use_cases.list_fillable_forms(self.backends, self.default_backend, session, student_id)

    def list_booked_meetings(self, session: SessionContext, student_id: str) -> List[BookedMeetingItem]:
        return use_cases.list_booked_meetings(self.backends, self.default_backend, session, student_id)

    def list_teacher_materials(self, session: SessionContext, student_id: str) -> List[TeacherMaterialItem]:
        return use_cases.list_teacher_materials(self.backends, self.default_backend, session, student_id)

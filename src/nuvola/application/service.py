from typing import Dict, List, Optional

from nuvola.domain.contracts import BackendAdapter, SessionStore
from nuvola.domain.models import GradePeriod, HomeworkItem, LessonTopicEntry, SessionContext, Student, SubjectGrades

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

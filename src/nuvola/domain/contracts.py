from typing import List, Optional, Protocol

from .models import GradePeriod, HomeworkItem, LessonTopicEntry, SessionContext, Student, SubjectGrades


class BackendAdapter(Protocol):
    backend_name: str

    def authenticate(self, username: str, password: str, tenant: Optional[str] = None) -> SessionContext:
        ...

    def list_students(self, session: SessionContext) -> List[Student]:
        ...

    def list_grade_periods(self, session: SessionContext, student_id: str) -> List[GradePeriod]:
        ...

    def list_subject_grades(
        self,
        session: SessionContext,
        student_id: str,
        period_id: str,
    ) -> List[SubjectGrades]:
        ...

    def list_homework(
        self,
        session: SessionContext,
        student_id: str,
        start_date,
        end_date,
    ) -> List[HomeworkItem]:
        ...

    def list_lesson_topics(
        self,
        session: SessionContext,
        student_id: str,
        start_date,
        end_date,
    ) -> List[LessonTopicEntry]:
        ...


class SessionStore(Protocol):
    def load(self) -> Optional[SessionContext]:
        ...

    def save(self, session: SessionContext) -> None:
        ...

    def clear(self) -> None:
        ...

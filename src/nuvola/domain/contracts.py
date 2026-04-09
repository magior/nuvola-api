from typing import List, Optional, Protocol

from .models import (
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


class BackendAdapter(Protocol):
    backend_name: str

    def authenticate(self, username: str, password: str, tenant: Optional[str] = None) -> SessionContext:
        ...

    def list_students(self, session: SessionContext) -> List[Student]:
        ...

    def list_grade_periods(self, session: SessionContext, student_id: str) -> List[GradePeriod]:
        ...

    def list_latest_grades(self, session: SessionContext, student_id: str, limit: int = 10) -> List[LatestGradeItem]:
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

    def get_student_menu_options(self, session: SessionContext, student_id: str) -> dict[str, object]:
        ...

    def list_absences(self, session: SessionContext, student_id: str, limit: int = 10) -> List[AbsenceItem]:
        ...

    def list_notes(self, session: SessionContext, student_id: str, limit: int = 10) -> List[NoteItem]:
        ...

    def list_class_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
        only_planner_visible: Optional[bool] = None,
    ) -> List[EventItem]:
        ...

    def list_subject_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        ...

    def list_student_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        ...

    def list_payments(
        self,
        session: SessionContext,
        student_id: str,
        status: str = "daPagare",
        page: int = 1,
        limit: int = 10,
    ) -> List[PaymentItem]:
        ...

    def list_noticeboards(
        self,
        session: SessionContext,
        student_id: str,
        limit: int = 1000,
    ) -> List[NoticeboardItem]:
        ...

    def list_questionnaires(self, session: SessionContext, student_id: str) -> List[QuestionnaireItem]:
        ...

    def list_fillable_forms(self, session: SessionContext, student_id: str) -> List[FillableFormItem]:
        ...

    def list_booked_meetings(self, session: SessionContext, student_id: str) -> List[BookedMeetingItem]:
        ...

    def list_teacher_materials(self, session: SessionContext, student_id: str) -> List[TeacherMaterialItem]:
        ...


class SessionStore(Protocol):
    def load(self) -> Optional[SessionContext]:
        ...

    def save(self, session: SessionContext) -> None:
        ...

    def clear(self) -> None:
        ...

from typing import List, Optional

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


class TenantApiAdapter:
    backend_name = "tenant"

    def __init__(self, base_template: str = "https://{tenant}.nuvola.madisoft.it"):
        self.base_template = base_template

    def _base_url(self, tenant: Optional[str]) -> str:
        if not tenant:
            raise ValueError("Il backend tenant richiede NUVOLA_TENANT oppure un tenant in sessione.")
        return self.base_template.format(tenant=tenant)

    def _not_implemented(self, operation: str, tenant: Optional[str] = None) -> NotImplementedError:
        base_url = self.base_template.format(tenant=tenant or "<tenant>")
        return NotImplementedError(
            f"{operation} non ancora implementato per tenant API. Tenant previsto: {tenant}. Base URL attesa: {base_url}"
        )

    def authenticate(self, username: str, password: str, tenant: Optional[str] = None) -> SessionContext:
        if not tenant:
            raise ValueError("Il backend tenant richiede un tenant esplicito.")
        raise self._not_implemented("authenticate", tenant)

    def list_students(self, session: SessionContext) -> List[Student]:
        raise self._not_implemented("list_students", session.tenant)

    def list_grade_periods(self, session: SessionContext, student_id: str) -> List[GradePeriod]:
        raise self._not_implemented("list_grade_periods", session.tenant)

    def list_latest_grades(self, session: SessionContext, student_id: str, limit: int = 10) -> List[LatestGradeItem]:
        raise self._not_implemented("list_latest_grades", session.tenant)

    def list_subject_grades(
        self,
        session: SessionContext,
        student_id: str,
        period_id: str,
    ) -> List[SubjectGrades]:
        raise self._not_implemented("list_subject_grades", session.tenant)

    def list_homework(self, session: SessionContext, student_id: str, start_date, end_date) -> List[HomeworkItem]:
        raise self._not_implemented("list_homework", session.tenant)

    def list_lesson_topics(self, session: SessionContext, student_id: str, start_date, end_date) -> List[LessonTopicEntry]:
        raise self._not_implemented("list_lesson_topics", session.tenant)

    def get_student_menu_options(self, session: SessionContext, student_id: str) -> dict[str, object]:
        raise self._not_implemented("get_student_menu_options", session.tenant)

    def list_absences(self, session: SessionContext, student_id: str, limit: int = 10) -> List[AbsenceItem]:
        raise self._not_implemented("list_absences", session.tenant)

    def list_notes(self, session: SessionContext, student_id: str, limit: int = 10) -> List[NoteItem]:
        raise self._not_implemented("list_notes", session.tenant)

    def list_class_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
        only_planner_visible: Optional[bool] = None,
    ) -> List[EventItem]:
        raise self._not_implemented("list_class_events", session.tenant)

    def list_subject_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        raise self._not_implemented("list_subject_events", session.tenant)

    def list_student_events(
        self,
        session: SessionContext,
        student_id: str,
        page: int = 1,
        limit: int = 25,
        ordering: str = "data_inizio_desc",
    ) -> List[EventItem]:
        raise self._not_implemented("list_student_events", session.tenant)

    def list_payments(
        self,
        session: SessionContext,
        student_id: str,
        status: str = "daPagare",
        page: int = 1,
        limit: int = 10,
    ) -> List[PaymentItem]:
        raise self._not_implemented("list_payments", session.tenant)

    def list_noticeboards(self, session: SessionContext, student_id: str, limit: int = 1000) -> List[NoticeboardItem]:
        raise self._not_implemented("list_noticeboards", session.tenant)

    def list_questionnaires(self, session: SessionContext, student_id: str) -> List[QuestionnaireItem]:
        raise self._not_implemented("list_questionnaires", session.tenant)

    def list_fillable_forms(self, session: SessionContext, student_id: str) -> List[FillableFormItem]:
        raise self._not_implemented("list_fillable_forms", session.tenant)

    def list_booked_meetings(self, session: SessionContext, student_id: str) -> List[BookedMeetingItem]:
        raise self._not_implemented("list_booked_meetings", session.tenant)

    def list_teacher_materials(self, session: SessionContext, student_id: str) -> List[TeacherMaterialItem]:
        raise self._not_implemented("list_teacher_materials", session.tenant)

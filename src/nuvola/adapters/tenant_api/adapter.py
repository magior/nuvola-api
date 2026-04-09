from typing import List, Optional

from nuvola.domain.models import GradePeriod, HomeworkItem, LessonTopicEntry, SessionContext, Student, SubjectGrades


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

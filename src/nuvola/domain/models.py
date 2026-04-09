from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SessionContext:
    backend: str
    token: Optional[str] = None
    student_id: Optional[str] = None
    tenant: Optional[str] = None

    def with_student(self, student_id: Optional[str]) -> "SessionContext":
        return replace(self, student_id=student_id)


@dataclass(frozen=True)
class Student:
    id: str
    first_name: str
    last_name: str
    class_name: str
    school_year: str

    @property
    def label(self) -> str:
        return (
            f"{self.first_name} {self.last_name} "
            f"- classe {self.class_name} - a.s. {self.school_year}"
        )


@dataclass(frozen=True)
class GradePeriod:
    id: str
    name: str


@dataclass(frozen=True)
class GradeObjective:
    name: str
    value: str
    description: Optional[str]


@dataclass(frozen=True)
class GradeEntry:
    date: Optional[datetime]
    value: str
    teacher: Optional[str]
    kind: Optional[str]
    description: Optional[str]
    weight: Optional[str]
    objective_name: Optional[str]
    math_value: Optional[str]
    in_average: Optional[bool]
    objectives: List[GradeObjective] = field(default_factory=list)


@dataclass(frozen=True)
class SubjectGrades:
    subject_id: str
    subject: str
    grade_count: int
    average: Optional[str]
    entries: List[GradeEntry]


@dataclass(frozen=True)
class HomeworkItem:
    subject: str
    description: str
    due_date: Optional[datetime]
    assigned_date: Optional[datetime]
    teacher: Optional[str]
    topic_name: Optional[str]
    extra_dates: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LessonCoSignature:
    teacher: str
    role: str
    signed: bool


@dataclass(frozen=True)
class LessonTopicEntry:
    lesson_id: str
    class_name: str
    class_id: str
    day: date
    hour_number: int
    starts_at: str
    ends_at: str
    subject: str
    teacher: Optional[str]
    lesson_type: Optional[str]
    topic_name: str
    annotations: Optional[str]
    extended_description: Optional[str]
    co_presence: Optional[str]
    attachments: List[dict] = field(default_factory=list)
    cosignatures: List[LessonCoSignature] = field(default_factory=list)
    videos: List[dict] = field(default_factory=list)

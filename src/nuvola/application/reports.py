from collections import OrderedDict
from typing import Iterable, List

from nuvola.domain.models import GradePeriod, HomeworkItem, LessonTopicEntry, Student, SubjectGrades

from .dates import format_display_date, format_display_datetime


def render_students(students: Iterable[Student]) -> str:
    lines = ["Studenti disponibili:"]
    for index, student in enumerate(students, start=1):
        lines.append(f"{index}: {student.label}")
    return "\n".join(lines)


def render_grade_periods(periods: Iterable[GradePeriod]) -> str:
    lines = ["Frazioni temporali disponibili:"]
    for index, period in enumerate(periods, start=1):
        lines.append(f"{index}: {period.name}")
    return "\n".join(lines)


def render_subject_grades(subjects: Iterable[SubjectGrades]) -> str:
    grade_list = list(subjects)
    if not grade_list:
        return "Nessun voto disponibile."

    lines: List[str] = []
    for subject in grade_list:
        lines.append(subject.subject)
        if subject.average:
            lines.append(f"  Media: {subject.average}")
        if not subject.entries:
            lines.append("  Nessun voto")
            lines.append("")
            continue

        for entry in subject.entries:
            lines.append(
                "  {date} | {value} | {kind} | docente: {teacher}".format(
                    date=format_display_datetime(entry.date),
                    value=entry.value,
                    kind=entry.kind or "-",
                    teacher=entry.teacher or "-",
                )
            )
            if entry.description:
                lines.append(f"    descrizione: {entry.description}")
            if entry.weight:
                lines.append(f"    peso: {entry.weight}")
            if entry.objective_name:
                lines.append(f"    obiettivoPrincipale: {entry.objective_name}")
            for objective in entry.objectives:
                line = f"    * {objective.name}: {objective.value}"
                if objective.description:
                    line += f" ({objective.description})"
                lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip()


def render_homework(items: Iterable[HomeworkItem]) -> str:
    homework_items = list(items)
    if not homework_items:
        return "Nessun compito trovato nel range selezionato."

    lines: List[str] = []
    for item in homework_items:
        lines.append(item.subject)
        lines.append(
            "  dataConsegna: {due} | dataAssegnazione: {assigned} | docente: {teacher}".format(
                due=format_display_datetime(item.due_date),
                assigned=format_display_datetime(item.assigned_date),
                teacher=item.teacher or "-",
            )
        )
        if item.topic_name:
            lines.append(f"  nomeArgomento: {item.topic_name}")
        lines.append(f"  compito: {item.description}")
        if item.extra_dates:
            extra = ", ".join(f"{key}: {value}" for key, value in sorted(item.extra_dates.items()))
            lines.append(f"  extraDate: {extra}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_lesson_topics(entries: Iterable[LessonTopicEntry]) -> str:
    topic_entries = sorted(
        list(entries),
        key=lambda item: (item.day, item.hour_number, item.subject, item.topic_name),
    )
    if not topic_entries:
        return "Nessun argomento trovato nel range selezionato."

    grouped = OrderedDict()
    for entry in topic_entries:
        grouped.setdefault(entry.day, []).append(entry)

    lines: List[str] = []
    for day, items in grouped.items():
        lines.append(format_display_date(day))
        for item in items:
            lines.append(
                "  {hour}a ora {start}-{end} | {subject}".format(
                    hour=item.hour_number,
                    start=item.starts_at or "--:--",
                    end=item.ends_at or "--:--",
                    subject=item.subject,
                )
            )
            lines.append(f"    docente: {item.teacher or '-'}")
            lines.append(f"    tipo: {item.lesson_type or '-'}")
            lines.append(f"    descrizione: {item.topic_name or '-'}")
            if item.extended_description:
                lines.append(f"    descrizioneEstesa: {item.extended_description}")
            if item.annotations:
                lines.append(f"    annotazioni: {item.annotations}")
            if item.cosignatures:
                cosignatures = ", ".join(
                    f"{cos.teacher} ({cos.role or 'senza ruolo'}, {'firmato' if cos.signed else 'non firmato'})"
                    for cos in item.cosignatures
                )
                lines.append(f"    cofirme: {cosignatures}")
        lines.append("")
    return "\n".join(lines).rstrip()

from collections import OrderedDict
from typing import Iterable, List

from nuvola.domain.models import (
    GradePeriod,
    HomeworkItem,
    LessonTopicEntry,
    NoticeboardDocument,
    NoticeboardItem,
    NoticeboardNotification,
    Student,
    SubjectGrades,
)

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


def render_noticeboards(boards: Iterable[NoticeboardItem]) -> str:
    board_list = list(boards)
    if not board_list:
        return "Nessuna bacheca disponibile."
    lines = ["Bacheche disponibili:"]
    for index, board in enumerate(board_list, start=1):
        lines.append(f"{index}: {board.name or board.id}")
    return "\n".join(lines)


def render_noticeboard_documents(documents: Iterable[NoticeboardDocument], start: int = 1) -> str:
    document_list = list(documents)
    if not document_list:
        return "Nessun documento in bacheca."

    lines: List[str] = []
    total = document_list[0].raw.get("_collection_count")
    if isinstance(total, int) and (start > 1 or total > len(document_list)):
        lines.append(f"Documenti {start}-{start + len(document_list) - 1} di {total}.")
    for index, document in enumerate(document_list, start=start):
        marker = "*" if document.is_read is False else " "
        lines.append(
            "{index:>3}{marker} {date} | {subject}".format(
                index=index,
                marker=marker,
                date=format_display_date(document.published_at),
                subject=document.subject or "-",
            )
        )
    if any(document.is_read is False for document in document_list):
        lines.append("(* = non letto)")
    return "\n".join(lines)


def render_noticeboard_document(document: NoticeboardDocument) -> str:
    lines = [document.subject or "-"]
    if document.cancelled:
        reason = f": {document.cancellation_reason}" if document.cancellation_reason else ""
        lines.append(f"  ANNULLATO{reason}")
    lines.append(f"  titolario: {document.category or '-'}")
    lines.append(
        "  protocollo: {number} del {date}".format(
            number=document.registry_number or "-",
            date=format_display_date(document.registry_date),
        )
    )
    lines.append(f"  pubblicato: {format_display_datetime(document.published_at)}")
    lines.append(f"  archiviazione: {format_display_date(document.archived_at)}")
    if document.responsible_office:
        lines.append(f"  ufficio: {document.responsible_office}")
    if document.responsible_user:
        lines.append(f"  responsabile: {document.responsible_user}")
    if document.requires_adhesion:
        lines.append(f"  adesione richiesta entro: {format_display_datetime(document.adhesion_deadline)}")
        if document.adhesion_text:
            lines.append(f"    {document.adhesion_text}")
    if document.link:
        lines.append(f"  link: {document.link_text or document.link} ({document.link})")
    if document.attachments:
        lines.append("  allegati:")
        for index, attachment in enumerate(document.attachments, start=1):
            lines.append(f"    {index}: {attachment.name or attachment.id}")
    else:
        lines.append("  nessun allegato")
    return "\n".join(lines)


def render_noticeboard_notifications(notifications: Iterable[NoticeboardNotification]) -> str:
    notification_list = list(notifications)
    if not notification_list:
        return "Nessuna notifica dalle bacheche."
    lines = ["Notifiche bacheche:"]
    for notification in notification_list:
        lines.append(
            "  {date} | {subject}".format(
                date=format_display_date(notification.created_at),
                subject=notification.subject or notification.text or "-",
            )
        )
    return "\n".join(lines)

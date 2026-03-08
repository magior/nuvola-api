import os
from getpass import getpass
from typing import Callable, List, Optional, Tuple

from nuvola.adapters.legacy_student_api import LegacyStudentApiAdapter
from nuvola.adapters.storage.file_session_store import FileSessionStore
from nuvola.adapters.tenant_api import TenantApiAdapter
from nuvola.application.dates import default_homework_range, default_lesson_topics_range, normalize_date_range, parse_user_date
from nuvola.application.reports import (
    render_grade_periods,
    render_homework,
    render_lesson_topics,
    render_students,
    render_subject_grades,
)
from nuvola.application.service import NuvolaService
from nuvola.domain.models import GradePeriod, SessionContext, Student

try:
    from colorama import Fore, Style, init
except ImportError:
    class _ColorFallback:
        BLACK = ""
        BLUE = ""
        CYAN = ""
        GREEN = ""
        MAGENTA = ""
        RED = ""
        WHITE = ""
        YELLOW = ""

    class _StyleFallback:
        BRIGHT = ""

    def init(*args, **kwargs):
        return None

    Fore = _ColorFallback()
    Style = _StyleFallback()

init(autoreset=True)

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]
PasswordFn = Callable[[str], str]


def build_service(default_backend: Optional[str] = None) -> NuvolaService:
    backend_name = default_backend or os.getenv("NUVOLA_BACKEND", "legacy_student")
    return NuvolaService(
        backends={
            "legacy_student": LegacyStudentApiAdapter(),
            "tenant": TenantApiAdapter(),
        },
        session_store=FileSessionStore(),
        default_backend=backend_name,
    )


def is_unauthorized(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    return response is not None and getattr(response, "status_code", None) in {401, 403}


def choose_student(
    students: List[Student],
    preferred_student_id: Optional[str] = None,
    force_prompt: bool = False,
    input_fn: InputFn = input,
    output: OutputFn = print,
) -> Student:
    if not students:
        raise ValueError("Nessun alunno disponibile.")

    if not force_prompt and preferred_student_id is not None:
        for student in students:
            if student.id == str(preferred_student_id):
                return student

    if len(students) == 1 and not force_prompt:
        return students[0]

    output(Fore.YELLOW + render_students(students))
    while True:
        choice = input_fn("Seleziona lo studente attivo: ").strip()
        try:
            index = int(choice)
        except ValueError:
            output(Fore.RED + "Inserisci un numero valido.")
            continue

        if 1 <= index <= len(students):
            return students[index - 1]
        output(Fore.RED + "Scelta non valida. Riprova.")


def choose_grade_period(periods: List[GradePeriod], input_fn: InputFn = input, output: OutputFn = print) -> GradePeriod:
    if not periods:
        raise ValueError("Nessuna frazione temporale disponibile.")
    output(Fore.YELLOW + render_grade_periods(periods))
    while True:
        choice = input_fn("Seleziona la frazione temporale: ").strip()
        try:
            index = int(choice)
        except ValueError:
            output(Fore.RED + "Inserisci un numero valido.")
            continue
        if 1 <= index <= len(periods):
            return periods[index - 1]
        output(Fore.RED + "Scelta non valida. Riprova.")


def prompt_topic_range(input_fn: InputFn = input, output: OutputFn = print) -> Tuple[object, object]:
    default_start, default_end = default_lesson_topics_range()
    output(
        Fore.YELLOW
        + f"Argomenti: premi invio per usare il default {default_start.strftime('%d-%m-%Y')} - "
        + default_end.strftime("%d-%m-%Y")
    )
    start_text = input_fn("Data inizio [default ultimi 7 giorni]: ").strip()
    end_text = input_fn("Data fine [vuoto = oggi]: ").strip()
    start_date = parse_user_date(start_text) if start_text else default_start
    end_date = parse_user_date(end_text) if end_text else default_end
    return normalize_date_range(start_date, end_date)


def prompt_homework_range(active_student: Student, input_fn: InputFn = input, output: OutputFn = print) -> Tuple[object, object]:
    default_start, default_end = default_homework_range(active_student)
    output(
        Fore.YELLOW
        + f"Compiti: premi invio per usare il default da {default_start.strftime('%d-%m-%Y')} "
        + f"fino a fine anno scolastico ({default_end.strftime('%d-%m-%Y')})"
    )
    start_text = input_fn("Data inizio [default oggi]: ").strip()
    end_text = input_fn("Data fine [vuoto = fine anno scolastico]: ").strip()
    start_date = parse_user_date(start_text) if start_text else default_start
    end_date = parse_user_date(end_text) if end_text else default_end
    return normalize_date_range(start_date, end_date)


def authenticate(
    service: NuvolaService,
    input_fn: InputFn = input,
    password_fn: PasswordFn = getpass,
    output: OutputFn = print,
) -> Tuple[SessionContext, List[Student], Student]:
    session = service.resume_session()
    if session and session.token:
        output(Fore.YELLOW + "Provo la sessione salvata...")
        try:
            students = service.list_students(session)
            active_student = choose_student(
                students,
                preferred_student_id=session.student_id,
                input_fn=input_fn,
                output=output,
            )
            session = service.select_student(session, active_student.id)
            output(Fore.YELLOW + "Studente attivo: " + active_student.label)
            return session, students, active_student
        except Exception as exc:
            if is_unauthorized(exc):
                output(Fore.RED + "La sessione salvata non e' piu' valida. Richiedo nuove credenziali.")
                service.clear_session()
            else:
                raise

    username = input_fn("Inserisci il nome utente: ")
    password = password_fn("Inserisci la tua password: ")
    backend = os.getenv("NUVOLA_BACKEND", service.default_backend)
    tenant = os.getenv("NUVOLA_TENANT")
    session = service.login(username, password, backend=backend, tenant=tenant)
    students = service.list_students(session)
    active_student = choose_student(students, input_fn=input_fn, output=output)
    session = service.select_student(session, active_student.id)
    output(Fore.YELLOW + "Studente attivo: " + active_student.label)
    return session, students, active_student


def run_menu(
    service: NuvolaService,
    session: SessionContext,
    students: List[Student],
    active_student: Student,
    input_fn: InputFn = input,
    output: OutputFn = print,
) -> None:
    while True:
        output(Fore.CYAN + "1 Voti")
        output(Fore.CYAN + "2 Compiti")
        output(Fore.CYAN + "3 Argomenti svolti")
        output(Fore.CYAN + "4 Cambia studente")
        output(Fore.CYAN + "0 Esci")
        choice = input_fn("Inserisci la tua scelta: ").strip()

        if choice == "1":
            periods = service.list_grade_periods(session, active_student.id)
            period = choose_grade_period(periods, input_fn=input_fn, output=output)
            grades = service.list_subject_grades(session, active_student.id, period.id)
            output(Fore.YELLOW + period.name)
            output(render_subject_grades(grades))
        elif choice == "2":
            start_date, end_date = prompt_homework_range(active_student, input_fn=input_fn, output=output)
            homework = service.list_homework(session, active_student.id, start_date, end_date)
            output(render_homework(homework))
        elif choice == "3":
            start_date, end_date = prompt_topic_range(input_fn=input_fn, output=output)
            topics = service.list_lesson_topics(session, active_student.id, start_date, end_date)
            output(render_lesson_topics(topics))
        elif choice == "4":
            active_student = choose_student(students, force_prompt=True, input_fn=input_fn, output=output)
            session = service.select_student(session, active_student.id)
            output(Fore.YELLOW + "Studente attivo: " + active_student.label)
        elif choice == "0":
            return
        else:
            output(Fore.RED + "Scelta non valida. Riprova.")


def main() -> None:
    service = build_service()
    try:
        session, students, active_student = authenticate(service)
        run_menu(service, session, students, active_student)
    except KeyboardInterrupt:
        print("\n" + Fore.YELLOW + "Uscita.")
    except Exception as exc:
        print(Fore.RED + f"Si e' verificato un errore: {exc}")
        raise SystemExit(1)

from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Tuple, Union

from nuvola.domain.models import Student

DateLike = Union[date, datetime]
USER_DATE_FORMATS = ("%d-%m-%Y", "%Y-%m-%d")


def today_local() -> date:
    return date.today()


def last_week_range(today: Optional[date] = None) -> Tuple[date, date]:
    end_date = today or today_local()
    start_date = end_date - timedelta(days=6)
    return start_date, end_date


def school_year_end_date(start_year: Union[str, int]) -> date:
    year = int(start_year)
    return date(year + 1, 8, 31)


def default_homework_range(student: Student, today: Optional[date] = None) -> Tuple[date, date]:
    start_date = today or today_local()
    end_date = start_date + timedelta(days=14)
    return start_date, end_date


def default_lesson_topics_range(today: Optional[date] = None) -> Tuple[date, date]:
    return last_week_range(today=today)


def parse_user_date(value: str) -> date:
    text = value.strip()
    if not text:
        raise ValueError("Data vuota.")
    for fmt in USER_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato data non valido. Usa DD-MM-YYYY oppure YYYY-MM-DD.")


def normalize_date_range(start_date: date, end_date: date) -> Tuple[date, date]:
    if start_date > end_date:
        raise ValueError("La data iniziale non puo' essere successiva alla data finale.")
    return start_date, end_date


def iter_dates(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def format_api_date(value: date) -> str:
    return value.strftime("%d-%m-%Y")


def parse_api_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def format_display_date(value: Optional[DateLike]) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y")
    return value.strftime("%d-%m-%Y")


def format_display_datetime(value: Optional[datetime]) -> str:
    if value is None:
        return "-"
    if value.hour == 0 and value.minute == 0 and value.second == 0:
        return value.strftime("%d-%m-%Y")
    return value.strftime("%d-%m-%Y %H:%M")

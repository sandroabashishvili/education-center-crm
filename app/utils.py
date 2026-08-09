import re
from datetime import date, datetime


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def parse_page(value: str | None, default: int = 1) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def parse_int(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(normalize_text(value)))


def is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(normalize_text(value))
    except ValueError:
        return False
    return True


def is_valid_datetime_range(starts_at: str, ends_at: str) -> bool:
    try:
        start = datetime.fromisoformat(normalize_text(starts_at))
        end = datetime.fromisoformat(normalize_text(ends_at))
    except ValueError:
        return False
    return end > start

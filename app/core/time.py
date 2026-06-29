from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


APP_TIMEZONE_NAME = "America/Mexico_City"
APP_TIMEZONE = ZoneInfo(APP_TIMEZONE_NAME)


def utc_now() -> datetime:
    """Hora actual UTC aware para metadatos tecnicos externos."""
    return datetime.now(timezone.utc)


def local_now() -> datetime:
    """Hora actual local aware de Kanpai POS."""
    return datetime.now(APP_TIMEZONE)


def local_now_naive() -> datetime:
    """Hora local naive para SQLite, que almacena DateTime sin tzinfo."""
    return local_now().replace(tzinfo=None)


def as_local_naive(value: datetime) -> datetime:
    """Convierte un datetime aware a local naive; si ya es naive, se asume local."""
    if value.tzinfo is None:
        return value
    return value.astimezone(APP_TIMEZONE).replace(tzinfo=None)


def local_day_bounds(value: date) -> tuple[datetime, datetime]:
    """Límites locales naive [inicio, siguiente_dia) para consultas por día."""
    start = datetime.combine(value, time.min)
    end = datetime.combine(value, time.max)
    return start, end

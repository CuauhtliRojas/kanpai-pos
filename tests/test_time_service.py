from __future__ import annotations

from datetime import datetime, timezone

from app.core.time import APP_TIMEZONE, APP_TIMEZONE_NAME, as_local_naive, local_now, local_now_naive


def test_app_timezone_is_mexico_city() -> None:
    assert APP_TIMEZONE_NAME == "America/Mexico_City"
    assert getattr(APP_TIMEZONE, "key", None) == "America/Mexico_City"


def test_local_now_is_aware_and_local_naive_has_no_tzinfo() -> None:
    aware = local_now()
    naive = local_now_naive()

    assert aware.tzinfo is not None
    assert naive.tzinfo is None
    assert aware.replace(tzinfo=None).date() == naive.date()


def test_as_local_naive_converts_aware_utc_to_mexico_city() -> None:
    value = datetime(2026, 6, 24, 18, 30, 0, tzinfo=timezone.utc)
    expected = value.astimezone(APP_TIMEZONE).replace(tzinfo=None)

    assert as_local_naive(value) == expected


def test_as_local_naive_keeps_naive_datetime_as_local() -> None:
    value = datetime(2026, 6, 24, 12, 30, 0)

    assert as_local_naive(value) == value

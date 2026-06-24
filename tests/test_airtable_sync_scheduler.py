from __future__ import annotations

import asyncio
import importlib
import threading
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.services.airtable_sync_scheduler as scheduler_module
from app.core.config import Settings
from app.db.seed import run_seed
from app.services.airtable_sync_scheduler import AirtableSyncScheduler
from tests.auth_helpers import auth_headers


def _settings(**overrides) -> Settings:
    values = {
        "AIRTABLE_SYNC_ENABLED": True,
        "AIRTABLE_API_TOKEN": "test-token",
        "AIRTABLE_BASE_ID": "app-test",
        "AIRTABLE_SYNC_PULL_ENABLED": True,
        "AIRTABLE_SYNC_PUSH_ENABLED": False,
        "AIRTABLE_SYNC_RUN_ON_STARTUP": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_scheduler_does_not_start_when_disabled() -> None:
    scheduler = AirtableSyncScheduler(
        _settings(AIRTABLE_SYNC_ENABLED=False)
    )

    assert asyncio.run(scheduler.start()) is False
    assert scheduler.task is None
    assert scheduler.status()["last_status"] == "disabled"


@pytest.mark.parametrize(
    ("token", "base_id"),
    [(None, "app-test"), ("test-token", None)],
)
def test_scheduler_does_not_start_without_credentials(
    token: str | None, base_id: str | None
) -> None:
    scheduler = AirtableSyncScheduler(
        _settings(AIRTABLE_API_TOKEN=token, AIRTABLE_BASE_ID=base_id)
    )

    assert asyncio.run(scheduler.start()) is False
    assert scheduler.task is None
    assert scheduler.status()["last_status"] == "missing_credentials"


def test_sync_interval_rejects_values_below_30_minutes() -> None:
    with pytest.raises(ValidationError):
        _settings(AIRTABLE_SYNC_INTERVAL_MINUTES=29)


def test_scheduler_prevents_overlapping_cycles(monkeypatch) -> None:
    scheduler = AirtableSyncScheduler(_settings())
    started = threading.Event()
    release = threading.Event()

    def slow_cycle() -> tuple[str, None]:
        started.set()
        release.wait(timeout=2)
        return "success", None

    monkeypatch.setattr(scheduler, "_run_sync_cycle", slow_cycle)

    async def scenario() -> None:
        first = asyncio.create_task(scheduler.run_cycle())
        assert await asyncio.to_thread(started.wait, 1)
        assert await scheduler.run_cycle() is False
        release.set()
        assert await first is True

    asyncio.run(scenario())
    assert scheduler.status()["last_status"] == "success"


def test_scheduler_starts_and_stops_without_leaving_a_task() -> None:
    scheduler = AirtableSyncScheduler(_settings())

    async def scenario() -> None:
        assert await scheduler.start() is True
        assert scheduler.task is not None
        await scheduler.stop()
        assert scheduler.task is None

    asyncio.run(scenario())


def test_cycle_skips_pull_during_active_operation_but_runs_push(monkeypatch) -> None:
    scheduler = AirtableSyncScheduler(_settings(AIRTABLE_SYNC_PUSH_ENABLED=True))
    calls = {"pull": 0, "push": 0}

    monkeypatch.setattr(scheduler_module, "has_active_operation", lambda session: True)
    monkeypatch.setattr(
        scheduler,
        "_execute_pull",
        lambda: calls.__setitem__("pull", calls["pull"] + 1) or [],
    )
    monkeypatch.setattr(
        scheduler,
        "_execute_push",
        lambda: calls.__setitem__("push", calls["push"] + 1) or [],
    )

    status, error = scheduler._run_sync_cycle()

    assert status == "success_pull_skipped_active_operation"
    assert error is None
    assert calls == {"pull": 0, "push": 1}


def test_airtable_scheduler_failure_does_not_break_fastapi_startup(monkeypatch) -> None:
    main_module = importlib.import_module("app.main")
    scheduler = main_module.get_airtable_sync_scheduler()
    monkeypatch.setattr(scheduler, "start", AsyncMock(side_effect=RuntimeError("boom")))

    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_airtable_sync_status_endpoint_is_read_only() -> None:
    main_module = importlib.import_module("app.main")
    run_seed(include_development_data=True)

    with TestClient(main_module.app) as client:
        response = client.get(
            "/api/v1/system/airtable-sync", headers=auth_headers(client)
        )

    assert response.status_code == 200
    assert set(response.json()) == {
        "enabled",
        "interval_minutes",
        "pull_enabled",
        "push_enabled",
        "running",
        "last_started_at",
        "last_finished_at",
        "last_status",
        "last_error",
    }


def test_airtable_sync_manual_endpoints_are_registered():
    from app.main import app

    paths = app.openapi()["paths"]

    assert "post" in paths["/api/v1/system/airtable-sync/pull"]
    assert "post" in paths["/api/v1/system/airtable-sync/push"]
    assert "post" in paths["/api/v1/system/airtable-sync/run"]


def test_airtable_sync_manual_endpoint_requires_confirmation():
    from fastapi.testclient import TestClient

    import app.services.airtable_sync_scheduler as scheduler_module
    from app.main import app

    scheduler_module._scheduler = None
    run_seed(include_development_data=True)
    client = TestClient(app)
    response = client.post(
        "/api/v1/system/airtable-sync/run",
        json={"dry_run": False, "confirm": "WRONG"},
        headers=auth_headers(client),
    )

    assert response.status_code in {400, 409}


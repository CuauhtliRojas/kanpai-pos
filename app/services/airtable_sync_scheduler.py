"""Periodic Airtable synchronization bound to the FastAPI process lifecycle."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, sessionmaker

from airtable.scripts.pull_airtable_to_sqlite import (
    AirtableRecordsClient,
    CONFIRM_TEXT as PULL_CONFIRM_TEXT,
    parse_args as parse_pull_args,
    run_pull,
)
from airtable.scripts.push_sqlite_to_airtable import (
    CONFIRM_TEXT as PUSH_CONFIRM_TEXT,
    parse_args as parse_push_args,
    run_push,
)
from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.domain.constants import CashShiftStatus, TicketStatus
from app.models import CashShift, Ticket

logger = logging.getLogger(__name__)

RUN_CONFIRM_TEXT = "RUN_AIRTABLE_SYNC_NOW"


@dataclass
class AirtableSyncState:
    running: bool = False
    last_started_at: str | None = None
    last_finished_at: str | None = None
    last_status: str = "not_started"
    last_error: str | None = None


def has_active_operation(session: Session) -> bool:
    """Return whether catalog changes could affect an operation in progress."""
    open_shift = session.scalar(
        select(exists().where(CashShift.status == CashShiftStatus.OPEN))
    )
    active_ticket = session.scalar(
        select(
            exists().where(
                Ticket.status.in_((TicketStatus.OPEN, TicketStatus.IN_PAYMENT))
            )
        )
    )
    return bool(open_shift or active_ticket)


class AirtableSyncScheduler:
    def __init__(
        self,
        settings: Settings,
        *,
        session_factory: sessionmaker[Session] = SessionLocal,
    ) -> None:
        self.settings = settings
        self._session_factory = session_factory
        self._cycle_lock = asyncio.Lock()
        self._state_lock = threading.Lock()
        self._state = AirtableSyncState()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> bool:
        if not self.settings.airtable_sync_enabled:
            self._set_state(last_status="disabled")
            return False
        if not self._credentials_available:
            logger.warning(
                "Airtable sync disabled at runtime: AIRTABLE_API_TOKEN or "
                "AIRTABLE_BASE_ID is missing."
            )
            self._set_state(last_status="missing_credentials")
            return False
        if not (
            self.settings.airtable_sync_pull_enabled
            or self.settings.airtable_sync_push_enabled
        ):
            logger.warning("Airtable sync has neither pull nor push enabled.")
            self._set_state(last_status="no_directions_enabled")
            return False
        if self._task is not None and not self._task.done():
            return True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="airtable-sync")
        logger.info(
            "Airtable sync started with a %s-minute interval.",
            self.settings.airtable_sync_interval_minutes,
        )
        return True

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await self._task
        finally:
            self._task = None

    async def run_cycle(self) -> bool:
        if self._cycle_lock.locked():
            logger.warning("Airtable sync cycle skipped because another cycle is running.")
            return False
        async with self._cycle_lock:
            self._set_state(
                running=True,
                last_started_at=_utc_now(),
                last_status="running",
                last_error=None,
            )
            try:
                status, error = await asyncio.to_thread(self._run_sync_cycle)
                self._set_state(last_status=status, last_error=error)
            except Exception as exc:  # Keep scheduler failures away from Uvicorn.
                logger.exception("Unexpected Airtable sync cycle failure.")
                self._set_state(last_status="error", last_error=str(exc))
            finally:
                self._set_state(running=False, last_finished_at=_utc_now())
            return True

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            state = asdict(self._state)
        return {
            "enabled": self.settings.airtable_sync_enabled,
            "interval_minutes": self.settings.airtable_sync_interval_minutes,
            "pull_enabled": self.settings.airtable_sync_pull_enabled,
            "push_enabled": self.settings.airtable_sync_push_enabled,
            **state,
        }

    @property
    def task(self) -> asyncio.Task[None] | None:
        return self._task

    @property
    def _credentials_available(self) -> bool:
        return bool(
            (self.settings.airtable_api_token or "").strip()
            and (self.settings.airtable_base_id or "").strip()
        )

    async def _run_loop(self) -> None:
        if self.settings.airtable_sync_run_on_startup:
            await self.run_cycle()
        interval_seconds = self.settings.airtable_sync_interval_minutes * 60
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=interval_seconds
                )
                continue
            except TimeoutError:
                pass
            await self.run_cycle()

    def _run_sync_cycle(self) -> tuple[str, str | None]:
        failures: list[str] = []
        pull_skipped = False
        if self.settings.airtable_sync_pull_enabled:
            with self._session_factory() as session:
                pull_skipped = (
                    self.settings.airtable_sync_skip_pull_during_active_shift
                    and has_active_operation(session)
                )
            if pull_skipped:
                logger.info("Airtable pull skipped because local operation is active.")
            else:
                failures.extend(self._execute_pull())
        if self.settings.airtable_sync_push_enabled:
            failures.extend(self._execute_push())

        if failures:
            message = "; ".join(failures)
            logger.error("Airtable sync cycle completed with errors: %s", message)
            return "error", message
        if pull_skipped:
            return "success_pull_skipped_active_operation", None
        return "success", None

    async def run_manual(
        self,
        *,
        pull: bool,
        push: bool,
        dry_run: bool = True,
        confirm: str | None = None,
        force_pull_during_active_shift: bool = False,
    ) -> dict[str, Any]:
        if not pull and not push:
            return {
                "accepted": False,
                "status": "no_directions_requested",
                "error": "No se solicito pull ni push.",
            }
        if not self._credentials_available:
            return {
                "accepted": False,
                "status": "missing_credentials",
                "error": "Falta AIRTABLE_API_TOKEN o AIRTABLE_BASE_ID.",
            }
        if self._cycle_lock.locked():
            return {
                "accepted": False,
                "status": "busy",
                "error": "Ya hay una sincronizacion Airtable en ejecucion.",
            }

        expected_confirm = self._manual_confirm_text(pull=pull, push=push)
        if not dry_run and confirm != expected_confirm:
            return {
                "accepted": False,
                "status": "confirmation_required",
                "error": f"Confirmacion requerida: {expected_confirm}",
                "expected_confirm": expected_confirm,
            }

        async with self._cycle_lock:
            self._set_state(
                running=True,
                last_started_at=_utc_now(),
                last_status="manual_running",
                last_error=None,
            )
            try:
                result = await asyncio.to_thread(
                    self._run_manual_sync,
                    pull,
                    push,
                    dry_run,
                    force_pull_during_active_shift,
                )
                self._set_state(
                    last_status=result["status"],
                    last_error=result.get("error"),
                )
                return result
            except Exception as exc:
                logger.exception("Unexpected manual Airtable sync failure.")
                error = str(exc)
                self._set_state(last_status="manual_error", last_error=error)
                return {
                    "accepted": False,
                    "status": "manual_error",
                    "error": error,
                }
            finally:
                self._set_state(running=False, last_finished_at=_utc_now())

    def _run_manual_sync(
        self,
        pull: bool,
        push: bool,
        dry_run: bool,
        force_pull_during_active_shift: bool,
    ) -> dict[str, Any]:
        mode = "dry-run" if dry_run else "execute"
        result: dict[str, Any] = {
            "accepted": True,
            "mode": mode,
            "pull_requested": pull,
            "push_requested": push,
            "pull": None,
            "push": None,
        }
        failures: list[str] = []

        if pull:
            with self._session_factory() as session:
                pull_skipped = (
                    self.settings.airtable_sync_skip_pull_during_active_shift
                    and not force_pull_during_active_shift
                    and has_active_operation(session)
                )
            if pull_skipped:
                result["pull"] = {
                    "status": "skipped_active_operation",
                    "errors": 0,
                    "warnings": 0,
                    "error_messages": [],
                    "warning_messages": [],
                }
            else:
                pull_result = self._run_pull(execute=not dry_run)
                result["pull"] = pull_result
                failures.extend(pull_result["error_messages"])

        if push:
            push_result = self._run_push(execute=not dry_run)
            result["push"] = push_result
            failures.extend(push_result["error_messages"])

        pull_result = result.get("pull") or {}

        if failures:
            result["status"] = "error"
            result["error"] = "; ".join(failures)
        elif pull_result.get("status") == "skipped_active_operation":
            result["status"] = "success_pull_skipped_active_operation"
            result["error"] = None
        else:
            result["status"] = "success"
            result["error"] = None
        return result

    @staticmethod
    def _manual_confirm_text(*, pull: bool, push: bool) -> str:
        if pull and push:
            return RUN_CONFIRM_TEXT
        if pull:
            return PULL_CONFIRM_TEXT
        return PUSH_CONFIRM_TEXT

    def _run_pull(self, *, execute: bool) -> dict[str, Any]:
        client = self._client()
        argv = [
            "--database-url",
            self.settings.database_url,
            "--product-image-media-dir",
            str(self.settings.resolved_product_image_media_dir),
        ]
        if execute:
            argv = ["--execute", "--confirm", PULL_CONFIRM_TEXT, *argv]
        args = parse_pull_args(argv)
        plan = run_pull(args, run_remote_preflight=False, client=client)
        return self._plan_result("pull", plan)

    def _run_push(self, *, execute: bool) -> dict[str, Any]:
        client = self._client()
        argv = ["--database-url", self.settings.database_url]
        if execute:
            argv = ["--execute", "--confirm", PUSH_CONFIRM_TEXT, *argv]
        args = parse_push_args(argv)
        plan = run_push(args, client=client)
        return self._plan_result("push", plan)

    @staticmethod
    def _plan_result(direction: str, plan: Any) -> dict[str, Any]:
        issues = list(getattr(plan, "issues", []))
        errors = [
            f"{direction}/{issue.code}: {issue.message}"
            for issue in issues
            if issue.level == "error"
        ]
        warnings = [
            f"{direction}/{issue.code}: {issue.message}"
            for issue in issues
            if issue.level == "warning"
        ]
        return {
            "status": "success" if not errors else "error",
            "errors": len(errors),
            "warnings": len(warnings),
            "error_messages": errors,
            "warning_messages": warnings,
        }

    def _execute_pull(self) -> list[str]:
        return self._run_pull(execute=True)["error_messages"]

    def _execute_push(self) -> list[str]:
        return self._run_push(execute=True)["error_messages"]

    def _client(self) -> AirtableRecordsClient:
        return AirtableRecordsClient(
            self.settings.airtable_base_id or "",
            self.settings.airtable_api_token or "",
        )

    def _set_state(self, **values: Any) -> None:
        with self._state_lock:
            for name, value in values.items():
                setattr(self._state, name, value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


_scheduler: AirtableSyncScheduler | None = None


def get_airtable_sync_scheduler() -> AirtableSyncScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AirtableSyncScheduler(get_settings())
    return _scheduler

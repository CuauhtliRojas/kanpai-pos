from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.main import app
from app.models import (
    CashShift,
    DiningTable,
    Employee,
    Payment,
    PaymentMethod,
    Printer,
    PrintJob,
    Ticket,
)
from scripts.reset_operational_data import reset_operational_data

client = TestClient(app)
sequence = count(1)


@pytest.fixture(autouse=True)
def clean_preflight_data() -> None:
    """Preserve seed catalogs and isolate every preflight invariant test."""
    run_seed()
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()


def _catalog(db: Session) -> tuple[Employee, DiningTable]:
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    table = db.scalar(select(DiningTable).where(DiningTable.active.is_(True)))
    assert employee is not None and table is not None
    return employee, table


def _shift(db: Session) -> CashShift:
    employee, _ = _catalog(db)
    shift = CashShift(
        folio=f"QA-PREFLIGHT-SHIFT-{next(sequence)}",
        status="OPEN",
        opened_by_employee_id=employee.id,
        opening_cash_cents=0,
    )
    db.add(shift)
    db.flush()
    return shift


def _ticket(db: Session, shift: CashShift, table: DiningTable, status: str) -> Ticket:
    employee, _ = _catalog(db)
    ticket = Ticket(
        folio=f"QA-PREFLIGHT-TICKET-{next(sequence)}",
        cash_shift_id=shift.id,
        table_id=table.id,
        opened_by_employee_id=employee.id,
        status=status,
        payment_status="UNPAID",
    )
    db.add(ticket)
    db.flush()
    return ticket


def _checks(payload: dict) -> dict[str, dict]:
    return {check["key"]: check for check in payload["checks"]}


def test_preflight_endpoint_returns_complete_structure() -> None:
    response = client.get("/api/v1/preflight/local-backend")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"status", "database", "checks", "summary"}
    assert payload["database"] == "sqlite"
    assert set(payload["summary"]) == {
        "active_cash_shifts",
        "open_tickets",
        "in_payment_tickets",
        "pending_print_jobs",
        "failed_print_jobs",
        "active_stock_alerts",
    }
    assert {"key", "status", "message"} == set(payload["checks"][0])


def test_preflight_is_ok_with_clean_seed() -> None:
    payload = client.get("/api/v1/preflight/local-backend").json()
    assert payload["status"] == "OK"
    assert all(check["status"] == "OK" for check in payload["checks"])


def test_preflight_detects_more_than_one_open_cash_shift() -> None:
    with SessionLocal() as db:
        _shift(db)
        _shift(db)
        db.commit()
    payload = client.get("/api/v1/preflight/local-backend").json()
    assert payload["status"] == "ERROR"
    assert _checks(payload)["single_open_cash_shift"]["status"] == "ERROR"


def test_preflight_detects_more_than_one_active_ticket_for_table() -> None:
    with SessionLocal() as db:
        _, table = _catalog(db)
        shift = _shift(db)
        _ticket(db, shift, table, "OPEN")
        _ticket(db, shift, table, "IN_PAYMENT")
        db.commit()
    payload = client.get("/api/v1/preflight/local-backend").json()
    assert _checks(payload)["single_active_ticket_per_table"]["status"] == "ERROR"


def test_preflight_detects_print_job_without_printer_key() -> None:
    with SessionLocal() as db:
        printer = db.scalar(select(Printer).where(Printer.printer_key == "CAJA"))
        assert printer is not None
        number = next(sequence)
        db.add(
            PrintJob(
                folio=f"QA-PREFLIGHT-PRINT-{number}",
                job_type="TICKET",
                printer_id=printer.id,
                printer_key_snapshot="",
                content_snapshot="QA",
                status="PENDING",
                idempotency_key=f"QA-PREFLIGHT-PRINT:{number}",
            )
        )
        db.commit()
    payload = client.get("/api/v1/preflight/local-backend").json()
    assert _checks(payload)["print_job_printer_snapshot"]["status"] == "ERROR"


def test_preflight_detects_active_payment_for_cancelled_ticket() -> None:
    with SessionLocal() as db:
        employee, table = _catalog(db)
        shift = _shift(db)
        ticket = _ticket(db, shift, table, "CANCELLED")
        method = db.scalar(
            select(PaymentMethod).where(PaymentMethod.method_key == "CASH")
        )
        assert method is not None
        db.add(
            Payment(
                folio=f"QA-PREFLIGHT-PAYMENT-{next(sequence)}",
                ticket_id=ticket.id,
                cash_shift_id=shift.id,
                payment_method_id=method.id,
                cashier_employee_id=employee.id,
                amount_cents=100,
                status="ACTIVE",
            )
        )
        db.commit()
    payload = client.get("/api/v1/preflight/local-backend").json()
    assert _checks(payload)["cancelled_ticket_payments"]["status"] == "ERROR"

from datetime import datetime, timedelta
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import DiscountType, TicketStatus
from app.main import app
from app.models import (
    AuditEvent,
    BusinessSetting,
    DiningTable,
    Employee,
    PrintJob,
    Product,
    StationOrder,
    TicketDiscount,
    TicketLineModification,
)
from app.services.cash_shift_service import open_cash_shift
from app.services.discount_service import apply_discount
from app.services.exceptions import (
    BusinessConflictError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.services.modification_service import modify_ticket_line
from app.services.order_service import send_round
from app.services.production_service import transition_station_order
from app.services.product_service import add_product_to_ticket
from app.services.reporting_service import get_print_jobs_summary, get_production_times
from app.services.reprint_service import request_reprint
from app.services.ticket_service import open_ticket_for_table, recalculate_ticket_totals
from scripts.reset_operational_data import reset_operational_data

sequence = count(1)


@pytest.fixture(autouse=True)
def clean_phase_3m_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.execute(delete(Employee).where(Employee.employee_code.like("QA-NOPERM-%")))
        setting = db.scalar(select(BusinessSetting))
        assert setting
        setting.tax_enabled = True
        setting.tax_rate_bps = 1600
        setting.tax_included = False
        setting.tax_label = "IVA"
        db.commit()
    yield
    with SessionLocal() as db:
        reset_operational_data(db)
        db.execute(delete(Employee).where(Employee.employee_code.like("QA-NOPERM-%")))
        db.commit()


def _context(db):
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    table = db.scalar(
        select(DiningTable)
        .where(DiningTable.active.is_(True))
        .order_by(DiningTable.id)
    )
    product = db.scalar(select(Product).where(Product.sku == "DEV-CHELA"))
    assert employee and table and product
    open_cash_shift(db, employee.id, 0)
    db.commit()
    ticket = open_ticket_for_table(db, table.id, employee.id)
    line = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)[0]
    db.commit()
    return employee, ticket, line


def _unprivileged_employee(db) -> Employee:
    number = next(sequence)
    employee = Employee(
        employee_code=f"QA-NOPERM-{number}",
        full_name="Sin permisos",
        active=True,
    )
    db.add(employee)
    db.flush()
    return employee


def test_production_lifecycle_and_audit() -> None:
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        send_round(db, ticket.id, employee.id)
        db.commit()
        order = db.scalar(select(StationOrder))
        assert order

        with pytest.raises(BusinessConflictError):
            transition_station_order(db, order.id, employee.id, "complete")
        assert transition_station_order(db, order.id, employee.id, "receive").status == "Recibida"
        assert transition_station_order(db, order.id, employee.id, "start").status == "En preparacion"
        assert transition_station_order(db, order.id, employee.id, "complete").status == "Terminada"
        delivered = transition_station_order(db, order.id, employee.id, "deliver")
        db.commit()

        assert delivered.status == "Entregada"
        assert delivered.received_at and delivered.started_at
        assert delivered.completed_at and delivered.delivered_at
        assert delivered.delivered_by_employee_id == employee.id
        assert db.scalar(select(func.count(AuditEvent.id))) >= 4


def test_production_times_calculates_prepare_interval() -> None:
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        send_round(db, ticket.id, employee.id)
        order = db.scalar(select(StationOrder))
        assert order
        transition_station_order(db, order.id, employee.id, "receive")
        transition_station_order(db, order.id, employee.id, "start")
        transition_station_order(db, order.id, employee.id, "complete")
        transition_station_order(db, order.id, employee.id, "deliver")
        order.started_at = datetime(2026, 1, 1, 10, 0, 0)
        order.completed_at = order.started_at + timedelta(seconds=90)
        db.commit()

        report = get_production_times(db)
        assert report[0]["orders_count"] == 1
        assert report[0]["average_prepare_seconds"] == 90


def test_captured_line_modification_updates_note_and_audits_without_print() -> None:
    with SessionLocal() as db:
        employee, _, line = _context(db)
        modification = modify_ticket_line(db, line.id, employee.id, "Sin cebolla")
        db.commit()

        assert line.note == "Sin cebolla"
        assert modification.print_job_id is None
        assert db.scalar(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type == "Modificacion de linea"
            )
        )


def test_sent_line_modification_creates_modification_print_job() -> None:
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        send_round(db, ticket.id, employee.id)
        db.commit()

        modification = modify_ticket_line(db, line.id, employee.id, "Sin cebolla")
        db.commit()
        job = db.get(PrintJob, modification.print_job_id)

        assert job and job.job_type == "Modificacion"
        assert "MODIFICACION" in job.content_snapshot
        assert "NOTA: Sin cebolla" in job.content_snapshot


@pytest.mark.parametrize("ticket_status", [TicketStatus.PAID, TicketStatus.CANCELLED])
def test_closed_ticket_line_cannot_be_modified(ticket_status: str) -> None:
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        ticket.status = ticket_status
        db.flush()
        with pytest.raises(BusinessConflictError):
            modify_ticket_line(db, line.id, employee.id, "Cambio")


@pytest.mark.parametrize(
    ("discount_type", "amount", "percent", "expected"),
    [
        (DiscountType.AMOUNT, 1000, None, 1000),
        (DiscountType.PERCENT, None, 1000, 700),
        (DiscountType.COURTESY, None, 10000, 7000),
    ],
)
def test_apply_discount_variants(
    discount_type: str, amount: int | None, percent: int | None, expected: int
) -> None:
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        discount = apply_discount(
            db,
            ticket.id,
            employee.id,
            discount_type,
            amount,
            percent,
            "Autorizado",
            discount_type == DiscountType.COURTESY,
        )
        db.commit()

        assert discount.amount_cents == expected
        assert ticket.discount_cents == expected
        assert ticket.tax_cents == round((7000 - expected) * 0.16)
        assert ticket.total_cents == 7000 - expected + ticket.tax_cents


def test_discount_requires_permission_and_cannot_exceed_subtotal() -> None:
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        no_permission = _unprivileged_employee(db)
        with pytest.raises(PermissionDeniedError):
            apply_discount(
                db, ticket.id, no_permission.id, DiscountType.AMOUNT, 100, None, "QA", False
            )
        with pytest.raises(InvalidBusinessDataError):
            apply_discount(
                db, ticket.id, employee.id, DiscountType.AMOUNT, 7001, None, "QA", False
            )


def test_tax_policy_disabled_and_included_do_not_inflate_total() -> None:
    with SessionLocal() as db:
        _, ticket, _ = _context(db)
        setting = db.scalar(select(BusinessSetting))
        assert setting and setting.tax_enabled and setting.tax_rate_bps == 1600
        assert ticket.tax_cents == 1120 and ticket.total_cents == 8120

        setting.tax_enabled = False
        recalculate_ticket_totals(db, ticket)
        assert ticket.tax_cents == 0 and ticket.total_cents == 7000

        setting.tax_enabled = True
        setting.tax_included = True
        recalculate_ticket_totals(db, ticket)
        assert ticket.total_cents == 7000
        assert ticket.tax_cents == round(7000 - 7000 / 1.16)


def test_reprint_requires_reason_permission_and_creates_audit() -> None:
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        send_round(db, ticket.id, employee.id)
        db.commit()
        original = db.scalar(select(PrintJob))
        assert original

        with pytest.raises(InvalidBusinessDataError):
            request_reprint(db, original.id, employee.id, " ")
        no_permission = _unprivileged_employee(db)
        with pytest.raises(PermissionDeniedError):
            request_reprint(db, original.id, no_permission.id, "Ilegible")

        reprint = request_reprint(db, original.id, employee.id, "Ticket ilegible")
        db.commit()
        assert reprint.id != original.id
        assert reprint.status == "Pendiente"
        assert reprint.content_snapshot == original.content_snapshot
        assert db.scalar(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type == "Reimpresion solicitada"
            )
        )
        assert get_print_jobs_summary(db)["reprint_count"] == 1


def test_ticket_audit_and_openapi_expose_phase_3m_operations() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/production/station-orders",
        "/api/v1/production/station-orders/{station_order_id}/receive",
        "/api/v1/production/station-orders/{station_order_id}/start",
        "/api/v1/production/station-orders/{station_order_id}/complete",
        "/api/v1/production/station-orders/{station_order_id}/deliver",
        "/api/v1/reports/production-times",
        "/api/v1/pos/ticket-lines/{line_id}/modify",
        "/api/v1/pos/tickets/{ticket_id}/discounts",
        "/api/v1/system/business-settings",
        "/api/v1/printing/jobs/{print_job_id}/reprint",
    }
    assert expected.issubset(paths)

    response = TestClient(app).get("/api/v1/system/business-settings")
    assert response.status_code == 200
    assert response.json()["tax_label"] == "IVA"


def test_operational_reset_deletes_phase_3m_transactions() -> None:
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        modify_ticket_line(db, line.id, employee.id, "Sin cebolla")
        apply_discount(
            db, ticket.id, employee.id, DiscountType.AMOUNT, 100, None, "QA", False
        )
        db.commit()
        assert db.scalar(select(func.count(TicketLineModification.id))) == 1
        assert db.scalar(select(func.count(TicketDiscount.id))) == 1

        reset_operational_data(db)
        db.commit()
        assert db.scalar(select(func.count(TicketLineModification.id))) == 0
        assert db.scalar(select(func.count(TicketDiscount.id))) == 0

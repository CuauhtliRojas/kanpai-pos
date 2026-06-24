from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import PrintJobType, PrintStatus
from app.main import app
from app.models import (
    AuditEvent,
    CashShift,
    DiningTable,
    Employee,
    Payment,
    PaymentMethod,
    PrintJob,
    Printer,
    Product,
    ProductVariantGroup,
    TableStatusEvent,
    Ticket,
    TicketLine,
)
from app.services.cash_shift_service import open_cash_shift
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table
from tests.auth_helpers import auth_headers


def _clean(db: Session) -> None:
    for model in (
        AuditEvent,
        TableStatusEvent,
        PrintJob,
        Payment,
        TicketLine,
        Ticket,
        CashShift,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


def setup_function() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean(db)


def teardown_function() -> None:
    with SessionLocal() as db:
        _clean(db)


def _context(db: Session) -> tuple[Employee, Ticket, DiningTable]:
    employee = db.scalar(select(Employee).where(Employee.active.is_(True)).order_by(Employee.id))
    table = db.scalar(select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id))
    assert employee and table
    open_cash_shift(db, employee.id, 0)
    db.commit()
    ticket = open_ticket_for_table(db, table.id, employee.id)
    db.commit()
    return employee, ticket, table


def _add_print_job(db: Session, ticket: Ticket) -> PrintJob:
    printer = db.scalar(select(Printer).order_by(Printer.id))
    assert printer
    job = PrintJob(
        folio=f"HIST-PRINT-{ticket.id}",
        job_type=PrintJobType.TICKET,
        printer_id=printer.id,
        printer_key_snapshot=printer.printer_key,
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        content_snapshot="snapshot que no debe aparecer en readonly",
        status=PrintStatus.PRINTED,
        attempts=1,
        idempotency_key=f"HIST:TICKET:{ticket.id}",
    )
    db.add(job)
    db.flush()
    return job


def test_history_defaults_to_open_shift_and_filters_table() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        _, ticket, table = _context(db)
        other_table = db.scalar(
            select(DiningTable)
            .where(DiningTable.active.is_(True), DiningTable.id != table.id)
            .order_by(DiningTable.id)
        )
        assert other_table
        other_ticket = Ticket(
            folio="TK-HISTORY-OTHER",
            cash_shift_id=ticket.cash_shift_id,
            table_id=other_table.id,
            opened_by_employee_id=ticket.opened_by_employee_id,
            guest_count=1,
        )
        db.add(other_ticket)
        db.commit()
        ticket_id = ticket.id
        table_id = table.id
        table_name = table.display_name

    response = client.get(
        f"/api/v1/pos/ticket-history?table_id={table_id}",
        headers=auth_headers(client),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == ticket_id
    assert body["items"][0]["table_name"] == table_name


def test_history_searches_partial_ticket_folio_and_has_small_payload() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        _, ticket, _ = _context(db)
        ticket.folio = "TK-BUSCABLE-908"
        _add_print_job(db, ticket)
        for index in range(20):
            db.add(
                AuditEvent(
                    event_type="QA",
                    entity_type="Ticket",
                    entity_id=ticket.id,
                    ticket_id=ticket.id,
                    cash_shift_id=ticket.cash_shift_id,
                    after_snapshot="x" * 500,
                )
            )
        db.commit()

    response = client.get(
        "/api/v1/pos/ticket-history?q=BUSCABLE", headers=auth_headers(client)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["folio"] == "TK-BUSCABLE-908"
    assert body["items"][0]["can_reprint_ticket"] is True
    assert "audit" not in response.text.lower()
    assert "content_snapshot" not in response.text


def test_readonly_detail_includes_lines_payments_and_print_jobs_without_snapshots() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket, table = _context(db)
        product_id = db.scalar(
            select(Product.id)
            .outerjoin(
                ProductVariantGroup,
                (ProductVariantGroup.product_id == Product.id)
                & (ProductVariantGroup.active.is_(True)),
            )
            .where(
                Product.active.is_(True),
                Product.visible_pos.is_(True),
                Product.price_cents > 0,
                ProductVariantGroup.id.is_(None),
            )
            .order_by(Product.id)
        )
        assert product_id
        add_product_to_ticket(db, ticket.id, product_id, employee.id, 1)
        method = db.scalar(select(PaymentMethod).where(PaymentMethod.active.is_(True)).order_by(PaymentMethod.id))
        assert method
        db.add(
            Payment(
                folio=f"PAY-HIST-{ticket.id}",
                ticket_id=ticket.id,
                cash_shift_id=ticket.cash_shift_id,
                payment_method_id=method.id,
                cashier_employee_id=employee.id,
                amount_cents=ticket.total_cents,
            )
        )
        print_job = _add_print_job(db, ticket)
        db.commit()
        ticket_id = ticket.id
        table_id = table.id
        method_name = method.name
        print_job_id = print_job.id

    response = client.get(
        f"/api/v1/pos/tickets/{ticket_id}/readonly", headers=auth_headers(client)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_readonly"] is True
    assert body["table"]["id"] == table_id
    assert len(body["lines"]) == 1
    assert len(body["payments"]) == 1
    assert body["payments"][0]["payment_method_name"] == method_name
    assert body["print_jobs"][0]["id"] == print_job_id
    assert body["can_reprint_ticket"] is True
    assert "content_snapshot" not in response.text
    assert "audit_events" not in response.text


def test_reprint_endpoint_still_requires_reason() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket, _ = _context(db)
        job = _add_print_job(db, ticket)
        db.commit()
        job_id = job.id
        employee_id = employee.id

    response = client.post(
        f"/api/v1/printing/jobs/{job_id}/reprint",
        json={"employee_id": employee_id, "reason": "   "},
        headers=auth_headers(client),
    )
    assert response.status_code == 400

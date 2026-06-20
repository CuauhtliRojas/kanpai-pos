from decimal import Decimal
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.main import app
from app.models import (
    AuditEvent,
    CashExpense,
    CashShift,
    CommandBatch,
    DiningTable,
    Employee,
    InventoryItem,
    InventoryMovement,
    Payment,
    PaymentMethod,
    PrintJob,
    Printer,
    Product,
    PurchaseReceipt,
    PurchaseReceiptLine,
    StationOrder,
    StationOrderLine,
    StockAlert,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
    TicketLineNote,
)

client = TestClient(app)
sequence = count(1)


def _clean_operational_data(db: Session) -> None:
    """Limpia datos auditables conservando catálogos seed."""
    for model in (
        PrintJob,
        StationOrderLine,
        StationOrder,
        CommandBatch,
        AuditEvent,
        TableStatusEvent,
        TicketLineNote,
        TicketLine,
        TicketDiscount,
        Payment,
        Ticket,
        CashExpense,
        CashShift,
        StockAlert,
        InventoryMovement,
        PurchaseReceiptLine,
        PurchaseReceipt,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_audit_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _context(db: Session):
    employee = db.scalar(select(Employee).order_by(Employee.id))
    table = db.scalar(select(DiningTable).order_by(DiningTable.id))
    product = db.scalar(select(Product).order_by(Product.id))
    assert employee and table and product
    number = next(sequence)
    shift = CashShift(
        folio=f"QA-A-SHIFT-{number}",
        opened_by_employee_id=employee.id,
        opening_cash_cents=1000,
    )
    db.add(shift)
    db.flush()
    ticket = Ticket(
        folio=f"QA-A-TICKET-{number}",
        cash_shift_id=shift.id,
        table_id=table.id,
        opened_by_employee_id=employee.id,
        status="Cobrado",
        payment_status="Cobrado",
        total_cents=500,
    )
    db.add(ticket)
    db.flush()
    line = TicketLine(
        ticket_id=ticket.id,
        product_id=product.id,
        quantity=1,
        unit_price_cents=500,
        line_total_cents=500,
        product_name_snapshot=product.display_name,
        product_sku_snapshot=product.sku,
        created_by_employee_id=employee.id,
    )
    db.add(line)
    db.flush()
    return employee, shift, ticket, line


def test_audit_events_lists_with_pagination_and_filter() -> None:
    with SessionLocal() as db:
        employee, shift, ticket, _ = _context(db)
        db.add_all(
            [
                AuditEvent(
                    event_type="Ticket abierto",
                    entity_type="Ticket",
                    entity_id=ticket.id,
                    actor_employee_id=employee.id,
                    ticket_id=ticket.id,
                    cash_shift_id=shift.id,
                    after_snapshot='{"status": "Abierto"}',
                ),
                AuditEvent(
                    event_type="Ticket cobrado",
                    entity_type="Ticket",
                    entity_id=ticket.id,
                    actor_employee_id=employee.id,
                    ticket_id=ticket.id,
                    cash_shift_id=shift.id,
                ),
            ]
        )
        db.commit()
    page = client.get("/api/v1/audit/events?limit=1&offset=0").json()
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["limit"] == 1
    filtered = client.get("/api/v1/audit/events?event_type=Ticket%20cobrado").json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["event_type"] == "Ticket cobrado"


def test_audit_ticket_returns_complete_cycle() -> None:
    with SessionLocal() as db:
        employee, shift, ticket, line = _context(db)
        method = db.scalar(
            select(PaymentMethod).where(PaymentMethod.method_key == "Efectivo")
        )
        printer = db.scalar(select(Printer).order_by(Printer.id))
        item = db.scalar(select(InventoryItem).order_by(InventoryItem.id))
        assert method and printer and item
        number = next(sequence)
        db.add_all(
            [
                Payment(
                    folio=f"QA-A-PAY-{number}",
                    ticket_id=ticket.id,
                    cash_shift_id=shift.id,
                    payment_method_id=method.id,
                    cashier_employee_id=employee.id,
                    amount_cents=500,
                ),
                PrintJob(
                    folio=f"QA-A-PRINT-{number}",
                    job_type="Ticket",
                    printer_id=printer.id,
                    printer_key_snapshot=printer.printer_key,
                    ticket_id=ticket.id,
                    content_snapshot="QA",
                    idempotency_key=f"QA-A:{number}",
                ),
                InventoryMovement(
                    folio=f"QA-A-MOV-{number}",
                    inventory_item_id=item.id,
                    movement_type="Consumo venta",
                    quantity_base=Decimal("1"),
                    signed_quantity_base=Decimal("-1"),
                    ticket_line_id=line.id,
                    registered_by_employee_id=employee.id,
                ),
            ]
        )
        db.commit()
        ticket_id = ticket.id
    payload = client.get(f"/api/v1/audit/tickets/{ticket_id}").json()
    assert payload["ticket"]["id"] == ticket_id
    assert len(payload["lines"]) == 1
    assert len(payload["payments"]) == 1
    assert len(payload["print_jobs"]) == 1
    assert len(payload["inventory_movements"]) == 1


def test_audit_cash_shift_returns_financial_context() -> None:
    with SessionLocal() as db:
        employee, shift, ticket, _ = _context(db)
        method = db.scalar(
            select(PaymentMethod).where(PaymentMethod.method_key == "Efectivo")
        )
        assert method
        number = next(sequence)
        db.add_all(
            [
                Payment(
                    folio=f"QA-A-PAY-{number}",
                    ticket_id=ticket.id,
                    cash_shift_id=shift.id,
                    payment_method_id=method.id,
                    cashier_employee_id=employee.id,
                    amount_cents=500,
                ),
                CashExpense(
                    folio=f"QA-A-EXP-{number}",
                    cash_shift_id=shift.id,
                    description="QA",
                    amount_cents=100,
                    registered_by_employee_id=employee.id,
                ),
            ]
        )
        db.commit()
        shift_id = shift.id
    payload = client.get(f"/api/v1/audit/cash-shifts/{shift_id}").json()
    assert payload["cash_shift"]["id"] == shift_id
    assert len(payload["tickets"]) == 1
    assert len(payload["payments"]) == 1
    assert len(payload["expenses"]) == 1
    assert payload["summary"]["total_paid_cents"] == 500


def test_audit_not_found_and_invalid_pagination_are_public_errors() -> None:
    assert client.get("/api/v1/audit/tickets/999999").status_code == 404
    assert client.get("/api/v1/audit/cash-shifts/999999").status_code == 404
    assert client.get("/api/v1/audit/events?limit=invalid").status_code == 400


def test_audit_routes_are_registered_in_openapi() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/audit/events" in paths
    assert "/api/v1/audit/tickets/{ticket_id}" in paths
    assert "/api/v1/audit/cash-shifts/{cash_shift_id}" in paths

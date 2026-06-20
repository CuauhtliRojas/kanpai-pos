from datetime import datetime
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
    """Limpia operaciones de reportes sin borrar catálogos seed."""
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
def clean_reporting_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _catalog(db: Session):
    employee = db.scalar(select(Employee).order_by(Employee.id))
    table = db.scalar(select(DiningTable).order_by(DiningTable.id))
    product = db.scalar(select(Product).order_by(Product.id))
    assert employee and table and product
    return employee, table, product


def _shift(db: Session, status: str = "Abierto") -> CashShift:
    employee, _, _ = _catalog(db)
    number = next(sequence)
    shift = CashShift(
        folio=f"QA-R-SHIFT-{number}",
        status=status,
        opened_by_employee_id=employee.id,
        opening_cash_cents=0,
    )
    db.add(shift)
    db.flush()
    return shift


def _ticket(db: Session, shift: CashShift, status: str, total: int = 1000) -> Ticket:
    employee, table, _ = _catalog(db)
    number = next(sequence)
    ticket = Ticket(
        folio=f"QA-R-TICKET-{number}",
        cash_shift_id=shift.id,
        table_id=table.id,
        opened_by_employee_id=employee.id,
        status=status,
        payment_status="Cobrado" if status == "Cobrado" else "Sin pagar",
        total_cents=total,
        paid_at=datetime.utcnow() if status == "Cobrado" else None,
    )
    db.add(ticket)
    db.flush()
    return ticket


def _line(
    db: Session,
    ticket: Ticket,
    *,
    line_type: str = "Simple",
    quantity: int = 1,
    total: int = 1000,
) -> TicketLine:
    employee, _, product = _catalog(db)
    line = TicketLine(
        ticket_id=ticket.id,
        product_id=product.id,
        line_type=line_type,
        quantity=quantity,
        unit_price_cents=total // quantity if quantity else 0,
        line_total_cents=total,
        product_name_snapshot=product.display_name,
        product_sku_snapshot=product.sku,
        created_by_employee_id=employee.id,
    )
    db.add(line)
    db.flush()
    return line


def _print_job(db: Session, status: str, job_type: str = "Ticket") -> PrintJob:
    printer = db.scalar(select(Printer).order_by(Printer.id))
    assert printer
    number = next(sequence)
    job = PrintJob(
        folio=f"QA-R-PRINT-{number}",
        job_type=job_type,
        printer_id=printer.id,
        printer_key_snapshot=printer.printer_key,
        content_snapshot="QA",
        status=status,
        idempotency_key=f"QA-R:{number}",
    )
    db.add(job)
    return job


def test_operational_summary_has_complete_structure() -> None:
    payload = client.get("/api/v1/reports/operational-summary").json()
    assert set(payload) == {
        "total_sales_cents",
        "total_paid_cents",
        "total_expenses_cents",
        "net_cash_cents",
        "paid_ticket_count",
        "cancelled_ticket_count",
        "open_ticket_count",
        "in_payment_ticket_count",
        "active_cash_shift_count",
        "pending_print_jobs_count",
        "failed_print_jobs_count",
        "low_stock_alert_count",
        "inventory_negative_item_count",
    }


def test_operational_summary_counts_paid_and_cancelled_tickets() -> None:
    with SessionLocal() as db:
        shift = _shift(db)
        _ticket(db, shift, "Cobrado", 2500)
        _ticket(db, shift, "Cancelado", 900)
        db.commit()
    payload = client.get("/api/v1/reports/operational-summary").json()
    assert payload["total_sales_cents"] == 2500
    assert payload["paid_ticket_count"] == 1
    assert payload["cancelled_ticket_count"] == 1


def test_operational_summary_counts_print_jobs_and_stock_alerts() -> None:
    with SessionLocal() as db:
        _print_job(db, "Pendiente")
        _print_job(db, "Fallido")
        item = db.scalar(select(InventoryItem).order_by(InventoryItem.id))
        assert item
        db.add(
            StockAlert(
                inventory_item_id=item.id,
                alert_type="Stock bajo",
                status="Abierta",
                message="QA",
            )
        )
        db.commit()
    payload = client.get("/api/v1/reports/operational-summary").json()
    assert payload["pending_print_jobs_count"] == 1
    assert payload["failed_print_jobs_count"] == 1
    assert payload["low_stock_alert_count"] == 1


def test_sales_by_payment_method_groups_active_methods() -> None:
    with SessionLocal() as db:
        shift = _shift(db)
        ticket = _ticket(db, shift, "Cobrado", 600)
        employee, _, _ = _catalog(db)
        methods = db.scalars(
            select(PaymentMethod).where(
                PaymentMethod.method_key.in_(("Efectivo", "Tarjeta", "Transferencia"))
            )
        ).all()
        for method in methods:
            number = next(sequence)
            db.add(
                Payment(
                    folio=f"QA-R-PAY-{number}",
                    ticket_id=ticket.id,
                    cash_shift_id=shift.id,
                    payment_method_id=method.id,
                    cashier_employee_id=employee.id,
                    amount_cents=200,
                    status="Activo",
                )
            )
        db.commit()
    payload = client.get("/api/v1/reports/sales-by-payment-method").json()
    assert {item["method_key"] for item in payload} == {
        "Efectivo",
        "Tarjeta",
        "Transferencia",
    }
    assert all(item["total_cents"] == 200 for item in payload)


def test_sales_by_product_sums_simple_and_ignores_package_components() -> None:
    with SessionLocal() as db:
        shift = _shift(db)
        ticket = _ticket(db, shift, "Cobrado", 3000)
        _line(db, ticket, quantity=2, total=2000)
        _line(db, ticket, line_type="Componente de paquete", total=1000)
        db.commit()
    payload = client.get("/api/v1/reports/sales-by-product").json()
    assert len(payload) == 1
    assert payload[0]["quantity_sold"] == 2
    assert payload[0]["total_cents"] == 2000


def test_inventory_consumption_defaults_to_sale_consumption() -> None:
    with SessionLocal() as db:
        employee, _, _ = _catalog(db)
        item = db.scalar(select(InventoryItem).order_by(InventoryItem.id))
        assert item
        number = next(sequence)
        db.add(
            InventoryMovement(
                folio=f"QA-R-MOV-{number}",
                inventory_item_id=item.id,
                movement_type="Consumo venta",
                quantity_base=Decimal("2.5"),
                signed_quantity_base=Decimal("-2.5"),
                registered_by_employee_id=employee.id,
            )
        )
        db.commit()
    payload = client.get("/api/v1/reports/inventory-consumption").json()
    assert payload[0]["movement_type"] == "Consumo venta"
    assert Decimal(payload[0]["total_quantity_base"]) == Decimal("2.5")


def test_print_jobs_summary_groups_by_status() -> None:
    with SessionLocal() as db:
        for status in ("Pendiente", "Tomado", "Impreso", "Fallido", "Cancelado"):
            _print_job(db, status)
        db.commit()
    payload = client.get("/api/v1/reports/print-jobs-summary").json()
    assert payload["total_print_jobs"] == 5
    assert payload["pending_count"] == payload["failed_count"] == 1
    assert sum(payload["by_printer"].values()) == 5


def test_report_routes_are_registered_in_openapi() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/reports/operational-summary" in paths
    assert "/api/v1/reports/print-jobs-summary" in paths

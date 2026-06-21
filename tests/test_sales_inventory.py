from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
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
    InventoryMovement,
    Payment,
    PaymentMethod,
    PrintJob,
    Product,
    ProductRecipe,
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
from app.services.cancellation_service import cancel_ticket, cancel_ticket_line
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import BusinessConflictError
from app.services.order_service import send_round
from app.services.payment_service import create_payment, start_payment
from app.services.product_service import add_product_to_ticket
from app.services.sales_inventory_service import consume_inventory_for_paid_ticket
from app.services.ticket_service import open_ticket_for_table


def _clean_operational_data(db: Session) -> None:
    """Limpia operaciones en orden de dependencias y conserva catálogos seed."""
    for model in (
        StockAlert,
        InventoryMovement,
        PurchaseReceiptLine,
        PurchaseReceipt,
        CashExpense,
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
        CashShift,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_sales_inventory_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _employee(db: Session) -> Employee:
    return db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))


def _product(db: Session, sku: str) -> Product:
    return db.scalar(select(Product).where(Product.sku == sku))


def _open_ticket(db: Session, sku: str = "DEV-CHELA", quantity: int = 1) -> Ticket:
    employee = _employee(db)
    table = db.scalar(
        select(DiningTable)
        .where(DiningTable.status_cache == "Libre")
        .order_by(DiningTable.id)
    )
    if db.scalar(select(func.count(CashShift.id))) == 0:
        open_cash_shift(db, employee.id, 0)
    ticket = open_ticket_for_table(db, table.id, employee.id)
    add_product_to_ticket(db, ticket.id, _product(db, sku).id, employee.id, quantity)
    return ticket


def _pay_ticket(db: Session, ticket: Ticket) -> None:
    employee = _employee(db)
    send_round(db, ticket.id, employee.id)
    start_payment(db, ticket.id, employee.id)
    cash_id = db.scalar(
        select(PaymentMethod.id).where(PaymentMethod.method_key == "Efectivo")
    )
    create_payment(db, ticket.id, employee.id, cash_id, ticket.total_cents)


def _sales_movements(db: Session, ticket_id: int) -> list[InventoryMovement]:
    line_ids = select(TicketLine.id).where(TicketLine.ticket_id == ticket_id)
    return list(
        db.scalars(
            select(InventoryMovement).where(
                InventoryMovement.movement_type == "Consumo venta",
                InventoryMovement.source_id.in_(line_ids),
            )
        )
    )


def test_seed_creates_demo_recipes_without_duplicates() -> None:
    run_seed(include_development_data=True)
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        recipes = db.scalars(
            select(ProductRecipe)
            .join(Product)
            .where(Product.sku.in_(("DEV-CHELA", "DEV-SAKE")))
        ).all()
        assert len(recipes) == 2
        assert sorted(recipe.quantity_base for recipe in recipes) == [100, 120]


def test_paid_simple_ticket_creates_negative_sale_consumption() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db, quantity=2)
        _pay_ticket(db, ticket)
        movement = _sales_movements(db, ticket.id)[0]
        assert movement.movement_type == "Consumo venta"
        assert movement.quantity_base == Decimal("200")
        assert movement.signed_quantity_base == Decimal("-200")
        assert movement.ticket_line_id == movement.source_id


def test_decimal_recipe_quantity_is_consumed_without_truncation() -> None:
    with SessionLocal() as db:
        product = _product(db, "DEV-CHELA")
        recipe = db.scalar(
            select(ProductRecipe).where(ProductRecipe.product_id == product.id)
        )
        recipe.quantity_base = Decimal("0.125000")
        recipe.waste_pct = Decimal("0.015000")
        ticket = _open_ticket(db, quantity=2)
        _pay_ticket(db, ticket)
        movement = _sales_movements(db, ticket.id)[0]
        assert movement.quantity_base == Decimal("0.253750")
        assert movement.signed_quantity_base == Decimal("-0.253750")


def test_product_recipe_multiplier_scales_piece_recipe_consumption() -> None:
    with SessionLocal() as db:
        product = _product(db, "DEV-CHELA")
        product.inventory_recipe_multiplier = Decimal("2")
        ticket = _open_ticket(db, quantity=1)
        _pay_ticket(db, ticket)
        movement = _sales_movements(db, ticket.id)[0]
        assert movement.quantity_base == Decimal("200")


def test_package_consumes_components_and_not_parent() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db, "DEV-CHELA-SAKE")
        _pay_ticket(db, ticket)
        movements = _sales_movements(db, ticket.id)
        source_types = db.scalars(
            select(TicketLine.line_type).where(
                TicketLine.id.in_([movement.source_id for movement in movements])
            )
        ).all()
        assert sorted(movement.quantity_base for movement in movements) == [100, 120]
        assert set(source_types) == {"Componente de paquete"}


def test_cancelled_line_does_not_consume() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        cancelled = ticket.lines[0]
        add_product_to_ticket(
            db, ticket.id, _product(db, "DEV-SAKE").id, _employee(db).id, 1
        )
        cancel_ticket_line(db, cancelled.id, _employee(db).id, "QA")
        _pay_ticket(db, ticket)
        movements = _sales_movements(db, ticket.id)
        assert len(movements) == 1
        assert movements[0].source_id != cancelled.id


def test_product_without_recipe_does_not_fail_sale() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        for recipe in db.scalars(
            select(ProductRecipe).where(
                ProductRecipe.product_id == _product(db, "DEV-CHELA").id
            )
        ):
            recipe.active = False
        _pay_ticket(db, ticket)
        assert ticket.status == "Cobrado"
        assert _sales_movements(db, ticket.id) == []


def test_partial_payment_does_not_consume_inventory() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        employee = _employee(db)
        send_round(db, ticket.id, employee.id)
        start_payment(db, ticket.id, employee.id)
        cash_id = db.scalar(
            select(PaymentMethod.id).where(PaymentMethod.method_key == "Efectivo")
        )
        create_payment(db, ticket.id, employee.id, cash_id, 100)
        assert ticket.status == "En cobro"
        assert ticket.inventory_consumed_at is None
        assert _sales_movements(db, ticket.id) == []


def test_consumption_is_idempotent_and_marks_ticket() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        _pay_ticket(db, ticket)
        original_count = len(_sales_movements(db, ticket.id))
        assert ticket.inventory_consumed_at is not None
        assert consume_inventory_for_paid_ticket(db, ticket.id, _employee(db).id) == []
        assert len(_sales_movements(db, ticket.id)) == original_count == 1


def test_sale_opens_low_stock_alert_and_allows_negative_stock() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        _pay_ticket(db, ticket)
        movement = _sales_movements(db, ticket.id)[0]
        stock = db.scalar(
            select(func.sum(InventoryMovement.signed_quantity_base)).where(
                InventoryMovement.inventory_item_id == movement.inventory_item_id
            )
        )
        alert = db.scalar(
            select(StockAlert).where(
                StockAlert.inventory_item_id == movement.inventory_item_id,
                StockAlert.status == "Abierta",
            )
        )
        assert stock == Decimal("-100")
        assert alert is not None
        assert alert.current_quantity == Decimal("-100")


def test_inventory_movements_endpoint_lists_ticket_consumption() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        _pay_ticket(db, ticket)
        ticket_id = ticket.id
        db.commit()
    response = TestClient(app).get(
        f"/api/v1/pos/tickets/{ticket_id}/inventory-movements"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["source_type"] == "Linea ticket"
    assert Decimal(response.json()[0]["signed_quantity_base"]) < 0


def test_paid_ticket_still_creates_ticket_print_job() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        _pay_ticket(db, ticket)
        job = db.scalar(
            select(PrintJob).where(
                PrintJob.ticket_id == ticket.id, PrintJob.job_type == "Ticket"
            )
        )
        assert job is not None


def test_cancelled_ticket_cannot_consume_inventory() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket(db)
        cancel_ticket(db, ticket.id, _employee(db).id, "QA")
        with pytest.raises(BusinessConflictError, match="tickets pagados"):
            consume_inventory_for_paid_ticket(db, ticket.id, _employee(db).id)
        assert ticket.inventory_consumed_at is None
        assert _sales_movements(db, ticket.id) == []

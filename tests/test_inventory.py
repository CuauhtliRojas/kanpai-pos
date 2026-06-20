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
    InventoryItem,
    InventoryMovement,
    Payment,
    PaymentMethod,
    PrintJob,
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
    Unit,
    UnitConversion,
)
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.services.inventory_service import (
    convert_quantity,
    create_inventory_movement,
    get_current_stock,
    process_purchase_receipt,
)


def _clean_operational_data(db: Session) -> None:
    """Limpia operaciones en orden de dependencias y conserva el seed."""
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
    db.execute(delete(Employee).where(Employee.employee_code == "QA-NO-PERM"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_inventory_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _admin(db: Session) -> Employee:
    return db.execute(
        select(Employee).where(Employee.employee_code == "EMP-0001")
    ).scalar_one()


def _item(db: Session, code: str = "INV-ARROZ") -> InventoryItem:
    return db.execute(
        select(InventoryItem).where(InventoryItem.item_code == code)
    ).scalar_one()


def _unit(db: Session, key: str) -> Unit:
    return db.execute(select(Unit).where(Unit.unit_key == key)).scalar_one()


def _receipt(db: Session, paid: int = 0) -> PurchaseReceipt:
    admin = _admin(db)
    item = _item(db)
    unit = _unit(db, "KG")
    payment_method_id = None
    if paid:
        open_cash_shift(db, admin.id, 10_000)
        payment_method_id = db.execute(
            select(PaymentMethod.id).where(PaymentMethod.method_key == "Efectivo")
        ).scalar_one()
    return process_purchase_receipt(
        db,
        employee_id=admin.id,
        supplier_name="Proveedor QA",
        invoice_reference="FAC-QA-001",
        paid_amount_cents=paid,
        payment_method_id=payment_method_id,
        note="Recepción QA",
        lines=[
            {
                "inventory_item_id": item.id,
                "quantity": 2,
                "unit_id": unit.id,
                "unit_cost_cents": 100,
            }
        ],
    )


def test_seed_creates_demo_inventory_items_without_duplicates() -> None:
    run_seed()
    run_seed()
    with SessionLocal() as db:
        count = db.scalar(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.item_code.in_(("INV-ARROZ", "INV-SAKE", "INV-LIMON"))
            )
        )
    assert count == 3


def test_seed_creates_unit_conversions_without_duplicates() -> None:
    run_seed()
    run_seed()
    with SessionLocal() as db:
        pairs = db.execute(
            select(UnitConversion.from_unit_id, UnitConversion.to_unit_id)
        ).all()
    assert len(pairs) == len(set(pairs))
    assert len(pairs) >= 6


def test_initial_stock_is_zero() -> None:
    with SessionLocal() as db:
        stock = get_current_stock(db, _item(db).id)
    assert stock["current_stock"] == 0
    assert stock["stock_status"] == "Sin stock"


def test_adjustment_in_increases_stock() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(
            db, item.id, "Ajuste entrada", Decimal("500"), admin.id, "QA"
        )
        assert get_current_stock(db, item.id)["current_stock"] == 500


def test_adjustment_out_decreases_stock() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(
            db, item.id, "Ajuste entrada", Decimal("800"), admin.id, "QA"
        )
        create_inventory_movement(
            db, item.id, "Ajuste salida", Decimal("300"), admin.id, "QA"
        )
        assert get_current_stock(db, item.id)["current_stock"] == 500


def test_movement_requires_permission() -> None:
    with SessionLocal() as db:
        employee = Employee(
            employee_code="QA-NO-PERM",
            full_name="Sin permiso",
            active=True,
            sync_status="Activo",
        )
        db.add(employee)
        db.flush()
        with pytest.raises(PermissionDeniedError, match="INVENTORY_ADJUST"):
            create_inventory_movement(
                db, _item(db).id, "Ajuste entrada", Decimal("1"), employee.id, "QA"
            )


def test_movement_rejects_zero_quantity() -> None:
    with SessionLocal() as db:
        with pytest.raises(InvalidBusinessDataError, match="mayor a cero"):
            create_inventory_movement(
                db, _item(db).id, "Ajuste entrada", Decimal("0"), _admin(db).id, "QA"
            )


def test_convert_kg_to_g() -> None:
    with SessionLocal() as db:
        result = convert_quantity(db, 2, _unit(db, "KG").id, _unit(db, "G").id)
    assert result == 2000


def test_convert_l_to_ml() -> None:
    with SessionLocal() as db:
        result = convert_quantity(db, 2, _unit(db, "L").id, _unit(db, "ML").id)
    assert result == 2000


def test_receipt_creates_purchase_receipt() -> None:
    with SessionLocal() as db:
        receipt = _receipt(db)
        assert receipt.status == "Procesada"
        assert db.get(PurchaseReceipt, receipt.id) is receipt


def test_receipt_creates_lines() -> None:
    with SessionLocal() as db:
        receipt = _receipt(db)
        lines = db.scalars(
            select(PurchaseReceiptLine).where(
                PurchaseReceiptLine.purchase_receipt_id == receipt.id
            )
        ).all()
        assert len(lines) == 1
        assert lines[0].converted_quantity_base == 2000


def test_receipt_creates_positive_movements() -> None:
    with SessionLocal() as db:
        receipt = _receipt(db)
        movement = db.execute(
            select(InventoryMovement)
            .join(PurchaseReceiptLine)
            .where(PurchaseReceiptLine.purchase_receipt_id == receipt.id)
        ).scalar_one()
        assert movement.movement_type == "Compra"
        assert movement.signed_quantity_base == 2000


def test_paid_receipt_creates_cash_expense() -> None:
    with SessionLocal() as db:
        receipt = _receipt(db, paid=25_000)
        expense = db.get(CashExpense, receipt.cash_expense_id)
        assert expense is not None
        assert expense.amount_cents == 25_000


def test_paid_receipt_without_open_shift_conflicts() -> None:
    with SessionLocal() as db:
        with pytest.raises(BusinessConflictError, match="corte de caja abierto"):
            process_purchase_receipt(
                db,
                employee_id=_admin(db).id,
                paid_amount_cents=25_000,
                payment_method_id=1,
                lines=[
                    {
                        "inventory_item_id": _item(db).id,
                        "quantity": 1,
                        "unit_id": _unit(db, "G").id,
                        "unit_cost_cents": 1,
                    }
                ],
            )


def test_low_stock_creates_active_alert() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(db, item.id, "Ajuste entrada", 500, admin.id, "QA")
        alert = db.scalar(select(StockAlert).where(StockAlert.status == "Abierta"))
        assert alert is not None
        assert alert.alert_type == "Stock bajo"


def test_low_stock_does_not_duplicate_active_alert() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(db, item.id, "Ajuste entrada", 300, admin.id, "QA")
        create_inventory_movement(db, item.id, "Ajuste entrada", 200, admin.id, "QA")
        count = db.scalar(
            select(func.count(StockAlert.id)).where(StockAlert.status == "Abierta")
        )
        assert count == 1


def test_recovered_stock_resolves_alert() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(db, item.id, "Ajuste entrada", 500, admin.id, "QA")
        create_inventory_movement(db, item.id, "Ajuste entrada", 600, admin.id, "QA")
        alert = db.scalar(
            select(StockAlert).where(StockAlert.inventory_item_id == item.id)
        )
        assert alert is not None
        assert alert.status == "Resuelta"
        assert alert.resolved_at is not None


def test_list_inventory_items_endpoint() -> None:
    response = TestClient(app).get("/api/v1/inventory/items")
    assert response.status_code == 200
    items = response.json()
    assert all(item["id"] for item in items)
    assert all(item["sku"] for item in items)
    rice = next(item for item in items if item["sku"] == "INV-ARROZ")
    assert rice["base_unit_id"]
    assert rice["base_unit_name"] == "G"
    assert rice["stock_minimum"] == 1000
    assert rice["stock_status"] == "Sin stock"


def test_get_inventory_item_stock_endpoint() -> None:
    with SessionLocal() as db:
        item_id = _item(db).id
    response = TestClient(app).get(f"/api/v1/inventory/items/{item_id}/stock")
    assert response.status_code == 200
    stock = response.json()
    assert stock["inventory_item_id"] == item_id
    assert stock["sku"] == "INV-ARROZ"
    assert stock["current_stock"] == 0
    assert stock["stock_minimum"] == 1000
    assert stock["stock_status"] == "Sin stock"


def test_create_inventory_movement_endpoint() -> None:
    with SessionLocal() as db:
        payload = {
            "employee_id": _admin(db).id,
            "inventory_item_id": _item(db).id,
            "movement_type": "Ajuste entrada",
            "quantity": 500,
            "unit_id": _unit(db, "G").id,
            "reason": "QA ajuste entrada",
            "unit_cost_cents": 10,
        }
    response = TestClient(app).post("/api/v1/inventory/movements", json=payload)
    assert response.status_code == 201
    assert Decimal(str(response.json()["signed_quantity_base"])) == 500


def test_process_purchase_receipt_endpoint() -> None:
    with SessionLocal() as db:
        payload = {
            "employee_id": _admin(db).id,
            "supplier_name": "Proveedor QA",
            "invoice_reference": "FAC-QA-001",
            "paid_amount_cents": 0,
            "note": "Recepción QA",
            "lines": [
                {
                    "inventory_item_id": _item(db).id,
                    "quantity": 2,
                    "unit_id": _unit(db, "KG").id,
                    "unit_cost_cents": 100,
                }
            ],
        }
    response = TestClient(app).post("/api/v1/inventory/purchase-receipts", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "Procesada"
    assert len(response.json()["lines"]) == 1


def test_list_active_stock_alerts_endpoint() -> None:
    with SessionLocal() as db:
        item, admin = _item(db), _admin(db)
        create_inventory_movement(db, item.id, "Ajuste entrada", 500, admin.id, "QA")
        db.commit()
    response = TestClient(app).get("/api/v1/inventory/stock-alerts/active")
    assert response.status_code == 200
    assert len(response.json()) == 1

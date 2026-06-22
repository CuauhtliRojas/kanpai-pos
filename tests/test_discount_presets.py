import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import DiscountType
from app.main import app
from app.models import DiningTable, DiscountPreset, Employee, Product
from app.services.cash_shift_service import open_cash_shift
from app.services.discount_service import apply_discount
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table
from scripts.reset_operational_data import reset_operational_data


@pytest.fixture(autouse=True)
def discount_data():
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield


def test_catalog_lists_only_active_visible_presets_in_order():
    with SessionLocal() as db:
        hidden = db.scalar(
            select(DiscountPreset).where(DiscountPreset.preset_key == "DESC_50_MXN")
        )
        hidden.visible_pos = False
        inactive = db.scalar(
            select(DiscountPreset).where(DiscountPreset.preset_key == "DESC_10")
        )
        inactive.active = False
        db.commit()

    response = TestClient(app).get("/api/v1/catalog/discount-presets")
    assert response.status_code == 200
    assert [item["preset_key"] for item in response.json()] == ["CORTESIA_TOTAL"]


@pytest.mark.parametrize(
    "values",
    [
        {"discount_type": DiscountType.AMOUNT, "amount_cents": 0, "percent_bps": None},
        {"discount_type": DiscountType.PERCENT, "amount_cents": None, "percent_bps": 10001},
        {"discount_type": DiscountType.COURTESY, "amount_cents": None, "percent_bps": 5000},
    ],
)
def test_database_rejects_invalid_preset_values(values):
    with SessionLocal() as db:
        db.add(
            DiscountPreset(
                preset_key=f"INVALID-{values['discount_type']}",
                name="Inválido",
                reason_template="QA",
                requires_authorization=True,
                visible_pos=True,
                sort_order=99,
                active=True,
                **values,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()


def test_preset_applies_through_existing_authorized_discount_contract():
    with SessionLocal() as db:
        employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
        table = db.scalar(
            select(DiningTable)
            .where(DiningTable.active.is_(True))
            .order_by(DiningTable.sort_order)
        )
        product = db.scalar(select(Product).where(Product.sku == "DEV-CHELA"))
        preset = db.scalar(
            select(DiscountPreset).where(DiscountPreset.preset_key == "DESC_10")
        )
        open_cash_shift(db, employee.id, 0)
        ticket = open_ticket_for_table(db, table.id, employee.id)
        add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)

        discount = apply_discount(
            db,
            ticket.id,
            employee.id,
            preset.discount_type,
            preset.amount_cents,
            preset.percent_bps,
            preset.reason_template,
            preset.discount_type == DiscountType.COURTESY,
        )

        assert discount.percent_bps == 1000
        assert discount.amount_cents == round(ticket.subtotal_cents * 0.10)
        assert discount.authorized_by_employee_id == employee.id

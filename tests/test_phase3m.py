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
    DiningTable,
    Employee,
    PrintJob,
    Product,
    ProductVariantGroup,
    ProductVariantOption,
    StationOrder,
    TicketDiscount,
    TicketLineModification,
    TicketLineVariantSelection,
)
from app.services.split_service import create_lines_split
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
from tests.auth_helpers import auth_headers

sequence = count(1)


@pytest.fixture(autouse=True)
def clean_phase_3m_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.execute(delete(Employee).where(Employee.employee_code.like("QA-NOPERM-%")))
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
        assert "NOTA:" in job.content_snapshot
        assert "Sin cebolla" in job.content_snapshot


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
        assert ticket.tax_cents == 0
        assert ticket.total_cents == max(7000 - expected, 0)


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


def test_net_price_total_is_subtotal_minus_discount() -> None:
    with SessionLocal() as db:
        _, ticket, _ = _context(db)
        assert ticket.tax_cents == 0
        assert ticket.total_cents == ticket.subtotal_cents - ticket.discount_cents
        recalculate_ticket_totals(db, ticket)
        assert ticket.tax_cents == 0
        assert ticket.total_cents == ticket.subtotal_cents - ticket.discount_cents


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
    data = response.json()
    assert "business_name" in data
    assert "tax_label" not in data


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


# --- V3 quantity tests ---

def test_modify_captured_line_quantity_recalculates_total() -> None:
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        original_unit = line.unit_price_cents
        assert line.quantity == 1

        modification = modify_ticket_line(db, line.id, employee.id, quantity=3)
        db.commit()

        assert line.quantity == 3
        assert line.line_total_cents == original_unit * 3
        assert ticket.subtotal_cents == original_unit * 3
        assert modification.print_job_id is None
        assert "3" in modification.note
        assert db.scalar(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type == "Modificacion de linea"
            )
        )


def test_modify_sent_line_quantity_is_rejected() -> None:
    from app.services.exceptions import BusinessConflictError as BCE
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        send_round(db, ticket.id, employee.id)
        db.commit()

        with pytest.raises(BCE, match="enviada"):
            modify_ticket_line(db, line.id, employee.id, quantity=2)


def test_modify_captured_line_note_does_not_print() -> None:
    with SessionLocal() as db:
        employee, _, line = _context(db)
        modification = modify_ticket_line(db, line.id, employee.id, note="Sin sal")
        db.commit()

        assert line.note == "Sin sal"
        assert modification.print_job_id is None


def test_modify_sent_line_note_creates_print_job_existing_behavior() -> None:
    with SessionLocal() as db:
        employee, ticket, line = _context(db)
        send_round(db, ticket.id, employee.id)
        db.commit()

        modification = modify_ticket_line(db, line.id, employee.id, note="Sin sal")
        db.commit()

        assert modification.print_job_id is not None
        job = db.get(PrintJob, modification.print_job_id)
        assert job is not None
        assert "MODIFICACION" in job.content_snapshot
        assert "Sin sal" in job.content_snapshot


# --- V3-05B variant tests ---


def test_yakitori_preparation_can_be_added_modified_and_sent() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee = db.scalar(
            select(Employee).where(Employee.employee_code == "EMP-0001")
        )
        table = db.scalar(
            select(DiningTable)
            .where(DiningTable.active.is_(True))
            .order_by(DiningTable.id)
        )
        product = db.scalar(
            select(Product).where(Product.sku == "YAK-COC-POLL")
        )
        assert employee and table and product
        group = db.scalar(
            select(ProductVariantGroup).where(
                ProductVariantGroup.product_id == product.id,
                ProductVariantGroup.name == "Preparación",
            )
        )
        assert group is not None
        options = {option.name: option for option in group.options}
        assert set(options) == {"Tempura", "Asada"}

        response = client.get(f"/api/v1/catalog/products/{product.id}/variant-groups")
        assert response.status_code == 200
        assert response.json()[0]["name"] == "Preparación"
        assert [item["name"] for item in response.json()[0]["options"]] == [
            "Tempura",
            "Asada",
        ]

        open_cash_shift(db, employee.id, 0)
        db.commit()
        ticket = open_ticket_for_table(db, table.id, employee.id)
        line = add_product_to_ticket(
            db,
            ticket.id,
            product.id,
            employee.id,
            1,
            variant_selections=[
                {
                    "variant_group_id": group.id,
                    "variant_option_id": options["Tempura"].id,
                    "quantity": 1,
                }
            ],
        )[0]
        assert line.variant_selections[0].name_snapshot == "Tempura"

        modification = modify_ticket_line(
            db,
            line.id,
            employee.id,
            variant_selections=[
                {
                    "variant_group_id": group.id,
                    "variant_option_id": options["Asada"].id,
                    "quantity": 1,
                }
            ],
        )
        assert modification.print_job_id is None
        db.flush()
        selections = list(
            db.scalars(
                select(TicketLineVariantSelection).where(
                    TicketLineVariantSelection.ticket_line_id == line.id
                )
            )
        )
        assert [selection.name_snapshot for selection in selections] == ["Asada"]

        batch = send_round(db, ticket.id, employee.id)
        job = db.scalar(
            select(PrintJob).where(PrintJob.command_batch_id == batch.id)
        )
        assert job is not None
        assert "Asada" in job.content_snapshot
        db.commit()
        ticket_id = ticket.id
        line_id = line.id

    headers = auth_headers(client)
    readonly = client.get(f"/api/v1/pos/tickets/{ticket_id}/readonly", headers=headers)
    assert readonly.status_code == 200
    readonly_line = next(
        item for item in readonly.json()["lines"] if item["id"] == line_id
    )
    assert [item["name_snapshot"] for item in readonly_line["variant_selections"]] == [
        "Asada"
    ]
    assert readonly_line["variant_selections"][0]["group_name"] == "Preparación"

    active_lines = client.get(f"/api/v1/pos/tickets/{ticket_id}/lines", headers=headers)
    assert active_lines.status_code == 200
    active_selection = active_lines.json()[0]["variant_selections"][0]
    assert active_selection["group_name"] == "Preparación"
    assert active_selection["name_snapshot"] == "Asada"


def test_yakitori_mix_exposes_brochetas_and_preparation_groups() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        product = db.scalar(select(Product).where(Product.sku == "YAK-COC-MIX"))
        assert product is not None
        product_id = product.id

    response = client.get(f"/api/v1/catalog/products/{product_id}/variant-groups")

    assert response.status_code == 200
    groups = {group["name"]: group for group in response.json()}
    assert set(groups) == {"BROCHETAS", "Preparación"}
    assert (groups["BROCHETAS"]["min_select"], groups["BROCHETAS"]["max_select"]) == (3, 3)
    assert (groups["Preparación"]["min_select"], groups["Preparación"]["max_select"]) == (1, 1)
    assert [option["name"] for option in groups["Preparación"]["options"]] == [
        "Tempura",
        "Asada",
    ]

def _clear_dev_chela_variants(db) -> None:
    """Remove any ProductVariantGroup rows added by previous tests for DEV-CHELA."""
    product = db.scalar(select(Product).where(Product.sku == "DEV-CHELA"))
    if product is None:
        return
    for group in list(db.scalars(
        select(ProductVariantGroup).where(ProductVariantGroup.product_id == product.id)
    )):
        db.delete(group)
    db.flush()


def _add_variant_group(db, product, *, min_select=0, max_select=1, required=False):
    group = ProductVariantGroup(
        product_id=product.id,
        name="Preparación",
        min_select=min_select,
        max_select=max_select,
        required=required,
        active=True,
    )
    db.add(group)
    db.flush()
    opt_normal = ProductVariantOption(
        variant_group_id=group.id, name="Normal", price_delta_cents=0, active=True
    )
    opt_spicy = ProductVariantOption(
        variant_group_id=group.id, name="Extra picante", price_delta_cents=500, active=True
    )
    db.add(opt_normal)
    db.add(opt_spicy)
    db.flush()
    return group, [opt_normal, opt_spicy]


def test_captured_line_quantity_can_change_without_note() -> None:
    with SessionLocal() as db:
        _clear_dev_chela_variants(db)
        employee, ticket, line = _context(db)
        original_unit = line.unit_price_cents
        modification = modify_ticket_line(db, line.id, employee.id, quantity=5)
        db.commit()
        assert line.quantity == 5
        assert line.line_total_cents == original_unit * 5
        assert "5" in modification.note
        assert modification.print_job_id is None


def test_captured_line_variant_selections_can_be_replaced() -> None:
    with SessionLocal() as db:
        _clear_dev_chela_variants(db)
        employee, ticket, line = _context(db)
        product = db.get(Product, line.product_id)
        group, options = _add_variant_group(db, product, min_select=0, max_select=1)

        modification = modify_ticket_line(
            db,
            line.id,
            employee.id,
            variant_selections=[{
                "variant_group_id": group.id,
                "variant_option_id": options[0].id,
                "quantity": 1,
            }],
        )
        db.commit()

        assert modification.print_job_id is None
        sels = list(
            db.scalars(
                select(TicketLineVariantSelection).where(
                    TicketLineVariantSelection.ticket_line_id == line.id
                )
            )
        )
        assert len(sels) == 1
        assert sels[0].variant_option_id == options[0].id


def test_variant_price_delta_recalculates_unit_price_and_ticket_total() -> None:
    with SessionLocal() as db:
        _clear_dev_chela_variants(db)
        employee, ticket, line = _context(db)
        product = db.get(Product, line.product_id)
        base_price = product.price_cents
        group, options = _add_variant_group(db, product)
        expensive = options[1]  # price_delta_cents=500

        modify_ticket_line(
            db,
            line.id,
            employee.id,
            variant_selections=[{
                "variant_group_id": group.id,
                "variant_option_id": expensive.id,
                "quantity": 1,
            }],
        )
        db.commit()

        assert line.unit_price_cents == base_price + 500
        assert line.line_total_cents == (base_price + 500) * line.quantity
        assert ticket.subtotal_cents == line.line_total_cents


def test_sent_line_variant_change_is_rejected() -> None:
    with SessionLocal() as db:
        _clear_dev_chela_variants(db)
        employee, ticket, line = _context(db)
        product = db.get(Product, line.product_id)
        group, options = _add_variant_group(db, product)
        send_round(db, ticket.id, employee.id)
        db.commit()

        with pytest.raises(BusinessConflictError, match="preparación"):
            modify_ticket_line(
                db,
                line.id,
                employee.id,
                variant_selections=[{
                    "variant_group_id": group.id,
                    "variant_option_id": options[0].id,
                    "quantity": 1,
                }],
            )


def test_line_in_active_split_cannot_change_variants() -> None:
    with SessionLocal() as db:
        _clear_dev_chela_variants(db)
        employee, ticket, line = _context(db)
        create_lines_split(db, ticket.id, employee.id, "Persona 1", [line.id])
        db.commit()

        with pytest.raises(BusinessConflictError, match="división"):
            modify_ticket_line(db, line.id, employee.id, variant_selections=[])

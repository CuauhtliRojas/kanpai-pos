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
    Payment,
    PrintJob,
    Product,
    StationOrder,
    StationOrderLine,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
    TicketLineNote,
)
from app.services.cash_shift_service import get_current_cash_shift, open_cash_shift
from app.services.exceptions import BusinessConflictError
from app.services.exceptions import InvalidBusinessDataError
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table


def _clean_operational_data(db: Session) -> None:
    """Limpia transacciones POS conservando catálogos y seeds base."""
    for model in (
        AuditEvent,
        TableStatusEvent,
        PrintJob,
        StationOrderLine,
        StationOrder,
        CommandBatch,
        TicketLineNote,
        TicketDiscount,
        Payment,
        TicketLine,
        Ticket,
        CashExpense,
        CashShift,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_pos_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _employee_and_table(db: Session) -> tuple[Employee, DiningTable]:
    employee = (
        db.execute(
            select(Employee).where(Employee.active.is_(True)).order_by(Employee.id)
        )
        .scalars()
        .first()
    )
    table = (
        db.execute(
            select(DiningTable)
            .where(DiningTable.active.is_(True))
            .order_by(DiningTable.id)
        )
        .scalars()
        .first()
    )
    assert employee is not None
    assert table is not None
    return employee, table


def _open_ticket(db: Session) -> tuple[Employee, Ticket]:
    """Crea el contexto operativo mínimo para pruebas de captura."""
    employee, table = _employee_and_table(db)
    open_cash_shift(db, employee.id, 0)
    db.commit()
    ticket = open_ticket_for_table(db, table.id, employee.id)
    db.commit()
    return employee, ticket


def test_open_cash_shift_successfully() -> None:
    with SessionLocal() as db:
        employee, _ = _employee_and_table(db)

        cash_shift = open_cash_shift(db, employee.id, 150_00)
        db.commit()

        assert cash_shift.status == "Abierto"
        assert cash_shift.folio.startswith("CC")
        assert cash_shift.opening_cash_cents == 150_00
        assert db.scalar(select(AuditEvent.event_type)) == "Corte abierto"


def test_cannot_open_two_cash_shifts() -> None:
    with SessionLocal() as db:
        employee, _ = _employee_and_table(db)
        open_cash_shift(db, employee.id, 0)
        db.commit()

        with pytest.raises(BusinessConflictError):
            open_cash_shift(db, employee.id, 0)


def test_get_current_cash_shift() -> None:
    with SessionLocal() as db:
        employee, _ = _employee_and_table(db)
        opened = open_cash_shift(db, employee.id, 500_00)
        db.commit()

        current = get_current_cash_shift(db)

        assert current is not None
        assert current.id == opened.id


def test_open_ticket_on_free_table() -> None:
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        cash_shift = open_cash_shift(db, employee.id, 0)
        db.commit()

        ticket = open_ticket_for_table(
            db,
            table_id=table.id,
            employee_id=employee.id,
            guest_count=3,
            note="Sin prisa",
        )
        db.commit()

        assert ticket.status == "Abierto"
        assert ticket.payment_status == "Sin pagar"
        assert ticket.cash_shift_id == cash_shift.id
        assert ticket.folio.startswith("TK")


def test_open_ticket_marks_table_as_occupied() -> None:
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        open_cash_shift(db, employee.id, 0)
        db.commit()

        open_ticket_for_table(db, table.id, employee.id)
        db.commit()

        assert table.status_cache == "Ocupada"
        assert db.scalar(select(TableStatusEvent.to_status)) == "Ocupada"


def test_cannot_open_second_active_ticket_on_same_table() -> None:
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        open_cash_shift(db, employee.id, 0)
        db.commit()
        open_ticket_for_table(db, table.id, employee.id)
        db.commit()

        # Simula un cache desincronizado para verificar también la consulta de tickets.
        table.status_cache = "Libre"
        db.commit()

        with pytest.raises(BusinessConflictError):
            open_ticket_for_table(db, table.id, employee.id)


def test_pos_endpoints_with_test_client() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        employee_id = employee.id
        table_id = table.id

    shift_response = client.post(
        "/api/v1/pos/cash-shifts/open",
        json={"employee_id": employee_id, "opening_cash_cents": 100_00},
    )
    assert shift_response.status_code == 201
    assert shift_response.json()["status"] == "Abierto"

    current_response = client.get("/api/v1/pos/cash-shifts/current")
    assert current_response.status_code == 200
    assert current_response.json()["id"] == shift_response.json()["id"]

    ticket_response = client.post(
        f"/api/v1/pos/tables/{table_id}/open-ticket",
        json={"employee_id": employee_id, "guest_count": 2},
    )
    assert ticket_response.status_code == 201
    assert ticket_response.json()["table_id"] == table_id

    ticket_id = ticket_response.json()["id"]
    get_response = client.get(f"/api/v1/pos/tickets/{ticket_id}")
    assert get_response.status_code == 200
    assert get_response.json()["folio"] == ticket_response.json()["folio"]

    conflict_response = client.post(
        "/api/v1/pos/cash-shifts/open",
        json={"employee_id": employee_id, "opening_cash_cents": 0},
    )
    assert conflict_response.status_code == 409


def test_add_simple_product_updates_ticket_and_captured_line() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA")
        ).scalar_one()

        lines = add_product_to_ticket(db, ticket.id, product.id, employee.id, 2, "Fría")
        db.commit()

        assert len(lines) == 1
        assert lines[0].line_type == "Simple"
        assert lines[0].status == "Capturado"
        assert lines[0].line_total_cents == product.price_cents * 2
        assert lines[0].station_id_snapshot is not None
        assert ticket.subtotal_cents == product.price_cents * 2
        assert ticket.total_cents == product.price_cents * 2
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Linea de ticket agregada"
                )
            )
            == "Linea de ticket agregada"
        )


def test_rejects_zero_quantity() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA")
        ).scalar_one()

        with pytest.raises(InvalidBusinessDataError):
            add_product_to_ticket(db, ticket.id, product.id, employee.id, 0)


@pytest.mark.parametrize("field", ["active", "visible_pos"])
def test_rejects_inactive_or_hidden_product(field: str) -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA")
        ).scalar_one()
        setattr(product, field, False)
        db.flush()

        with pytest.raises(InvalidBusinessDataError):
            add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)

        db.rollback()


def test_add_package_creates_parent_components_and_only_charges_parent() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        package_product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA-SAKE")
        ).scalar_one()

        lines = add_product_to_ticket(db, ticket.id, package_product.id, employee.id, 2)
        db.commit()

        parent = lines[0]
        components = lines[1:]
        assert parent.line_type == "Paquete padre"
        assert parent.status == "Capturado"
        assert len(components) == 2
        assert {line.line_type for line in components} == {"Componente de paquete"}
        assert all(line.parent_ticket_line_id == parent.id for line in components)
        assert all(line.line_total_cents == 0 for line in components)
        assert all(line.status == "Capturado" for line in components)
        assert ticket.subtotal_cents == package_product.price_cents * 2
        assert ticket.total_cents == package_product.price_cents * 2
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Paquete agregado"
                )
            )
            == "Paquete agregado"
        )


def test_rejects_product_when_ticket_is_not_open() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA")
        ).scalar_one()
        ticket.status = "En cobro"
        db.commit()

        with pytest.raises(BusinessConflictError):
            add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)


def test_ticket_line_endpoints_add_and_list_product() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-SAKE")
        ).scalar_one()
        employee_id = employee.id
        ticket_id = ticket.id
        product_id = product.id
        expected_total = product.price_cents * 2

    response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/lines",
        json={
            "product_id": product_id,
            "employee_id": employee_id,
            "quantity": 2,
            "note": "Tibio",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["ticket_id"] == ticket_id
    assert payload["lines_created"][0]["status"] == "Capturado"
    assert payload["ticket_totals"]["total_cents"] == expected_total

    list_response = client.get(f"/api/v1/pos/tickets/{ticket_id}/lines")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_ticket_line_endpoint_maps_business_errors() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = db.execute(
            select(Product).where(Product.sku == "DEV-CHELA")
        ).scalar_one()
        employee_id = employee.id
        ticket_id = ticket.id
        product_id = product.id

    invalid_quantity = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/lines",
        json={"product_id": product_id, "employee_id": employee_id, "quantity": 0},
    )
    missing_product = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/lines",
        json={"product_id": -1, "employee_id": employee_id, "quantity": 1},
    )

    assert invalid_quantity.status_code == 400
    assert missing_product.status_code == 404

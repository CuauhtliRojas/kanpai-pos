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
    db.execute(
        DiningTable.__table__.update().values(status_cache="FREE")
    )
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
    employee = db.execute(
        select(Employee).where(Employee.active.is_(True)).order_by(Employee.id)
    ).scalars().first()
    table = db.execute(
        select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id)
    ).scalars().first()
    assert employee is not None
    assert table is not None
    return employee, table


def test_open_cash_shift_successfully() -> None:
    with SessionLocal() as db:
        employee, _ = _employee_and_table(db)

        cash_shift = open_cash_shift(db, employee.id, 150_00)
        db.commit()

        assert cash_shift.status == "OPEN"
        assert cash_shift.folio.startswith("CC")
        assert cash_shift.opening_cash_cents == 150_00
        assert db.scalar(select(AuditEvent.event_type)) == "CASH_SHIFT_OPENED"


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

        assert ticket.status == "OPEN"
        assert ticket.payment_status == "UNPAID"
        assert ticket.cash_shift_id == cash_shift.id
        assert ticket.folio.startswith("TK")


def test_open_ticket_marks_table_as_occupied() -> None:
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        open_cash_shift(db, employee.id, 0)
        db.commit()

        open_ticket_for_table(db, table.id, employee.id)
        db.commit()

        assert table.status_cache == "OCCUPIED"
        assert db.scalar(select(TableStatusEvent.to_status)) == "OCCUPIED"


def test_cannot_open_second_active_ticket_on_same_table() -> None:
    with SessionLocal() as db:
        employee, table = _employee_and_table(db)
        open_cash_shift(db, employee.id, 0)
        db.commit()
        open_ticket_for_table(db, table.id, employee.id)
        db.commit()

        # Simula un cache desincronizado para verificar también la consulta de tickets.
        table.status_cache = "FREE"
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
    assert shift_response.json()["status"] == "OPEN"

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

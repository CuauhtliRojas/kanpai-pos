import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import TableStatus, TicketPaymentStatus, TicketStatus
from app.main import app
from app.models import DiningTable, Employee
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import BusinessConflictError
from app.services.ticket_service import open_ticket_for_table
from scripts.reset_operational_data import reset_operational_data


@pytest.fixture(autouse=True)
def table_data():
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield


def _context(db):
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    tables = list(
        db.scalars(
            select(DiningTable)
            .where(DiningTable.active.is_(True))
            .order_by(DiningTable.sort_order)
        )
    )
    open_cash_shift(db, employee.id, 0)
    db.flush()
    return employee, tables


def test_free_table_opens_ticket():
    with SessionLocal() as db:
        employee, tables = _context(db)
        ticket = open_ticket_for_table(db, tables[0].id, employee.id)
        assert ticket.status == TicketStatus.OPEN
        assert tables[0].status_cache == TableStatus.OCCUPIED


def test_table_with_open_ticket_is_exposed_for_continuation_even_with_stale_cache():
    with SessionLocal() as db:
        employee, tables = _context(db)
        ticket = open_ticket_for_table(db, tables[0].id, employee.id)
        tables[0].status_cache = TableStatus.FREE
        db.commit()
        ticket_id = ticket.id
        table_id = tables[0].id

    response = TestClient(app).get("/api/v1/operations/tables")
    table = next(item for item in response.json() if item["id"] == table_id)
    assert table["status"] == TableStatus.OCCUPIED
    assert table["active_ticket_id"] == ticket_id

    with SessionLocal() as db:
        employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
        with pytest.raises(BusinessConflictError, match="ticket activo"):
            open_ticket_for_table(db, table_id, employee.id)


@pytest.mark.parametrize(
    ("terminal_status", "payment_status"),
    [
        (TicketStatus.PAID, TicketPaymentStatus.PAID),
        (TicketStatus.CANCELLED, TicketPaymentStatus.CANCELLED),
    ],
)
def test_terminal_ticket_does_not_block_new_account(terminal_status, payment_status):
    with SessionLocal() as db:
        employee, tables = _context(db)
        previous = open_ticket_for_table(db, tables[0].id, employee.id)
        previous.status = terminal_status
        previous.payment_status = payment_status
        tables[0].status_cache = TableStatus.OCCUPIED
        db.flush()

        current = open_ticket_for_table(db, tables[0].id, employee.id)

        assert current.id != previous.id
        assert current.status == TicketStatus.OPEN
        assert tables[0].status_cache == TableStatus.OCCUPIED

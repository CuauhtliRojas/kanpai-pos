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
    EmployeeRole,
    Payment,
    PaymentMethod,
    PrintJob,
    StationOrder,
    StationOrderLine,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
    TicketLineNote,
)
from app.services.cash_shift_service import (
    close_cash_shift,
    get_cash_shift_summary,
    open_cash_shift,
)
from app.services.exceptions import (
    BusinessConflictError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.services.expense_service import create_cash_expense
from app.services.ticket_service import open_ticket_for_table
from tests.auth_helpers import auth_headers


def _clean_operational_data(db: Session) -> None:
    """Elimina operaciones de prueba sin tocar los catálogos seed."""
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
        CashExpense,
        Ticket,
        CashShift,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_cash_shift_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _employee(db: Session) -> Employee:
    employee = db.scalar(
        select(Employee).where(Employee.active.is_(True)).order_by(Employee.id)
    )
    assert employee is not None
    return employee


def _table(db: Session) -> DiningTable:
    table = db.scalar(
        select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id)
    )
    assert table is not None
    return table


def _method(db: Session, key: str = "Efectivo") -> PaymentMethod:
    return db.execute(
        select(PaymentMethod).where(PaymentMethod.method_key == key)
    ).scalar_one()


def _open_shift(
    db: Session, opening_cash_cents: int = 10_000
) -> tuple[Employee, CashShift]:
    employee = _employee(db)
    cash_shift = open_cash_shift(db, employee.id, opening_cash_cents)
    db.flush()
    return employee, cash_shift


def _ticket(db: Session, employee: Employee, status: str) -> Ticket:
    ticket = open_ticket_for_table(db, _table(db).id, employee.id)
    ticket.status = status
    if status == "Cobrado":
        ticket.payment_status = "Cobrado"
        ticket.total_cents = 8_000
    elif status == "Cancelado":
        ticket.payment_status = "Cancelado"
        ticket.table.status_cache = "Libre"
    db.flush()
    return ticket


def test_create_expense_with_open_shift() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        expense = create_cash_expense(
            db, employee.id, 2_500, "Compra servilletas", "INSUMO", note="QA"
        )
        db.commit()

        assert expense.cash_shift_id == cash_shift.id
        assert expense.folio.startswith("G")
        assert expense.status == "Activo"
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Gasto de caja creado"
                )
            )
            == "Gasto de caja creado"
        )


def test_cannot_create_expense_without_open_shift() -> None:
    with SessionLocal() as db:
        with pytest.raises(BusinessConflictError, match="corte"):
            create_cash_expense(db, _employee(db).id, 100, "Compra")


def test_cannot_create_zero_expense() -> None:
    with SessionLocal() as db:
        employee, _ = _open_shift(db)
        with pytest.raises(InvalidBusinessDataError, match="mayor a cero"):
            create_cash_expense(db, employee.id, 0, "Compra")


def test_cannot_create_expense_without_permission() -> None:
    with SessionLocal() as db:
        employee, _ = _open_shift(db)
        db.execute(delete(EmployeeRole).where(EmployeeRole.employee_id == employee.id))
        db.flush()

        with pytest.raises(PermissionDeniedError, match="EXPENSE_CREATE"):
            create_cash_expense(db, employee.id, 100, "Compra")


def _summary_context(db: Session) -> tuple[Employee, CashShift]:
    employee, cash_shift = _open_shift(db)
    ticket = _ticket(db, employee, "Cobrado")
    cash = _method(db)
    card = _method(db, "Tarjeta")
    db.add_all(
        [
            Payment(
                folio="PG-SUM-CASH",
                ticket_id=ticket.id,
                cash_shift_id=cash_shift.id,
                payment_method_id=cash.id,
                cashier_employee_id=employee.id,
                amount_cents=5_000,
                status="Activo",
            ),
            Payment(
                folio="PG-SUM-CARD",
                ticket_id=ticket.id,
                cash_shift_id=cash_shift.id,
                payment_method_id=card.id,
                cashier_employee_id=employee.id,
                amount_cents=3_000,
                status="Activo",
            ),
        ]
    )
    create_cash_expense(db, employee.id, 2_000, "Servilletas")
    db.flush()
    return employee, cash_shift


def test_summary_includes_opening_sales_payments_and_expenses() -> None:
    with SessionLocal() as db:
        _, cash_shift = _summary_context(db)
        summary = get_cash_shift_summary(db, cash_shift.id)

        assert summary["opening_cash_cents"] == 10_000
        assert summary["total_sales_cents"] == 8_000
        assert summary["total_paid_cents"] == 8_000
        assert summary["total_cash_cents"] == 5_000
        assert summary["total_card_cents"] == 3_000
        assert summary["total_expenses_cents"] == 2_000
        assert summary["paid_ticket_count"] == 1


def test_summary_calculates_expected_cash() -> None:
    with SessionLocal() as db:
        _, cash_shift = _summary_context(db)

        assert (
            get_cash_shift_summary(db, cash_shift.id)["expected_cash_cents"] == 13_000
        )


@pytest.mark.parametrize("ticket_status", ["Abierto", "En cobro"])
def test_cannot_close_with_active_ticket(ticket_status: str) -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        _ticket(db, employee, ticket_status)

        with pytest.raises(BusinessConflictError, match="cuentas pendientes"):
            close_cash_shift(db, cash_shift.id, employee.id, 10_000)


def test_close_with_paid_tickets() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        _ticket(db, employee, "Cobrado")

        closed = close_cash_shift(db, cash_shift.id, employee.id, 10_000)

        assert closed.status == "Cerrado"


def test_close_with_cancelled_tickets() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        _ticket(db, employee, "Cancelado")

        assert (
            close_cash_shift(db, cash_shift.id, employee.id, 10_000).status == "Cerrado"
        )


def test_close_calculates_cash_difference() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _summary_context(db)
        closed = close_cash_shift(db, cash_shift.id, employee.id, 12_500)

        assert closed.expected_cash_cents == 13_000
        assert closed.cash_difference_cents == -500


def test_close_creates_cash_shift_print_job() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        close_cash_shift(db, cash_shift.id, employee.id, 10_000)

        job = db.execute(
            select(PrintJob).where(PrintJob.job_type == "Corte")
        ).scalar_one()
        assert job.printer_key_snapshot == "CAJA"
        assert job.status == "Pendiente"
        assert job.idempotency_key == f"CORTE:{cash_shift.id}"
        assert "SOMOS KANPAI" in job.content_snapshot
        assert "CORTE" in job.content_snapshot
        job.content_snapshot.encode("ascii")


def test_close_persists_closed_status() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        cash_shift_id = cash_shift.id
        close_cash_shift(db, cash_shift_id, employee.id, 10_000, "Cierre QA")
        db.commit()

        persisted = db.get(CashShift, cash_shift_id)
        assert persisted is not None
        assert persisted.status == "Cerrado"
        assert persisted.closed_at is not None
        assert persisted.closing_note == "Cierre QA"


def test_cannot_close_twice() -> None:
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        close_cash_shift(db, cash_shift.id, employee.id, 10_000)
        db.flush()

        with pytest.raises(BusinessConflictError, match="no está abierto"):
            close_cash_shift(db, cash_shift.id, employee.id, 10_000)


def test_create_expense_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, _ = _open_shift(db)
        method = _method(db)
        db.commit()
        employee_id, method_id = employee.id, method.id

    response = client.post(
        "/api/v1/pos/cash-expenses",
        json={
            "employee_id": employee_id,
            "amount_cents": 2_500,
            "description": "Compra servilletas",
            "category": "INSUMO",
            "payment_method_id": method_id,
            "note": "QA gasto",
        },
        headers=auth_headers(client),
    )

    assert response.status_code == 201
    assert response.json()["amount_cents"] == 2_500


def test_cash_shift_summary_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db, 7_000)
        create_cash_expense(db, employee.id, 1_000, "Compra")
        db.commit()
        cash_shift_id = cash_shift.id

    response = client.get(
        f"/api/v1/pos/cash-shifts/{cash_shift_id}/summary",
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["expected_cash_cents"] == 6_000


def test_close_cash_shift_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, cash_shift = _open_shift(db)
        db.commit()
        employee_id, cash_shift_id = employee.id, cash_shift.id

    response = client.post(
        f"/api/v1/pos/cash-shifts/{cash_shift_id}/close",
        json={
            "employee_id": employee_id,
            "declared_cash_cents": 9_500,
            "note": "Cierre QA",
            "allow_pending_print_jobs": True,
        },
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["closed"] is True
    assert payload["cash_shift"]["status"] == "Cerrado"
    assert payload["print_job"]["job_type"] == "Corte"

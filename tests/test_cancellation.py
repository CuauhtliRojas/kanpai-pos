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
    EmployeeRole,
    Payment,
    PaymentMethod,
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
from app.services.cancellation_service import cancel_ticket, cancel_ticket_line
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import BusinessConflictError, PermissionDeniedError
from app.services.order_service import send_round
from app.services.payment_service import create_payment, start_payment
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table


def _clean_operational_data(db: Session) -> None:
    """Limpia datos POS de pruebas sin borrar catálogos seed."""
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
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="FREE"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_cancellation_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _context(db: Session) -> tuple[Employee, Ticket]:
    employee = db.scalar(
        select(Employee).where(Employee.active.is_(True)).order_by(Employee.id)
    )
    table = db.scalar(
        select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id)
    )
    assert employee is not None
    assert table is not None
    open_cash_shift(db, employee.id, 0)
    ticket = open_ticket_for_table(db, table.id, employee.id)
    db.commit()
    return employee, ticket


def _product(db: Session, sku: str = "DEV-CHELA") -> Product:
    return db.execute(select(Product).where(Product.sku == sku)).scalar_one()


def _add_line(db: Session, ticket: Ticket, employee: Employee) -> TicketLine:
    line = add_product_to_ticket(
        db, ticket.id, _product(db).id, employee.id, quantity=1
    )[0]
    db.commit()
    return line


def _pay_ticket(db: Session, ticket: Ticket, employee: Employee) -> None:
    send_round(db, ticket.id, employee.id)
    start_payment(db, ticket.id, employee.id)
    cash = db.execute(
        select(PaymentMethod).where(PaymentMethod.method_key == "CASH")
    ).scalar_one()
    create_payment(db, ticket.id, employee.id, cash.id, ticket.total_cents)
    db.commit()


def test_cancel_captured_line() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)

        result = cancel_ticket_line(db, line.id, employee.id, "Error de captura")
        db.commit()

        assert result.status == "CANCELLED"
        assert result.cancelled_by_employee_id == employee.id
        assert result.cancel_reason == "Error de captura"
        assert result.cancelled_at is not None
        assert db.scalar(select(func.count(PrintJob.id))) == 0
        assert db.scalar(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type == "TICKET_LINE_CANCELLED"
            )
        ) == "TICKET_LINE_CANCELLED"


def test_cancel_captured_line_recalculates_totals() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        first = _add_line(db, ticket, employee)
        second = _add_line(db, ticket, employee)
        original_total = ticket.total_cents

        cancel_ticket_line(db, first.id, employee.id)

        assert ticket.subtotal_cents == second.line_total_cents
        assert ticket.total_cents == original_total - first.line_total_cents


def test_cancel_sent_line_creates_cancellation_print_job() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        send_round(db, ticket.id, employee.id)
        db.commit()

        cancel_ticket_line(db, line.id, employee.id, "Producto incorrecto")
        db.commit()

        job = db.execute(
            select(PrintJob).where(PrintJob.job_type == "CANCELACION_COMANDA")
        ).scalar_one()
        assert job.idempotency_key == f"CANCEL_LINE:{line.id}"
        assert job.station_order_id is not None
        assert "KANPAI\nCANCELACION COMANDA" in job.content_snapshot
        job.content_snapshot.encode("ascii")


def test_cancel_sent_line_changes_status() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        send_round(db, ticket.id, employee.id)

        cancel_ticket_line(db, line.id, employee.id)

        assert line.status == "CANCELLED"


def test_cannot_cancel_line_from_paid_ticket() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        _pay_ticket(db, ticket, employee)

        with pytest.raises(BusinessConflictError, match="pagado"):
            cancel_ticket_line(db, line.id, employee.id)


def test_cannot_cancel_line_twice() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        cancel_ticket_line(db, line.id, employee.id)
        db.flush()

        with pytest.raises(BusinessConflictError, match="ya está cancelada"):
            cancel_ticket_line(db, line.id, employee.id)


def test_cannot_cancel_active_package_component_directly() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        lines = add_product_to_ticket(
            db, ticket.id, _product(db, "DEV-CHELA-SAKE").id, employee.id, 1
        )
        db.commit()

        with pytest.raises(BusinessConflictError, match="paquete padre"):
            cancel_ticket_line(db, lines[1].id, employee.id)


def test_cancel_package_parent_cancels_components() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        lines = add_product_to_ticket(
            db, ticket.id, _product(db, "DEV-CHELA-SAKE").id, employee.id, 1
        )
        send_round(db, ticket.id, employee.id)
        db.commit()

        cancel_ticket_line(db, lines[0].id, employee.id)
        db.commit()

        assert all(line.status == "CANCELLED" for line in lines)
        assert ticket.total_cents == 0
        assert db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.job_type == "CANCELACION_COMANDA"
            )
        ) == 2


def test_cancel_open_ticket() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        historical_total = ticket.total_cents

        result = cancel_ticket(db, ticket.id, employee.id, "Cliente canceló")
        db.commit()

        assert result.status == "CANCELLED"
        assert result.payment_status == "CANCELLED"
        assert result.cancelled_at is not None
        assert line.status == "CANCELLED"
        assert result.total_cents == historical_total
        assert db.scalar(
            select(AuditEvent.event_type).where(
                AuditEvent.event_type == "TICKET_CANCELLED"
            )
        ) == "TICKET_CANCELLED"


def test_cancel_ticket_with_sent_lines_creates_jobs() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        first = _add_line(db, ticket, employee)
        second = _add_line(db, ticket, employee)
        send_round(db, ticket.id, employee.id)
        db.commit()

        cancel_ticket(db, ticket.id, employee.id)
        db.commit()

        jobs = list(
            db.execute(
                select(PrintJob).where(
                    PrintJob.job_type == "CANCELACION_COMANDA"
                )
            ).scalars()
        )
        assert {job.idempotency_key for job in jobs} == {
            f"CANCEL_TICKET:{ticket.id}:LINE:{first.id}",
            f"CANCEL_TICKET:{ticket.id}:LINE:{second.id}",
        }


def test_cancel_ticket_releases_table() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        _add_line(db, ticket, employee)

        cancel_ticket(db, ticket.id, employee.id)
        db.commit()

        assert ticket.table.status_cache == "FREE"
        event = db.execute(
            select(TableStatusEvent)
            .where(TableStatusEvent.reason == "TICKET_CANCELLED")
            .order_by(TableStatusEvent.id.desc())
        ).scalar_one()
        assert event.from_status == "OCCUPIED"
        assert event.to_status == "FREE"


def test_cancel_in_payment_ticket_cancels_active_payments() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        _add_line(db, ticket, employee)
        send_round(db, ticket.id, employee.id)
        start_payment(db, ticket.id, employee.id)
        cash = db.execute(
            select(PaymentMethod).where(PaymentMethod.method_key == "CASH")
        ).scalar_one()
        payment = create_payment(db, ticket.id, employee.id, cash.id, 100)
        db.commit()

        cancel_ticket(db, ticket.id, employee.id, "Cambio de decisión")
        db.commit()

        assert payment.status == "CANCELLED"
        assert payment.cancelled_by_employee_id == employee.id
        assert payment.cancelled_at is not None
        assert ticket.status == "CANCELLED"


def test_cannot_cancel_paid_ticket() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        _add_line(db, ticket, employee)
        _pay_ticket(db, ticket, employee)

        with pytest.raises(BusinessConflictError, match="pagado"):
            cancel_ticket(db, ticket.id, employee.id)


def test_employee_without_permission_cannot_cancel() -> None:
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        db.execute(delete(EmployeeRole).where(EmployeeRole.employee_id == employee.id))
        db.flush()

        with pytest.raises(PermissionDeniedError, match="TICKET_CANCEL"):
            cancel_ticket_line(db, line.id, employee.id)
        db.rollback()


def test_cancel_line_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _context(db)
        line = _add_line(db, ticket, employee)
        employee_id, line_id = employee.id, line.id

    response = client.post(
        f"/api/v1/pos/ticket-lines/{line_id}/cancel",
        json={"employee_id": employee_id, "reason": "Error de captura"},
    )

    assert response.status_code == 200
    assert response.json()["line"]["status"] == "CANCELLED"
    assert response.json()["ticket"]["total_cents"] == 0
    assert response.json()["print_jobs_created"] == 0


def test_cancel_ticket_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _context(db)
        _add_line(db, ticket, employee)
        employee_id, ticket_id = employee.id, ticket.id

    response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/cancel",
        json={"employee_id": employee_id, "reason": "Cliente canceló pedido"},
    )

    assert response.status_code == 200
    assert response.json()["ticket"]["status"] == "CANCELLED"
    assert response.json()["lines_cancelled"] == 1
    assert response.json()["payments_cancelled"] == 0
    assert response.json()["table_released"] is True

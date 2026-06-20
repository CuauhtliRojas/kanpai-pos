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
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import BusinessConflictError, InvalidBusinessDataError
from app.services.order_service import send_round
from app.services.payment_service import create_payment, start_payment
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table


def _clean_operational_data(db: Session) -> None:
    """Limpia datos POS de pruebas y conserva todos los catálogos seed."""
    for model in (
        PrintJob,
        StationOrderLine,
        StationOrder,
        CommandBatch,
        AuditEvent,
        TableStatusEvent,
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
def clean_payment_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _payment_context(db: Session, *, send: bool = True) -> tuple[Employee, Ticket]:
    employee = db.scalar(
        select(Employee).where(Employee.active.is_(True)).order_by(Employee.id)
    )
    table = db.scalar(
        select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id)
    )
    product = db.scalar(select(Product).where(Product.sku == "DEV-CHELA"))
    assert employee is not None
    assert table is not None
    assert product is not None
    open_cash_shift(db, employee.id, 0)
    ticket = open_ticket_for_table(db, table.id, employee.id)
    add_product_to_ticket(db, ticket.id, product.id, employee.id, 2)
    if send:
        send_round(db, ticket.id, employee.id)
    db.commit()
    return employee, ticket


def _method(db: Session, key: str) -> PaymentMethod:
    return db.execute(
        select(PaymentMethod).where(PaymentMethod.method_key == key)
    ).scalar_one()


def test_start_payment_after_sent_round() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)

        result = start_payment(db, ticket.id, employee.id)
        db.commit()

        assert result.status == "En cobro"
        assert result.billing_started_at is not None
        assert result.table.status_cache == "En cobro"
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Cobro iniciado"
                )
            )
            == "Cobro iniciado"
        )


def test_start_payment_rejects_captured_lines() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db, send=False)

        with pytest.raises(InvalidBusinessDataError):
            start_payment(db, ticket.id, employee.id)


def test_start_payment_rejects_zero_total() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        ticket.total_cents = 0
        db.flush()

        with pytest.raises(InvalidBusinessDataError):
            start_payment(db, ticket.id, employee.id)


def test_start_payment_cannot_run_twice() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        db.flush()

        with pytest.raises(BusinessConflictError):
            start_payment(db, ticket.id, employee.id)


def test_partial_payment_keeps_ticket_in_payment() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")

        payment = create_payment(db, ticket.id, employee.id, cash.id, 100)
        db.commit()

        assert payment.status == "Activo"
        assert ticket.status == "En cobro"
        assert ticket.table.status_cache == "En cobro"
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Pago registrado"
                )
            )
            == "Pago registrado"
        )
        assert (
            db.scalar(select(PrintJob.id).where(PrintJob.job_type == "Ticket")) is None
        )


def test_complete_payment_closes_ticket_and_releases_table() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")

        create_payment(db, ticket.id, employee.id, cash.id, ticket.total_cents)
        db.commit()

        assert ticket.status == "Cobrado"
        assert ticket.payment_status == "Pagado"
        assert ticket.paid_at is not None
        assert ticket.closed_by_employee_id == employee.id
        assert ticket.table.status_cache == "Libre"
        table_event = db.scalar(
            select(TableStatusEvent)
            .where(TableStatusEvent.to_status == "Libre")
            .order_by(TableStatusEvent.id.desc())
        )
        assert table_event is not None
        assert table_event.from_status == "En cobro"


def test_complete_payment_creates_ticket_print_job() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")
        create_payment(db, ticket.id, employee.id, cash.id, ticket.total_cents)
        db.commit()

        job = db.execute(
            select(PrintJob).where(PrintJob.job_type == "Ticket")
        ).scalar_one()
        assert job.printer_key_snapshot == "CAJA"
        assert job.status == "Pendiente"
        assert job.attempts == 0
        assert job.idempotency_key == f"TICKET:{ticket.id}"
        assert job.ticket_id == ticket.id
        assert job.cash_shift_id == ticket.cash_shift_id
        assert "KANPAI\nTICKET" in job.content_snapshot
        job.content_snapshot.encode("ascii")


def test_payment_rejects_open_ticket() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        cash = _method(db, "Efectivo")

        with pytest.raises(BusinessConflictError):
            create_payment(db, ticket.id, employee.id, cash.id, ticket.total_cents)


def test_payment_requires_reference_when_configured() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        card = _method(db, "Tarjeta")

        with pytest.raises(InvalidBusinessDataError):
            create_payment(db, ticket.id, employee.id, card.id, ticket.total_cents)


def test_cash_payment_calculates_change() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")

        payment = create_payment(
            db,
            ticket.id,
            employee.id,
            cash.id,
            ticket.total_cents,
            received_cents=ticket.total_cents + 500,
        )

        assert payment.change_cents == 500


def test_cash_payment_rejects_insufficient_received_amount() -> None:
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")

        with pytest.raises(InvalidBusinessDataError):
            create_payment(
                db,
                ticket.id,
                employee.id,
                cash.id,
                ticket.total_cents,
                received_cents=ticket.total_cents - 1,
            )


def test_start_payment_endpoint() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        employee_id, ticket_id = employee.id, ticket.id

    response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/start-payment",
        json={"employee_id": employee_id},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "En cobro"


def test_create_and_list_payments_endpoints() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        start_payment(db, ticket.id, employee.id)
        cash = _method(db, "Efectivo")
        db.commit()
        employee_id = employee.id
        ticket_id = ticket.id
        method_id = cash.id
        total_cents = ticket.total_cents

    create_response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/payments",
        json={
            "employee_id": employee_id,
            "payment_method_id": method_id,
            "amount_cents": total_cents,
            "received_cents": total_cents,
            "reference": None,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["total_paid_cents"] == total_cents
    assert create_response.json()["remaining_cents"] == 0
    assert create_response.json()["closed"] is True

    list_response = client.get(f"/api/v1/pos/tickets/{ticket_id}/payments")
    assert list_response.status_code == 200
    assert len(list_response.json()["payments"]) == 1
    assert list_response.json()["payments"][0]["status"] == "Activo"


def test_payment_endpoints_map_domain_errors() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _payment_context(db)
        card = _method(db, "Tarjeta")
        employee_id, ticket_id, card_id = employee.id, ticket.id, card.id

    open_ticket_payment = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/payments",
        json={
            "employee_id": employee_id,
            "payment_method_id": card_id,
            "amount_cents": 100,
        },
    )
    assert open_ticket_payment.status_code == 409

    start_response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/start-payment",
        json={"employee_id": employee_id},
    )
    assert start_response.status_code == 200
    missing_reference = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/payments",
        json={
            "employee_id": employee_id,
            "payment_method_id": card_id,
            "amount_cents": 100,
        },
    )
    assert missing_reference.status_code == 400

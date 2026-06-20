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
    Payment,
    PrintJob,
    Product,
    ProductStationAssignment,
    StationOrder,
    StationOrderLine,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
    TicketLineNote,
)
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import InvalidBusinessDataError
from app.services.order_service import send_round
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table


def _clean_operational_data(db: Session) -> None:
    """Limpia datos transaccionales y conserva todos los catálogos seed."""
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
def clean_order_data() -> None:
    run_seed()
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _open_ticket(db: Session) -> tuple[Employee, Ticket]:
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
    open_cash_shift(db, employee.id, 0)
    db.commit()
    ticket = open_ticket_for_table(db, table.id, employee.id)
    db.commit()
    return employee, ticket


def _product(db: Session, sku: str = "DEV-CHELA") -> Product:
    return db.execute(select(Product).where(Product.sku == sku)).scalar_one()


def test_send_simple_line_creates_complete_logical_command() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        line = add_product_to_ticket(
            db, ticket.id, _product(db).id, employee.id, 2, "Muy fría"
        )[0]
        db.commit()

        batch = send_round(db, ticket.id, employee.id)
        db.commit()

        station_order = db.scalar(
            select(StationOrder).where(StationOrder.command_batch_id == batch.id)
        )
        assert batch.batch_type == "Pedido"
        assert batch.round_number == 1
        assert station_order is not None
        assert station_order.status == "En cola"

        order_line = db.scalar(
            select(StationOrderLine).where(
                StationOrderLine.station_order_id == station_order.id
            )
        )
        assert order_line is not None
        assert order_line.ticket_line_id == line.id
        assert order_line.quantity == 2
        assert order_line.note_snapshot == "Muy fría"
        assert order_line.line_action == "Agregar"

        print_job = db.scalar(
            select(PrintJob).where(PrintJob.command_batch_id == batch.id)
        )
        assert print_job is not None
        assert print_job.status == "Pendiente"
        assert print_job.attempts == 0
        assert "KANPAI\nCOMANDA" in print_job.content_snapshot
        assert ticket.folio in print_job.content_snapshot
        assert "Muy fria" in print_job.content_snapshot

        db.refresh(line)
        assert line.status == "Enviado a comanda"
        assert line.round_number == 1
        assert line.sent_at is not None
        assert (
            db.scalar(
                select(AuditEvent.event_type).where(
                    AuditEvent.event_type == "Ronda enviada"
                )
            )
            == "Ronda enviada"
        )


def test_second_round_only_sends_new_captured_lines() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = _product(db)
        first_line = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)[0]
        db.commit()
        first_batch = send_round(db, ticket.id, employee.id)
        db.commit()

        second_line = add_product_to_ticket(db, ticket.id, product.id, employee.id, 3)[
            0
        ]
        db.commit()
        second_batch = send_round(db, ticket.id, employee.id)
        db.commit()

        assert first_batch.round_number == 1
        assert second_batch.round_number == 2
        assert first_line.round_number == 1
        assert second_line.round_number == 2
        second_order_ids = select(StationOrder.id).where(
            StationOrder.command_batch_id == second_batch.id
        )
        sent_ids = set(
            db.execute(
                select(StationOrderLine.ticket_line_id).where(
                    StationOrderLine.station_order_id.in_(second_order_ids)
                )
            ).scalars()
        )
        assert sent_ids == {second_line.id}


def test_send_round_rejects_when_no_captured_lines() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)

        with pytest.raises(InvalidBusinessDataError):
            send_round(db, ticket.id, employee.id)


def test_package_sends_components_but_not_parent() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        lines = add_product_to_ticket(
            db, ticket.id, _product(db, "DEV-CHELA-SAKE").id, employee.id, 1
        )
        db.commit()

        batch = send_round(db, ticket.id, employee.id)
        db.commit()

        parent = lines[0]
        components = lines[1:]
        produced_line_ids = set(
            db.execute(
                select(StationOrderLine.ticket_line_id)
                .join(StationOrder)
                .where(StationOrder.command_batch_id == batch.id)
            ).scalars()
        )
        assert parent.id not in produced_line_ids
        assert produced_line_ids == {line.id for line in components}
        assert parent.status == "Impreso"
        assert all(line.status == "Enviado a comanda" for line in components)


def test_line_without_station_is_marked_printed_without_command() -> None:
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        product = _product(db)
        assignment = db.scalar(
            select(ProductStationAssignment).where(
                ProductStationAssignment.product_id == product.id,
                ProductStationAssignment.is_primary.is_(True),
            )
        )
        assert assignment is not None
        assignment.active = False
        line = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)[0]
        line.station_id_snapshot = None
        db.commit()

        try:
            batch = send_round(db, ticket.id, employee.id)
            db.commit()
            assert line.status == "Impreso"
            assert (
                db.scalar(
                    select(func.count(StationOrder.id)).where(
                        StationOrder.command_batch_id == batch.id
                    )
                )
                == 0
            )
            assert (
                db.scalar(
                    select(func.count(PrintJob.id)).where(
                        PrintJob.command_batch_id == batch.id
                    )
                )
                == 0
            )
        finally:
            assignment.active = True
            db.commit()


def test_send_round_and_query_endpoints() -> None:
    client = TestClient(app)
    with SessionLocal() as db:
        employee, ticket = _open_ticket(db)
        add_product_to_ticket(db, ticket.id, _product(db).id, employee.id, 1)
        db.commit()
        employee_id = employee.id
        ticket_id = ticket.id

    response = client.post(
        f"/api/v1/pos/tickets/{ticket_id}/send-round",
        json={"employee_id": employee_id},
    )
    assert response.status_code == 201
    assert response.json() == {
        "ticket_id": ticket_id,
        "command_batch_id": response.json()["command_batch_id"],
        "round_number": 1,
        "station_orders_created": 1,
        "print_jobs_created": 1,
        "lines_sent": 1,
    }

    orders_response = client.get(f"/api/v1/pos/tickets/{ticket_id}/station-orders")
    assert orders_response.status_code == 200
    assert len(orders_response.json()) == 1
    assert len(orders_response.json()[0]["lines"]) == 1

    jobs_response = client.get("/api/v1/pos/print-jobs/pending")
    assert jobs_response.status_code == 200
    assert len(jobs_response.json()) == 1
    assert jobs_response.json()[0]["status"] == "Pendiente"

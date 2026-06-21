from datetime import datetime, timedelta
from itertools import count

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
    InventoryMovement,
    Payment,
    PrintJob,
    Printer,
    Product,
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
)
from app.services.cash_shift_service import open_cash_shift
from app.services.exceptions import BusinessConflictError
from app.services.order_service import send_round
from app.services.print_queue_service import (
    claim_next_print_job,
    list_pending_print_jobs,
    mark_print_job_failed,
    mark_print_job_printed,
    retry_failed_print_jobs,
)
from app.services.print_service import sanitize_print_content
from app.services.product_service import add_product_to_ticket
from app.services.ticket_service import open_ticket_for_table

_job_sequence = count(1)


def _clean_operational_data(db: Session) -> None:
    """Limpia operaciones en orden de dependencias y conserva catálogos seed."""
    for model in (
        StockAlert,
        InventoryMovement,
        PurchaseReceiptLine,
        PurchaseReceipt,
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
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def clean_print_queue_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean_operational_data(db)
    yield
    with SessionLocal() as db:
        _clean_operational_data(db)


def _job(
    db: Session,
    printer_key: str = "BARRA_FRIA",
    *,
    status: str = "Pendiente",
    created_at: datetime | None = None,
    next_retry_at: datetime | None = None,
) -> PrintJob:
    """Crea un trabajo mínimo para probar la máquina de estados de la cola."""
    number = next(_job_sequence)
    printer = db.scalar(select(Printer).where(Printer.printer_key == printer_key))
    assert printer is not None
    print_job = PrintJob(
        folio=f"QA-PRINT-{number:06d}",
        job_type="Comanda",
        printer_id=printer.id,
        printer_key_snapshot=printer_key,
        content_snapshot="KANPAI\nQA",
        status=status,
        attempts=0,
        idempotency_key=f"QA-PRINT:{number}",
        next_retry_at=next_retry_at,
    )
    if created_at is not None:
        print_job.created_at = created_at
    db.add(print_job)
    db.flush()
    return print_job


def _open_ticket_with_line(db: Session, note: str) -> Ticket:
    """Abre una venta mínima para comprobar generación real de PrintJob."""
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    table = db.scalar(
        select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id)
    )
    product = db.scalar(select(Product).where(Product.sku == "DEV-CHELA"))
    assert employee is not None and table is not None and product is not None
    open_cash_shift(db, employee.id, 0)
    ticket = open_ticket_for_table(db, table.id, employee.id)
    add_product_to_ticket(db, ticket.id, product.id, employee.id, 1, note)
    db.flush()
    return ticket


def test_seed_creates_logical_printers() -> None:
    with SessionLocal() as db:
        keys = set(db.scalars(select(Printer.printer_key)))
    assert {"CAJA", "COCINA", "BARRA_FRIA", "COCTELERIA", "BARRA_CALIENTE"} <= keys


def test_list_pending_filters_by_printer_key() -> None:
    with SessionLocal() as db:
        cold_job = _job(db)
        _job(db, "CAJA")
        db.commit()
        jobs = list_pending_print_jobs(db, "BARRA_FRIA")
    assert [job.id for job in jobs] == [cold_job.id]


def test_claim_takes_oldest_changes_status_and_increments_attempts() -> None:
    with SessionLocal() as db:
        old_job = _job(db, created_at=datetime.utcnow() - timedelta(minutes=2))
        _job(db, created_at=datetime.utcnow() - timedelta(minutes=1))
        db.commit()
        claimed = claim_next_print_job(db, "BARRA_FRIA", "local-daemon-01")
        assert claimed is not None
        assert claimed.id == old_job.id
        assert claimed.status == "Tomado"
        assert claimed.attempts == 1
        assert claimed.claimed_by == "local-daemon-01"
        assert claimed.claimed_at is not None


def test_claim_returns_none_without_available_jobs() -> None:
    with SessionLocal() as db:
        assert claim_next_print_job(db, "BARRA_FRIA", "worker") is None


def test_claim_skips_future_retry_and_does_not_double_take() -> None:
    with SessionLocal() as db:
        _job(db, next_retry_at=datetime.utcnow() + timedelta(minutes=1))
        available = _job(db)
        db.commit()
        first = claim_next_print_job(db, "BARRA_FRIA", "worker-a")
        second = claim_next_print_job(db, "BARRA_FRIA", "worker-b")
        assert first is not None and first.id == available.id
        assert second is None


def test_mark_printed_changes_claimed_job_to_printed() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        claim_next_print_job(db, "BARRA_FRIA", "worker")
        printed = mark_print_job_printed(db, print_job.id, "worker")
        assert printed.status == "Impreso"
        assert printed.printed_at is not None
        assert printed.last_error is None


def test_mark_printed_rejects_wrong_status() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        with pytest.raises(BusinessConflictError):
            mark_print_job_printed(db, print_job.id, "worker")


def test_mark_printed_rejects_another_worker() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        claim_next_print_job(db, "BARRA_FRIA", "worker-a")
        with pytest.raises(BusinessConflictError):
            mark_print_job_printed(db, print_job.id, "worker-b")


def test_mark_failed_records_error_and_retry_time() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        claim_next_print_job(db, "BARRA_FRIA", "worker")
        before = datetime.utcnow() + timedelta(seconds=59)
        failed = mark_print_job_failed(db, print_job.id, "worker", "Sin papel")
        assert failed.status == "Fallido"
        assert failed.failed_at is not None
        assert failed.last_error == "Sin papel"
        assert failed.next_retry_at is not None
        assert failed.next_retry_at >= before


def test_retry_failed_requeues_due_jobs_and_preserves_error() -> None:
    with SessionLocal() as db:
        print_job = _job(
            db,
            status="Fallido",
            next_retry_at=datetime.utcnow() - timedelta(seconds=1),
        )
        print_job.claimed_by = "worker"
        print_job.claimed_at = datetime.utcnow()
        print_job.last_error = "Sin papel"
        db.commit()
        assert retry_failed_print_jobs(db) == 1
        assert print_job.status == "Pendiente"
        assert print_job.claimed_by is None
        assert print_job.claimed_at is None
        assert print_job.last_error == "Sin papel"


def test_retry_failed_filters_by_printer() -> None:
    with SessionLocal() as db:
        cold_job = _job(db, status="Fallido")
        caja_job = _job(db, "CAJA", status="Fallido")
        db.commit()
        assert retry_failed_print_jobs(db, "BARRA_FRIA", reset_all=True) == 1
        assert cold_job.status == "Pendiente"
        assert caja_job.status == "Fallido"


def test_sanitize_print_content_produces_safe_ascii() -> None:
    content = sanitize_print_content("Estación\r\nLíneas\tMínimo 🧊\x00")
    assert content == "Estacion\nLineasMinimo "
    assert content.isascii()


def test_new_print_jobs_store_sanitized_snapshot() -> None:
    with SessionLocal() as db:
        ticket = _open_ticket_with_line(db, "Mínimo 🧊")
        employee_id = ticket.opened_by_employee_id
        send_round(db, ticket.id, employee_id)
        print_job = db.scalar(select(PrintJob).where(PrintJob.ticket_id == ticket.id))
        assert print_job is not None
        assert "Minimo " in print_job.content_snapshot
        assert "Mínimo" not in print_job.content_snapshot
        assert print_job.content_snapshot.isascii()


def test_claim_next_endpoint() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        job_id = print_job.id
        db.commit()
    response = TestClient(app).post(
        "/api/v1/printing/jobs/claim-next",
        json={"printer_key": "BARRA_FRIA", "worker_id": "daemon"},
    )
    assert response.status_code == 200
    assert response.json()["job"]["id"] == job_id
    assert response.json()["job"]["status"] == "Tomado"


def test_printed_endpoint() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        claim_next_print_job(db, "BARRA_FRIA", "daemon")
        job_id = print_job.id
        db.commit()
    response = TestClient(app).post(
        f"/api/v1/printing/jobs/{job_id}/printed", json={"worker_id": "daemon"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Impreso"


def test_failed_endpoint() -> None:
    with SessionLocal() as db:
        print_job = _job(db)
        db.commit()
        claim_next_print_job(db, "BARRA_FRIA", "daemon")
        job_id = print_job.id
        db.commit()
    response = TestClient(app).post(
        f"/api/v1/printing/jobs/{job_id}/failed",
        json={"worker_id": "daemon", "error_message": "Sin papel"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Fallido"
    assert response.json()["last_error"] == "Sin papel"


def test_retry_failed_endpoint() -> None:
    with SessionLocal() as db:
        _job(db, status="Fallido")
        db.commit()
    response = TestClient(app).post(
        "/api/v1/printing/jobs/retry-failed",
        json={"printer_key": "BARRA_FRIA", "reset_all": True},
    )
    assert response.status_code == 200
    assert response.json() == {"jobs_requeued": 1}


def test_pending_alias_remains_available() -> None:
    with SessionLocal() as db:
        _job(db)
        db.commit()
    response = TestClient(app).get("/api/v1/pos/print-jobs/pending")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_print_job_history_filters_and_omits_content_snapshot() -> None:
    with SessionLocal() as db:
        expected = _job(db, "BARRA_FRIA", status="Fallido")
        _job(db, "CAJA", status="Pendiente")
        expected_id = expected.id
        db.commit()
    response = TestClient(app).get(
        "/api/v1/printing/jobs",
        params={"status": "Fallido", "printer_key": "BARRA_FRIA", "limit": 10},
    )
    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [expected_id]
    assert "content_snapshot" not in response.json()[0]
    assert "claimed_by" not in response.json()[0]


def test_printers_contract_includes_logical_queue_counts() -> None:
    with SessionLocal() as db:
        _job(db, "BARRA_FRIA", status="Pendiente")
        _job(db, "BARRA_FRIA", status="Fallido")
        db.commit()
    response = TestClient(app).get("/api/v1/printing/printers")
    assert response.status_code == 200
    printer = next(item for item in response.json() if item["key"] == "BARRA_FRIA")
    assert printer["pending_count"] == 1
    assert printer["failed_count"] == 1
    assert printer["status"] == "has_failed_jobs"
    assert printer["display_name"]
    assert "physical_name_hint" in printer


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"printer_key": "", "worker_id": "daemon"}, 400),
        ({"printer_key": "BARRA_FRIA", "worker_id": ""}, 400),
        ({"printer_key": "NO_EXISTE", "worker_id": "daemon"}, 404),
    ],
)
def test_claim_endpoint_maps_public_errors(
    payload: dict[str, str], expected_status: int
) -> None:
    response = TestClient(app).post("/api/v1/printing/jobs/claim-next", json=payload)
    assert response.status_code == expected_status
    assert "traceback" not in response.text.lower()

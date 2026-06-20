from datetime import datetime, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.domain.constants import PrintStatus
from app.models import PrintJob
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.print_service import get_active_printer

PRINT_RETRY_DELAY_SECONDS = 60


def _required_text(value: str, field_name: str) -> str:
    """Normaliza un identificador de cola y rechaza valores vacíos."""
    normalized = value.strip()
    if not normalized:
        raise InvalidBusinessDataError(f"{field_name} no puede estar vacío.")
    return normalized


def list_pending_print_jobs(
    db: Session, printer_key: str | None = None, limit: int = 100
) -> list[PrintJob]:
    """Lista trabajos pendientes en FIFO, opcionalmente para una impresora."""
    query = select(PrintJob).where(PrintJob.status == PrintStatus.PENDING)
    if printer_key is not None:
        printer_key = _required_text(printer_key, "printer_key")
        get_active_printer(db, printer_key)
        query = query.where(PrintJob.printer_key_snapshot == printer_key)
    return list(
        db.execute(
            query.order_by(PrintJob.created_at, PrintJob.id).limit(limit)
        ).scalars()
    )


def claim_next_print_job(
    db: Session, printer_key: str, worker_id: str
) -> PrintJob | None:
    """Reclama atómicamente el trabajo FIFO disponible para un worker.

    El ``UPDATE`` condicional evita que dos transacciones reclamen el mismo id.
    SQLite serializa las escrituras, lo cual es suficiente para un POS local;
    un despliegue multiworker requerirá locking más fuerte en otra base de datos.
    La función hace ``flush``, pero deja el ``commit`` al llamador.
    """
    printer_key = _required_text(printer_key, "printer_key")
    worker_id = _required_text(worker_id, "worker_id")
    get_active_printer(db, printer_key)
    now = datetime.utcnow()
    candidate_id = (
        select(PrintJob.id)
        .where(
            PrintJob.status == PrintStatus.PENDING,
            PrintJob.printer_key_snapshot == printer_key,
            or_(PrintJob.next_retry_at.is_(None), PrintJob.next_retry_at <= now),
        )
        .order_by(PrintJob.created_at, PrintJob.id)
        .limit(1)
        .scalar_subquery()
    )
    claimed_id = db.execute(
        update(PrintJob)
        .where(PrintJob.id == candidate_id, PrintJob.status == PrintStatus.PENDING)
        .values(
            status=PrintStatus.CLAIMED,
            claimed_at=now,
            claimed_by=worker_id,
            attempts=PrintJob.attempts + 1,
        )
        .returning(PrintJob.id)
    ).scalar_one_or_none()
    db.flush()
    return db.get(PrintJob, claimed_id) if claimed_id is not None else None


def _claimed_job(db: Session, print_job_id: int, worker_id: str) -> PrintJob:
    """Carga un trabajo reclamado y valida que pertenezca al worker indicado."""
    worker_id = _required_text(worker_id, "worker_id")
    print_job = db.get(PrintJob, print_job_id)
    if print_job is None:
        raise EntityNotFoundError("El trabajo de impresión no existe.")
    if print_job.status != PrintStatus.CLAIMED:
        raise BusinessConflictError("El trabajo de impresión no está reclamado.")
    if print_job.claimed_by and print_job.claimed_by != worker_id:
        raise BusinessConflictError("El trabajo fue reclamado por otro worker.")
    return print_job


def mark_print_job_printed(db: Session, print_job_id: int, worker_id: str) -> PrintJob:
    """Finaliza como impreso un trabajo reclamado por el mismo worker."""
    print_job = _claimed_job(db, print_job_id, worker_id)
    print_job.status = PrintStatus.PRINTED
    print_job.printed_at = datetime.utcnow()
    print_job.last_error = None
    db.flush()
    return print_job


def mark_print_job_failed(
    db: Session, print_job_id: int, worker_id: str, error_message: str
) -> PrintJob:
    """Registra un fallo de impresión y agenda su retry inicial a 60 segundos."""
    error_message = _required_text(error_message, "error_message")
    print_job = _claimed_job(db, print_job_id, worker_id)
    now = datetime.utcnow()
    print_job.status = PrintStatus.FAILED
    print_job.failed_at = now
    print_job.last_error = error_message
    print_job.next_retry_at = now + timedelta(seconds=PRINT_RETRY_DELAY_SECONDS)
    db.flush()
    return print_job


def retry_failed_print_jobs(
    db: Session, printer_key: str | None = None, reset_all: bool = False
) -> int:
    """Reactiva fallos vencidos o todos los fallos cuando se solicita reset.

    Se conserva ``last_error`` para diagnóstico. ``next_retry_at`` se limpia al
    reencolar para que los resets manuales queden disponibles inmediatamente.
    """
    query = select(PrintJob).where(PrintJob.status == PrintStatus.FAILED)
    if printer_key is not None:
        printer_key = _required_text(printer_key, "printer_key")
        get_active_printer(db, printer_key)
        query = query.where(PrintJob.printer_key_snapshot == printer_key)
    if not reset_all:
        query = query.where(PrintJob.next_retry_at <= datetime.utcnow())

    jobs = list(db.execute(query).scalars())
    for print_job in jobs:
        print_job.status = PrintStatus.PENDING
        print_job.claimed_at = None
        print_job.claimed_by = None
        print_job.next_retry_at = None
    db.flush()
    return len(jobs)

from datetime import date, datetime, time, timedelta
from app.core.time import local_now_naive

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.orm import Session

from app.domain.constants import PrintStatus
from app.models import Printer, PrintJob, ProductionStation
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.print_service import get_active_printer

PRINT_RETRY_DELAY_SECONDS = 60


def _print_history_date_range(
    created_from: str | None, created_to: str | None
) -> tuple[datetime | None, datetime | None, bool]:
    def parse(value: str, field: str) -> tuple[datetime, bool]:
        try:
            parsed_date = date.fromisoformat(value)
            return datetime.combine(parsed_date, time.min), True
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is not None:
                    raise ValueError
                return parsed, False
            except ValueError as error:
                raise InvalidBusinessDataError(
                    f"{field} debe ser una fecha o datetime ISO local valido."
                ) from error

    start = parse(created_from, "created_from")[0] if created_from else None
    end = None
    end_exclusive = False
    if created_to:
        end, date_only = parse(created_to, "created_to")
        if date_only:
            end += timedelta(days=1)
            end_exclusive = True
    if start is not None and end is not None:
        if start >= end if end_exclusive else start > end:
            raise InvalidBusinessDataError(
                "created_from no puede ser posterior a created_to."
            )
    return start, end, end_exclusive


def list_print_jobs(
    db: Session,
    status: str | None = None,
    printer_key: str | None = None,
    job_type: str | None = None,
    ticket_id: int | None = None,
    cash_shift_id: int | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Lista metadatos de cola sin exponer el snapshot imprimible."""
    query = select(
        PrintJob.id,
        PrintJob.folio,
        PrintJob.job_type,
        PrintJob.printer_id,
        PrintJob.printer_key_snapshot.label("printer_key"),
        PrintJob.ticket_id,
        PrintJob.cash_shift_id,
        PrintJob.station_order_id,
        PrintJob.command_batch_id,
        PrintJob.status,
        PrintJob.attempts,
        PrintJob.claimed_at,
        PrintJob.printed_at,
        PrintJob.failed_at,
        PrintJob.last_error,
        PrintJob.next_retry_at,
        PrintJob.created_at,
    )
    if status is not None:
        query = query.where(PrintJob.status == status)
    if printer_key is not None:
        query = query.where(PrintJob.printer_key_snapshot == printer_key)
    if job_type is not None:
        query = query.where(PrintJob.job_type == job_type)
    if ticket_id is not None:
        query = query.where(PrintJob.ticket_id == ticket_id)
    if cash_shift_id is not None:
        query = query.where(PrintJob.cash_shift_id == cash_shift_id)
    start, end, end_exclusive = _print_history_date_range(created_from, created_to)
    if start is not None:
        query = query.where(PrintJob.created_at >= start)
    if end is not None:
        query = query.where(
            PrintJob.created_at < end if end_exclusive else PrintJob.created_at <= end
        )
    rows = db.execute(
        query.order_by(PrintJob.created_at.desc(), PrintJob.id.desc())
        .limit(limit)
        .offset(offset)
    ).mappings()
    return [dict(row) for row in rows]


def list_printers(db: Session) -> list[dict]:
    """Proyecta configuracion logica y salud derivada de la cola local."""
    job_stats = (
        select(
            PrintJob.printer_id,
            func.max(PrintJob.created_at).label("last_job_at"),
            func.sum(case((PrintJob.status == PrintStatus.PENDING, 1), else_=0)).label(
                "pending_count"
            ),
            func.sum(case((PrintJob.status == PrintStatus.FAILED, 1), else_=0)).label(
                "failed_count"
            ),
        )
        .group_by(PrintJob.printer_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Printer,
            ProductionStation.name.label("station_name"),
            job_stats.c.last_job_at,
            func.coalesce(job_stats.c.pending_count, 0),
            func.coalesce(job_stats.c.failed_count, 0),
        )
        .outerjoin(ProductionStation, ProductionStation.id == Printer.station_id)
        .outerjoin(job_stats, job_stats.c.printer_id == Printer.id)
        .order_by(Printer.printer_key)
    ).all()
    result = []
    for printer, station_name, last_job_at, pending_count, failed_count in rows:
        is_cash = printer.printer_key.upper() == "CAJA"
        if not printer.active:
            logical_status = "disabled"
        elif failed_count:
            logical_status = "has_failed_jobs"
        elif pending_count:
            logical_status = "has_pending_jobs"
        else:
            logical_status = "enabled"
        result.append(
            {
                "id": printer.id,
                "key": printer.printer_key,
                "display_name": printer.name,
                "role": "cash_register" if is_cash else "station" if printer.station_id else "logical",
                "station_id": printer.station_id,
                "station_name": station_name,
                "enabled": printer.active,
                "physical_name_hint": printer.connection_ref,
                "paper_width_mm": printer.paper_width_mm,
                "supports_cut": printer.autocut_enabled,
                "is_cash_register_printer": is_cash,
                "last_job_at": last_job_at,
                "pending_count": int(pending_count),
                "failed_count": int(failed_count),
                "status": logical_status,
            }
        )
    return result


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
    now = local_now_naive()
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
    print_job.printed_at = local_now_naive()
    print_job.last_error = None
    db.flush()
    return print_job


def mark_print_job_failed(
    db: Session, print_job_id: int, worker_id: str, error_message: str
) -> PrintJob:
    """Registra un fallo de impresión y agenda su retry inicial a 60 segundos."""
    error_message = _required_text(error_message, "error_message")
    print_job = _claimed_job(db, print_job_id, worker_id)
    now = local_now_naive()
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
        query = query.where(PrintJob.next_retry_at <= local_now_naive())

    jobs = list(db.execute(query).scalars())
    for print_job in jobs:
        print_job.status = PrintStatus.PENDING
        print_job.claimed_at = None
        print_job.claimed_by = None
        print_job.next_retry_at = None
    db.flush()
    return len(jobs)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PrintJob, Printer
from app.services.exceptions import BusinessConflictError, EntityNotFoundError


def get_active_printer(db: Session, printer_key: str) -> Printer:
    """Resuelve una impresora lógica activa o reporta un conflicto operativo."""
    printer = db.execute(
        select(Printer).where(Printer.printer_key == printer_key)
    ).scalar_one_or_none()
    if printer is None:
        raise EntityNotFoundError(
            f"No existe la impresora con clave {printer_key}."
        )
    if not printer.active:
        raise BusinessConflictError(
            f"La impresora {printer_key} está inactiva."
        )
    return printer


def list_pending_print_jobs(db: Session) -> list[PrintJob]:
    """Lista trabajos pendientes en orden FIFO, sin enviarlos a hardware."""
    return list(
        db.execute(
            select(PrintJob)
            .where(PrintJob.status == "PENDING")
            .order_by(PrintJob.created_at, PrintJob.id)
        ).scalars()
    )

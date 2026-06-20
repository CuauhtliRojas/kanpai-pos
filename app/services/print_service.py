from sqlalchemy import select
from sqlalchemy.orm import Session
from unicodedata import normalize

from app.models import Payment, PrintJob, Printer, Ticket
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.folio_service import generate_folio


def _ascii_text(value: str) -> str:
    """Normaliza texto dinámico al subconjunto ASCII admitido por impresoras."""
    return normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


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


def create_ticket_print_job(
    db: Session, ticket: Ticket, payments: list[Payment]
) -> PrintJob:
    """Encola una impresión lógica, idempotente y ASCII del ticket pagado."""
    printer = get_active_printer(db, "CAJA")
    payment_lines = [
        f"{payment.payment_method.method_key}: {payment.amount_cents / 100:.2f}"
        for payment in payments
    ]
    content = "\n".join(
        [
            "KANPAI",
            "TICKET",
            f"FOLIO: {ticket.folio}",
            f"MESA: {_ascii_text(ticket.table.display_name)}",
            f"TOTAL: {ticket.total_cents / 100:.2f}",
            "PAGOS:",
            *payment_lines,
            "GRACIAS",
        ]
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type="TICKET",
        printer_id=printer.id,
        printer_key_snapshot="CAJA",
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        content_snapshot=content,
        status="PENDING",
        attempts=0,
        idempotency_key=f"TICKET:{ticket.id}",
    )
    db.add(print_job)
    db.flush()
    return print_job

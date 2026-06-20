from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.constants import PermissionKey, PrintStatus, audit_event
from app.models import AuditEvent, PrintJob, Ticket
from app.services.exceptions import EntityNotFoundError, InvalidBusinessDataError
from app.services.folio_service import generate_folio
from app.services.permission_service import get_active_employee, require_employee_permission
from app.services.print_service import sanitize_print_content


def get_print_job(db: Session, print_job_id: int) -> PrintJob:
    """Return one logical print job for operational inspection."""
    job = db.get(PrintJob, print_job_id)
    if job is None:
        raise EntityNotFoundError("El trabajo de impresion no existe.")
    return job


def request_reprint(
    db: Session, print_job_id: int, employee_id: int, reason: str
) -> PrintJob:
    """Clone a sanitized logical job and record who authorized its reprint."""
    original = get_print_job(db, print_job_id)
    employee = get_active_employee(db, employee_id)
    require_employee_permission(db, employee.id, PermissionKey.REPRINT)
    reason = reason.strip()
    if not reason:
        raise InvalidBusinessDataError("El motivo de reimpresion es obligatorio.")
    now = datetime.utcnow()
    reprint = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type=original.job_type,
        printer_id=original.printer_id,
        printer_key_snapshot=original.printer_key_snapshot,
        ticket_id=original.ticket_id,
        cash_shift_id=original.cash_shift_id,
        station_order_id=original.station_order_id,
        command_batch_id=original.command_batch_id,
        content_snapshot=sanitize_print_content(original.content_snapshot),
        status=PrintStatus.PENDING,
        attempts=0,
        idempotency_key=f"REPRINT:{original.id}:{now.isoformat()}",
    )
    db.add(reprint)
    db.flush()
    ticket = db.get(Ticket, original.ticket_id) if original.ticket_id else None
    db.add(
        AuditEvent(
            event_type=audit_event("REPRINT_REQUESTED"),
            entity_type="Trabajo de impresion",
            entity_id=reprint.id,
            actor_employee_id=employee.id,
            cash_shift_id=original.cash_shift_id or (ticket.cash_shift_id if ticket else None),
            ticket_id=original.ticket_id,
            before_snapshot=str(original.id),
            after_snapshot=str(reprint.id),
            reason=reason,
        )
    )
    db.flush()
    return reprint

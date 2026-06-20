from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import (
    PrintJobType,
    PrintStatus,
    TicketLineNoteType,
    TicketLineStatus,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    PrintJob,
    ProductionStation,
    StationOrder,
    StationOrderLine,
    Ticket,
    TicketLine,
    TicketLineModification,
    TicketLineNote,
)
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.permission_service import get_active_employee
from app.services.print_service import get_active_printer, sanitize_print_content


def modify_ticket_line(
    db: Session, line_id: int, employee_id: int, note: str
) -> TicketLineModification:
    """Persist a line modification and enqueue a station notice when already sent."""
    line = db.get(TicketLine, line_id)
    if line is None:
        raise EntityNotFoundError("La linea de ticket no existe.")
    ticket = db.get(Ticket, line.ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_PAYMENT):
        raise BusinessConflictError("El ticket no admite modificaciones.")
    if line.status == TicketLineStatus.CANCELLED:
        raise BusinessConflictError("La linea cancelada no admite modificaciones.")
    employee = get_active_employee(db, employee_id)
    note = note.strip()
    if not note:
        raise InvalidBusinessDataError("La nota de modificacion es obligatoria.")

    line.note = note
    db.add(
        TicketLineNote(
            ticket_line_id=line.id,
            note_type=TicketLineNoteType.MODIFICATION,
            note=note,
            created_by_employee_id=employee.id,
        )
    )
    print_job = None
    station_order = None
    if line.status in (TicketLineStatus.SENT_TO_KITCHEN, TicketLineStatus.PRINTED):
        station_order = db.scalar(
            select(StationOrder)
            .join(StationOrderLine)
            .where(StationOrderLine.ticket_line_id == line.id)
            .order_by(StationOrder.id.desc())
        )
        if station_order is not None:
            station = db.get(ProductionStation, station_order.station_id)
            if station is None or not station.printer_key:
                raise BusinessConflictError("La estacion no tiene impresora configurada.")
            printer = get_active_printer(db, station.printer_key)
            content = "\n".join(
                [
                    "KANPAI",
                    "MODIFICACION",
                    f"FOLIO: {ticket.folio}",
                    f"MESA: {ticket.table.display_name}",
                    f"PRODUCTO: {line.product_name_snapshot}",
                    f"NOTA: {note}",
                ]
            )
            print_job = PrintJob(
                folio=generate_folio(db, "IMPRESION"),
                job_type=PrintJobType.MODIFICATION,
                printer_id=printer.id,
                printer_key_snapshot=printer.printer_key,
                ticket_id=ticket.id,
                station_order_id=station_order.id,
                command_batch_id=station_order.command_batch_id,
                content_snapshot=sanitize_print_content(content),
                status=PrintStatus.PENDING,
                attempts=0,
                idempotency_key=f"MODIFICACION:{line.id}:{datetime.utcnow().isoformat()}",
            )
            db.add(print_job)
            db.flush()

    modification = TicketLineModification(
        ticket_line_id=line.id,
        ticket_id=ticket.id,
        note=note,
        created_by_employee_id=employee.id,
        print_job_id=print_job.id if print_job else None,
    )
    db.add(modification)
    db.flush()
    db.add(
        AuditEvent(
            event_type=audit_event("TICKET_LINE_MODIFIED"),
            entity_type="Linea de ticket",
            entity_id=line.id,
            actor_employee_id=employee.id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            reason=note,
            after_snapshot=note,
        )
    )
    db.flush()
    return modification

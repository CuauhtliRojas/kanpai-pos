import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Payment, Ticket, TicketLine
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    PermissionDeniedError,
)
from app.services.permission_service import employee_has_permission
from app.services.print_service import create_cancellation_print_job
from app.services.table_service import release_table_for_cancelled_ticket
from app.services.ticket_service import (
    get_active_employee,
    get_ticket,
    recalculate_ticket_totals,
)

SENT_LINE_STATUSES = ("ENVIADO_COMANDA", "IMPRESO")


def _normalize_reason(reason: str | None) -> str | None:
    return reason.strip() if reason and reason.strip() else None


def _validate_authorized_employee(db: Session, employee_id: int) -> None:
    """Valida existencia, actividad y permiso operativo de cancelación."""
    get_active_employee(db, employee_id)
    if not employee_has_permission(db, employee_id, "TICKET_CANCEL"):
        raise PermissionDeniedError(
            "El empleado no tiene permiso TICKET_CANCEL."
        )


def _mark_line_cancelled(
    line: TicketLine,
    employee_id: int,
    reason: str | None,
    cancelled_at: datetime,
) -> None:
    line.status = "CANCELLED"
    line.cancelled_by_employee_id = employee_id
    line.cancel_reason = reason
    line.cancelled_at = cancelled_at


def cancel_ticket_line(
    db: Session,
    line_id: int,
    employee_id: int,
    reason: str | None = None,
) -> TicketLine:
    """Cancela una línea autorizada y propaga la cancelación de un paquete.

    Los componentes incluidos no pueden cancelarse directamente mientras el
    padre siga activo. Para un padre de paquete se cancelan sus hijos y solo
    aquellos ya enviados a una estación generan cancelación de comanda. La
    función recalcula el ticket, registra auditoría y nunca hace ``commit``.
    """
    line = db.get(TicketLine, line_id)
    if line is None:
        raise EntityNotFoundError("La línea no existe.")
    ticket = db.get(Ticket, line.ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    _validate_authorized_employee(db, employee_id)
    if ticket.status == "PAID":
        raise BusinessConflictError("No se puede cancelar una línea de un ticket pagado.")
    if ticket.status == "CANCELLED":
        raise BusinessConflictError("El ticket ya está cancelado.")
    if line.status == "CANCELLED":
        raise BusinessConflictError("La línea ya está cancelada.")
    if line.line_type == "PACKAGE_COMPONENT" and line.parent_ticket_line_id:
        parent = db.get(TicketLine, line.parent_ticket_line_id)
        if parent is not None and parent.status != "CANCELLED":
            raise BusinessConflictError(
                "El componente no puede cancelarse directamente; cancele el paquete padre."
            )

    normalized_reason = _normalize_reason(reason)
    targets = [line]
    if line.line_type == "PACKAGE_PARENT":
        targets.extend(
            db.execute(
                select(TicketLine)
                .where(
                    TicketLine.parent_ticket_line_id == line.id,
                    TicketLine.status != "CANCELLED",
                )
                .order_by(TicketLine.id)
            ).scalars()
        )

    now = datetime.utcnow()
    before_statuses = {target.id: target.status for target in targets}
    for target in targets:
        previous_status = target.status
        _mark_line_cancelled(target, employee_id, normalized_reason, now)
        if (
            target.line_type != "PACKAGE_PARENT"
            and previous_status in SENT_LINE_STATUSES
            and target.station_id_snapshot is not None
        ):
            create_cancellation_print_job(
                db,
                ticket,
                target,
                normalized_reason,
                f"CANCEL_LINE:{target.id}",
            )

    db.flush()
    recalculate_ticket_totals(db, ticket)
    db.add(
        AuditEvent(
            event_type="TICKET_LINE_CANCELLED",
            entity_type="TicketLine",
            entity_id=line.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"statuses": before_statuses}),
            after_snapshot=json.dumps(
                {"line_ids": [target.id for target in targets], "status": "CANCELLED"}
            ),
            reason=normalized_reason,
        )
    )
    db.flush()
    return line


def cancel_ticket(
    db: Session,
    ticket_id: int,
    employee_id: int,
    reason: str | None = None,
) -> Ticket:
    """Cancela un ticket no pagado, sus líneas y sus pagos activos.

    Los totales se preservan como evidencia histórica. Se generan cancelaciones
    de comanda para líneas enviadas con estación, se libera la mesa y todas las
    escrituras quedan pendientes del ``commit`` del llamador.
    """
    ticket = get_ticket(db, ticket_id)
    _validate_authorized_employee(db, employee_id)
    if ticket.status == "PAID":
        raise BusinessConflictError("No se puede cancelar un ticket pagado.")
    if ticket.status == "CANCELLED":
        raise BusinessConflictError("El ticket ya está cancelado.")

    normalized_reason = _normalize_reason(reason)
    now = datetime.utcnow()
    lines = list(
        db.execute(
            select(TicketLine)
            .where(TicketLine.ticket_id == ticket.id)
            .order_by(TicketLine.id)
        ).scalars()
    )
    for line in lines:
        previous_status = line.status
        if previous_status == "CANCELLED":
            continue
        _mark_line_cancelled(line, employee_id, normalized_reason, now)
        if (
            line.line_type != "PACKAGE_PARENT"
            and previous_status in SENT_LINE_STATUSES
            and line.station_id_snapshot is not None
        ):
            create_cancellation_print_job(
                db,
                ticket,
                line,
                normalized_reason,
                f"CANCEL_TICKET:{ticket.id}:LINE:{line.id}",
            )

    active_payments = list(
        db.execute(
            select(Payment).where(
                Payment.ticket_id == ticket.id,
                Payment.status == "ACTIVE",
            )
        ).scalars()
    )
    for payment in active_payments:
        payment.status = "CANCELLED"
        payment.cancelled_by_employee_id = employee_id
        payment.cancel_reason = normalized_reason
        payment.cancelled_at = now

    previous_status = ticket.status
    ticket.status = "CANCELLED"
    ticket.payment_status = "CANCELLED"
    ticket.cancelled_by_employee_id = employee_id
    ticket.cancel_reason = normalized_reason
    ticket.cancelled_at = now
    release_table_for_cancelled_ticket(db, ticket, employee_id)
    db.add(
        AuditEvent(
            event_type="TICKET_CANCELLED",
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"status": previous_status}),
            after_snapshot=json.dumps(
                {
                    "status": "CANCELLED",
                    "lines_cancelled": sum(
                        line.cancelled_at == now for line in lines
                    ),
                    "payments_cancelled": len(active_payments),
                }
            ),
            reason=normalized_reason,
        )
    )
    db.flush()
    return ticket

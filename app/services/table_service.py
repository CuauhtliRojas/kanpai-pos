from sqlalchemy.orm import Session

from app.domain.constants import TableStatus, audit_event
from app.models import DiningTable, TableStatusEvent, Ticket
from app.services.exceptions import BusinessConflictError, EntityNotFoundError


def get_free_active_table(db: Session, table_id: int) -> DiningTable:
    """Obtiene una mesa activa y libre o reporta la regla que lo impide."""
    table = db.get(DiningTable, table_id)
    if table is None:
        raise EntityNotFoundError("La mesa no existe.")
    if not table.active:
        raise BusinessConflictError("La mesa está inactiva.")
    if table.status_cache != TableStatus.FREE:
        raise BusinessConflictError("La mesa no está libre.")
    return table


def release_table_for_paid_ticket(
    db: Session, ticket: Ticket, employee_id: int
) -> DiningTable:
    """Libera la mesa de un ticket pagado y registra su transición de estado."""
    table = db.get(DiningTable, ticket.table_id)
    if table is None:
        raise EntityNotFoundError("La mesa no existe.")

    table.status_cache = TableStatus.FREE
    db.add(
        TableStatusEvent(
            table_id=table.id,
            ticket_id=ticket.id,
            actor_employee_id=employee_id,
            from_status=TableStatus.IN_PAYMENT,
            to_status=TableStatus.FREE,
            reason=audit_event("TICKET_PAID"),
        )
    )
    db.flush()
    return table


def release_table_for_cancelled_ticket(
    db: Session, ticket: Ticket, employee_id: int
) -> DiningTable:
    """Libera la mesa de un ticket cancelado y registra el estado previo real."""
    table = db.get(DiningTable, ticket.table_id)
    if table is None:
        raise EntityNotFoundError("La mesa no existe.")

    previous_status = table.status_cache
    table.status_cache = TableStatus.FREE
    db.add(
        TableStatusEvent(
            table_id=table.id,
            ticket_id=ticket.id,
            actor_employee_id=employee_id,
            from_status=previous_status,
            to_status=TableStatus.FREE,
            reason=audit_event("TICKET_CANCELLED"),
        )
    )
    db.flush()
    return table

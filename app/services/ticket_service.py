import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Employee, TableStatusEvent, Ticket
from app.services.cash_shift_service import get_current_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.table_service import get_free_active_table


def _get_active_employee(db: Session, employee_id: int, label: str) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError(f"{label} no existe.")
    if not employee.active:
        raise BusinessConflictError(f"{label} está inactivo.")
    return employee


def get_ticket(db: Session, ticket_id: int) -> Ticket:
    """Obtiene un ticket por identificador o reporta que no existe."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    return ticket


def open_ticket_for_table(
    db: Session,
    table_id: int,
    employee_id: int,
    guest_count: int = 1,
    waiter_employee_id: int | None = None,
    note: str | None = None,
) -> Ticket:
    """Abre un ticket en una mesa libre y registra estado y auditoría.

    Todas las escrituras quedan pendientes en la sesión. El llamador debe hacer
    ``commit`` si concluye correctamente o ``rollback`` ante cualquier error.
    """
    cash_shift = get_current_cash_shift(db)
    if cash_shift is None:
        raise BusinessConflictError("No existe un corte de caja abierto.")

    _get_active_employee(db, employee_id, "El empleado")
    if waiter_employee_id is not None:
        _get_active_employee(db, waiter_employee_id, "El mesero")
    table = get_free_active_table(db, table_id)
    if guest_count <= 0:
        raise InvalidBusinessDataError("El número de comensales debe ser mayor a cero.")

    active_ticket = db.execute(
        select(Ticket.id).where(
            Ticket.table_id == table_id,
            Ticket.status.in_(("OPEN", "IN_PAYMENT")),
        )
    ).scalar_one_or_none()
    if active_ticket is not None:
        raise BusinessConflictError("La mesa ya tiene un ticket activo.")

    previous_status = table.status_cache
    ticket = Ticket(
        folio=generate_folio(db, "TICKET"),
        status="OPEN",
        payment_status="UNPAID",
        cash_shift_id=cash_shift.id,
        table_id=table_id,
        opened_by_employee_id=employee_id,
        waiter_employee_id=waiter_employee_id,
        guest_count=guest_count,
        note=note,
    )
    db.add(ticket)
    db.flush()

    table.status_cache = "OCCUPIED"
    db.add(
        TableStatusEvent(
            table_id=table_id,
            ticket_id=ticket.id,
            actor_employee_id=employee_id,
            from_status=previous_status,
            to_status="OCCUPIED",
            reason="TICKET_OPENED",
        )
    )
    db.add(
        AuditEvent(
            event_type="TICKET_OPENED",
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=cash_shift.id,
            ticket_id=ticket.id,
            after_snapshot=json.dumps(
                {
                    "folio": ticket.folio,
                    "table_id": table_id,
                    "status": ticket.status,
                    "guest_count": guest_count,
                }
            ),
        )
    )
    db.flush()
    return ticket

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.constants import (
    TableStatus,
    TicketLineStatus,
    TicketLineType,
    TicketPaymentStatus,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    BusinessSetting,
    Employee,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
)
from app.services.cash_shift_service import get_current_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.table_service import get_free_active_table


def get_active_employee(
    db: Session, employee_id: int, label: str = "El empleado"
) -> Employee:
    """Obtiene un empleado activo o reporta una regla de dominio estable."""
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


def recalculate_ticket_totals(db: Session, ticket: Ticket) -> None:
    """Recalculate subtotal, discounts, tax component and payable total."""
    subtotal = db.execute(
        select(func.coalesce(func.sum(TicketLine.line_total_cents), 0)).where(
            TicketLine.ticket_id == ticket.id,
            TicketLine.line_type.in_(
                (TicketLineType.SIMPLE, TicketLineType.PACKAGE_PARENT)
            ),
            TicketLine.status != TicketLineStatus.CANCELLED,
        )
    ).scalar_one()
    discount = db.execute(
        select(func.coalesce(func.sum(TicketDiscount.amount_cents), 0)).where(
            TicketDiscount.ticket_id == ticket.id
        )
    ).scalar_one()
    ticket.subtotal_cents = int(subtotal)
    ticket.discount_cents = int(discount)
    taxable_base = max(ticket.subtotal_cents - ticket.discount_cents, 0)
    policy = db.scalar(select(BusinessSetting).where(BusinessSetting.active.is_(True)))
    tax_enabled = policy.tax_enabled if policy is not None else True
    rate = policy.tax_rate_bps if policy is not None else 1600
    tax_included = policy.tax_included if policy is not None else False
    if not tax_enabled or rate <= 0:
        tax = 0
    elif tax_included:
        tax = round(taxable_base - taxable_base / (1 + rate / 10_000))
    else:
        tax = round(taxable_base * rate / 10_000)
    ticket.tax_cents = int(tax)
    ticket.total_cents = taxable_base if tax_included else taxable_base + ticket.tax_cents


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

    get_active_employee(db, employee_id, "El empleado")
    if waiter_employee_id is not None:
        get_active_employee(db, waiter_employee_id, "El mesero")
    table = get_free_active_table(db, table_id)
    if guest_count <= 0:
        raise InvalidBusinessDataError("El número de comensales debe ser mayor a cero.")

    active_ticket = db.execute(
        select(Ticket.id).where(
            Ticket.table_id == table_id,
            Ticket.status.in_((TicketStatus.OPEN, TicketStatus.IN_PAYMENT)),
        )
    ).scalar_one_or_none()
    if active_ticket is not None:
        raise BusinessConflictError("La mesa ya tiene un ticket activo.")

    previous_status = table.status_cache
    ticket = Ticket(
        folio=generate_folio(db, "TICKET"),
        status=TicketStatus.OPEN,
        payment_status=TicketPaymentStatus.UNPAID,
        cash_shift_id=cash_shift.id,
        table_id=table_id,
        opened_by_employee_id=employee_id,
        waiter_employee_id=waiter_employee_id,
        guest_count=guest_count,
        note=note,
    )
    db.add(ticket)
    db.flush()

    table.status_cache = TableStatus.OCCUPIED
    db.add(
        TableStatusEvent(
            table_id=table_id,
            ticket_id=ticket.id,
            actor_employee_id=employee_id,
            from_status=previous_status,
            to_status=TableStatus.OCCUPIED,
            reason=audit_event("TICKET_OPENED"),
        )
    )
    db.add(
        AuditEvent(
            event_type=audit_event("TICKET_OPENED"),
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

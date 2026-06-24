from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import DiscountType, PermissionKey, TicketStatus, audit_event
from app.models import AuditEvent, Ticket, TicketDiscount
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.permission_service import get_active_employee, require_employee_permission
from app.services.ticket_service import recalculate_ticket_totals


def apply_discount(
    db: Session,
    ticket_id: int,
    employee_id: int,
    discount_type: str,
    amount_cents: int | None,
    percent_bps: int | None,
    reason: str,
    is_courtesy: bool,
) -> TicketDiscount:
    """Authorize, materialize and audit a discount against the current subtotal."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    if ticket.status != TicketStatus.OPEN:
        raise BusinessConflictError("El ticket debe estar Abierto para aplicar descuentos.")
    employee = get_active_employee(db, employee_id)
    require_employee_permission(db, employee.id, PermissionKey.DISCOUNT_AUTHORIZE)
    reason = reason.strip()
    if not reason:
        raise InvalidBusinessDataError("El motivo es obligatorio.")
    recalculate_ticket_totals(db, ticket)
    if ticket.subtotal_cents <= 0:
        raise InvalidBusinessDataError("El ticket debe tener subtotal mayor a cero.")

    if discount_type == DiscountType.AMOUNT:
        if amount_cents is None or amount_cents <= 0 or percent_bps is not None:
            raise InvalidBusinessDataError("Monto requiere amount_cents mayor a cero.")
        applied = amount_cents
    elif discount_type in (DiscountType.PERCENT, DiscountType.COURTESY):
        if percent_bps is None or percent_bps <= 0 or percent_bps > 10_000:
            raise InvalidBusinessDataError("percent_bps debe estar entre 1 y 10000.")
        if amount_cents is not None:
            raise InvalidBusinessDataError("Un porcentaje no admite amount_cents.")
        applied = round(ticket.subtotal_cents * percent_bps / 10_000)
    else:
        raise InvalidBusinessDataError("discount_type no es valido.")

    existing = ticket.discount_cents
    courtesy = is_courtesy or discount_type == DiscountType.COURTESY
    if applied <= 0 or existing + applied > ticket.subtotal_cents:
        raise InvalidBusinessDataError("El descuento excede el subtotal disponible.")
    if not courtesy and existing + applied >= ticket.subtotal_cents:
        raise InvalidBusinessDataError(
            "El descuento normal debe dejar al menos $1.00 por cobrar."
        )
    discount = TicketDiscount(
        ticket_id=ticket.id,
        discount_source=discount_type,
        amount_cents=applied,
        percent_bps=percent_bps,
        reason=reason,
        is_courtesy=courtesy,
        authorized_by_employee_id=employee.id,
        created_by_employee_id=employee.id,
    )
    db.add(discount)
    db.flush()
    recalculate_ticket_totals(db, ticket)
    db.add(
        AuditEvent(
            event_type=audit_event("COURTESY_APPLIED" if courtesy else "DISCOUNT_APPLIED"),
            entity_type="Descuento de ticket",
            entity_id=discount.id,
            actor_employee_id=employee.id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            reason=reason,
            after_snapshot=str(applied),
        )
    )
    db.flush()
    return discount


def list_ticket_discounts(db: Session, ticket_id: int) -> list[TicketDiscount]:
    """List discounts and courtesies in application order."""
    if db.get(Ticket, ticket_id) is None:
        raise EntityNotFoundError("El ticket no existe.")
    return list(
        db.scalars(
            select(TicketDiscount)
            .where(TicketDiscount.ticket_id == ticket_id)
            .order_by(TicketDiscount.id)
        )
    )

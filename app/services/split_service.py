"""División formal de cuentas compatible con pagos parciales existentes."""

import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.constants import ActiveStatus, TicketLineStatus, TicketSplitStatus, TicketSplitType, TicketStatus, audit_event
from app.models import AuditEvent, Payment, Ticket, TicketLine, TicketSplit, TicketSplitLine
from app.services.exceptions import BusinessConflictError, EntityNotFoundError, InvalidBusinessDataError
from app.services.payment_service import create_payment
from app.services.permission_service import get_active_employee


def _splittable_ticket(db: Session, ticket_id: int, employee_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    get_active_employee(db, employee_id)
    if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_PAYMENT):
        raise BusinessConflictError("El ticket cobrado o cancelado no se puede dividir.")
    return ticket


def create_equal_splits(db: Session, ticket_id: int, employee_id: int, parts: int) -> list[TicketSplit]:
    """Distribuye centavos exactamente entre partes, asignando el residuo al inicio."""
    ticket = _splittable_ticket(db, ticket_id, employee_id)
    if parts < 2 or parts > 50:
        raise InvalidBusinessDataError("La división requiere entre 2 y 50 partes.")
    if db.scalar(select(func.count(TicketSplit.id)).where(TicketSplit.ticket_id == ticket.id, TicketSplit.status != TicketSplitStatus.CANCELLED)):
        raise BusinessConflictError("El ticket ya tiene divisiones activas.")
    base, remainder = divmod(ticket.total_cents, parts)
    splits = []
    for index in range(1, parts + 1):
        split = TicketSplit(
            ticket_id=ticket.id, name=f"Parte {index}", split_type=TicketSplitType.EQUAL,
            parts=parts, part_number=index, amount_cents=base + (1 if index <= remainder else 0),
            status=TicketSplitStatus.OPEN, created_by_employee_id=employee_id,
        )
        db.add(split)
        splits.append(split)
    db.flush()
    db.add(AuditEvent(
        event_type=audit_event("TICKET_SPLIT_CREATED"), entity_type="Ticket", entity_id=ticket.id,
        actor_employee_id=employee_id, cash_shift_id=ticket.cash_shift_id, ticket_id=ticket.id,
        after_snapshot=json.dumps({"mode": "equal", "parts": parts, "split_ids": [item.id for item in splits]}),
    ))
    db.flush()
    return splits


def create_lines_split(db: Session, ticket_id: int, employee_id: int, name: str, ticket_line_ids: list[int]) -> TicketSplit:
    """Crea una división con líneas completas aún no asignadas a otra división."""
    ticket = _splittable_ticket(db, ticket_id, employee_id)
    unique_ids = set(ticket_line_ids)
    if not unique_ids:
        raise InvalidBusinessDataError("Debe seleccionar al menos una línea.")
    lines = list(db.scalars(select(TicketLine).where(
        TicketLine.ticket_id == ticket.id, TicketLine.id.in_(unique_ids),
        TicketLine.status != TicketLineStatus.CANCELLED,
    )))
    if len(lines) != len(unique_ids):
        raise InvalidBusinessDataError("Una línea no pertenece al ticket o está cancelada.")
    already_used = db.scalar(select(func.count(TicketSplitLine.id)).join(TicketSplit).where(
        TicketSplit.ticket_id == ticket.id, TicketSplit.status != TicketSplitStatus.CANCELLED,
        TicketSplitLine.ticket_line_id.in_(unique_ids),
    ))
    if already_used:
        raise BusinessConflictError("Una línea ya pertenece a otra división.")
    active_lines = list(db.scalars(select(TicketLine).where(
        TicketLine.ticket_id == ticket.id,
        TicketLine.status != TicketLineStatus.CANCELLED,
    ).order_by(TicketLine.id)))
    subtotal = sum(line.line_total_cents for line in active_lines)
    if subtotal <= 0:
        raise InvalidBusinessDataError("El ticket no tiene subtotal divisible.")
    allocations = {
        line.id: (line.line_total_cents * ticket.total_cents) // subtotal
        for line in active_lines
    }
    remainder = ticket.total_cents - sum(allocations.values())
    for line in active_lines[:remainder]:
        allocations[line.id] += 1
    split = TicketSplit(
        ticket_id=ticket.id, name=name.strip() or "Cuenta", split_type=TicketSplitType.BY_LINES,
        amount_cents=sum(allocations[line.id] for line in lines), status=TicketSplitStatus.OPEN,
        created_by_employee_id=employee_id,
    )
    db.add(split)
    db.flush()
    for line in lines:
        db.add(TicketSplitLine(ticket_split_id=split.id, ticket_line_id=line.id, amount_cents=allocations[line.id]))
    db.add(AuditEvent(
        event_type=audit_event("TICKET_SPLIT_CREATED"), entity_type="TicketSplit", entity_id=split.id,
        actor_employee_id=employee_id, cash_shift_id=ticket.cash_shift_id, ticket_id=ticket.id,
        after_snapshot=json.dumps({"mode": "lines", "ticket_line_ids": sorted(unique_ids)}),
    ))
    db.flush()
    return split


def list_splits(db: Session, ticket_id: int) -> list[TicketSplit]:
    if db.get(Ticket, ticket_id) is None:
        raise EntityNotFoundError("El ticket no existe.")
    return list(db.scalars(select(TicketSplit).options(selectinload(TicketSplit.lines)).where(TicketSplit.ticket_id == ticket_id).order_by(TicketSplit.id)))


def pay_split(db: Session, split_id: int, employee_id: int, payment_method_id: int, amount_cents: int, received_cents: int | None, reference: str | None) -> Payment:
    """Registra un pago asociado a una división y reutiliza el cierre transaccional del ticket."""
    split = db.get(TicketSplit, split_id)
    if split is None:
        raise EntityNotFoundError("La división no existe.")
    if split.status != TicketSplitStatus.OPEN:
        raise BusinessConflictError("La división no está abierta.")
    paid = int(db.scalar(select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
        Payment.ticket_split_id == split.id, Payment.status == ActiveStatus.ACTIVE,
    )) or 0)
    if paid + amount_cents > split.amount_cents:
        raise InvalidBusinessDataError("El pago excede el saldo de la división.")
    payment = create_payment(db, split.ticket_id, employee_id, payment_method_id, amount_cents, received_cents, reference, ticket_split_id=split.id)
    if paid + amount_cents == split.amount_cents:
        split.status = TicketSplitStatus.PAID
        split.closed_at = datetime.utcnow()
    db.add(AuditEvent(
        event_type=audit_event("TICKET_SPLIT_PAYMENT"), entity_type="TicketSplit", entity_id=split.id,
        actor_employee_id=employee_id, cash_shift_id=split.ticket.cash_shift_id, ticket_id=split.ticket_id,
        after_snapshot=json.dumps({"payment_id": payment.id, "amount_cents": amount_cents}),
    ))
    db.flush()
    return payment

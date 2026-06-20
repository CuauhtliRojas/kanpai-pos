import json
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditEvent,
    CashExpense,
    CashShift,
    InventoryMovement,
    Payment,
    PrintJob,
    StationOrder,
    Ticket,
    TicketLine,
)
from app.services.cash_shift_service import get_cash_shift_summary
from app.services.exceptions import EntityNotFoundError, InvalidBusinessDataError
from app.services.reporting_service import _date_conditions, parse_date_range


def audit_event_to_dict(event: AuditEvent) -> dict[str, Any]:
    """Serializa el evento y deriva metadata de snapshots JSON sin ocultar el original."""
    metadata: dict[str, Any] = {}
    for public_name, raw_value in (
        ("before", event.before_snapshot),
        ("after", event.after_snapshot),
    ):
        if raw_value is None:
            continue
        try:
            metadata[public_name] = json.loads(raw_value)
        except (json.JSONDecodeError, TypeError):
            metadata[public_name] = raw_value
    return {
        "id": event.id,
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "actor_employee_id": event.actor_employee_id,
        "ticket_id": event.ticket_id,
        "cash_shift_id": event.cash_shift_id,
        "created_at": event.created_at,
        "before_snapshot": event.before_snapshot,
        "after_snapshot": event.after_snapshot,
        "reason": event.reason,
        "metadata": metadata or None,
    }


def list_audit_events(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    event_type: str | None = None,
    actor_employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Lista eventos filtrados en orden descendente con paginación estable."""
    if limit < 1 or limit > 500:
        raise InvalidBusinessDataError("limit debe estar entre 1 y 500.")
    if offset < 0:
        raise InvalidBusinessDataError("offset no puede ser negativo.")
    conditions = _date_conditions(
        AuditEvent.created_at, parse_date_range(date_from, date_to)
    )
    if entity_type is not None:
        conditions.append(AuditEvent.entity_type == entity_type)
    if entity_id is not None:
        conditions.append(AuditEvent.entity_id == entity_id)
    if event_type is not None:
        conditions.append(AuditEvent.event_type == event_type)
    if actor_employee_id is not None:
        conditions.append(AuditEvent.actor_employee_id == actor_employee_id)
    total = int(db.scalar(select(func.count(AuditEvent.id)).where(*conditions)) or 0)
    events = db.scalars(
        select(AuditEvent)
        .where(*conditions)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [audit_event_to_dict(event) for event in events],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_ticket_audit(db: Session, ticket_id: int) -> dict:
    """Reconstruye el ciclo observable de un ticket desde todas sus tablas relacionadas."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    lines = db.scalars(
        select(TicketLine)
        .where(TicketLine.ticket_id == ticket_id)
        .order_by(TicketLine.id)
    ).all()
    line_ids = [line.id for line in lines]
    station_orders = db.scalars(
        select(StationOrder)
        .options(selectinload(StationOrder.lines))
        .where(StationOrder.ticket_id == ticket_id)
        .order_by(StationOrder.id)
    ).all()
    movements = []
    if line_ids:
        movements = db.scalars(
            select(InventoryMovement)
            .where(InventoryMovement.ticket_line_id.in_(line_ids))
            .order_by(InventoryMovement.id)
        ).all()
    events = db.scalars(
        select(AuditEvent)
        .where(
            or_(
                AuditEvent.ticket_id == ticket_id,
                (AuditEvent.entity_type == "Ticket")
                & (AuditEvent.entity_id == ticket_id),
            )
        )
        .order_by(AuditEvent.created_at, AuditEvent.id)
    ).all()
    return {
        "ticket": ticket,
        "lines": lines,
        "payments": db.scalars(
            select(Payment).where(Payment.ticket_id == ticket_id).order_by(Payment.id)
        ).all(),
        "station_orders": station_orders,
        "print_jobs": db.scalars(
            select(PrintJob)
            .where(PrintJob.ticket_id == ticket_id)
            .order_by(PrintJob.id)
        ).all(),
        "inventory_movements": movements,
        "audit_events": [audit_event_to_dict(event) for event in events],
    }


def get_cash_shift_audit(db: Session, cash_shift_id: int) -> dict:
    """Reconstruye el corte, sus flujos monetarios, impresiones y eventos asociados."""
    cash_shift = db.get(CashShift, cash_shift_id)
    if cash_shift is None:
        raise EntityNotFoundError("El corte de caja no existe.")
    tickets = db.scalars(
        select(Ticket).where(Ticket.cash_shift_id == cash_shift_id).order_by(Ticket.id)
    ).all()
    ticket_ids = [ticket.id for ticket in tickets]
    print_condition = PrintJob.cash_shift_id == cash_shift_id
    event_condition = or_(
        AuditEvent.cash_shift_id == cash_shift_id,
        (AuditEvent.entity_type == "CashShift")
        & (AuditEvent.entity_id == cash_shift_id),
    )
    if ticket_ids:
        print_condition = or_(print_condition, PrintJob.ticket_id.in_(ticket_ids))
        event_condition = or_(event_condition, AuditEvent.ticket_id.in_(ticket_ids))
    events = db.scalars(
        select(AuditEvent)
        .where(event_condition)
        .order_by(AuditEvent.created_at, AuditEvent.id)
    ).all()
    return {
        "cash_shift": cash_shift,
        "summary": get_cash_shift_summary(db, cash_shift_id),
        "tickets": tickets,
        "payments": db.scalars(
            select(Payment)
            .where(Payment.cash_shift_id == cash_shift_id)
            .order_by(Payment.id)
        ).all(),
        "expenses": db.scalars(
            select(CashExpense)
            .where(CashExpense.cash_shift_id == cash_shift_id)
            .order_by(CashExpense.id)
        ).all(),
        "print_jobs": db.scalars(
            select(PrintJob).where(print_condition).order_by(PrintJob.id)
        ).all(),
        "audit_events": [audit_event_to_dict(event) for event in events],
    }

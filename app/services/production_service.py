from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.constants import ProductionOrderStatus, audit_event
from app.models import AuditEvent, StationOrder, Ticket
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.permission_service import get_active_employee
from app.services.reporting_service import _date_conditions, parse_date_range


def list_station_orders(
    db: Session,
    station_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[StationOrder]:
    """List production orders with lines and optional operational filters."""
    conditions = _date_conditions(
        StationOrder.created_at, parse_date_range(date_from, date_to)
    )
    if station_id is not None:
        conditions.append(StationOrder.station_id == station_id)
    if status is not None:
        conditions.append(StationOrder.status == status)
    return list(
        db.scalars(
            select(StationOrder)
            .options(selectinload(StationOrder.lines))
            .where(*conditions)
            .order_by(StationOrder.created_at, StationOrder.id)
        )
    )


def transition_station_order(
    db: Session, station_order_id: int, employee_id: int, action: str
) -> StationOrder:
    """Apply one strict production transition and persist actor/timestamp/audit."""
    transitions = {
        "receive": (
            ProductionOrderStatus.QUEUED,
            ProductionOrderStatus.RECEIVED,
            "received_at",
            "received_by_employee_id",
            "PRODUCTION_ORDER_RECEIVED",
        ),
        "start": (
            ProductionOrderStatus.RECEIVED,
            ProductionOrderStatus.IN_PREPARATION,
            "started_at",
            "started_by_employee_id",
            "PRODUCTION_ORDER_STARTED",
        ),
        "complete": (
            ProductionOrderStatus.IN_PREPARATION,
            ProductionOrderStatus.COMPLETED,
            "completed_at",
            "completed_by_employee_id",
            "PRODUCTION_ORDER_COMPLETED",
        ),
        "deliver": (
            ProductionOrderStatus.COMPLETED,
            ProductionOrderStatus.DELIVERED,
            "delivered_at",
            "delivered_by_employee_id",
            "PRODUCTION_ORDER_DELIVERED",
        ),
    }
    expected, target, timestamp_field, actor_field, event_key = transitions[action]
    employee = get_active_employee(db, employee_id)
    order = db.get(StationOrder, station_order_id)
    if order is None:
        raise EntityNotFoundError("La orden de produccion no existe.")
    if order.status != expected:
        raise BusinessConflictError(
            f"La orden debe estar en estado {expected} para esta operacion."
        )
    before = order.status
    order.status = target
    setattr(order, timestamp_field, datetime.utcnow())
    setattr(order, actor_field, employee.id)
    ticket = db.get(Ticket, order.ticket_id)
    db.add(
        AuditEvent(
            event_type=audit_event(event_key),
            entity_type="Orden de produccion",
            entity_id=order.id,
            actor_employee_id=employee.id,
            cash_shift_id=ticket.cash_shift_id if ticket else None,
            ticket_id=order.ticket_id,
            before_snapshot=before,
            after_snapshot=target,
        )
    )
    db.flush()
    db.refresh(order, attribute_names=["lines"])
    return order

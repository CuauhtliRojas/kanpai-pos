from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.cash_shift import CashShiftResponse, CashShiftSummaryResponse
from app.schemas.expense import CashExpenseResponse
from app.schemas.discount import DiscountResponse
from app.schemas.modification import TicketLineModificationResponse
from app.schemas.order import StationOrderResponse
from app.schemas.payment import PaymentResponse
from app.schemas.print_job import PrintJobResponse
from app.schemas.ticket import TicketLineResponse, TicketResponse


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    entity_type: str
    entity_id: int
    actor_employee_id: int | None
    ticket_id: int | None
    cash_shift_id: int | None
    created_at: datetime
    before_snapshot: str | None
    after_snapshot: str | None
    reason: str | None
    metadata: dict[str, Any] | None = None


class AuditEventPage(BaseModel):
    items: list[AuditEventResponse]
    total: int
    limit: int
    offset: int


class AuditInventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    inventory_item_id: int
    movement_type: str
    quantity_base: Decimal
    signed_quantity_base: Decimal
    ticket_line_id: int | None
    source_type: str | None
    source_id: int | None
    reason: str | None
    registered_by_employee_id: int
    created_at: datetime


class TicketAuditResponse(BaseModel):
    ticket: TicketResponse
    lines: list[TicketLineResponse]
    payments: list[PaymentResponse]
    discounts: list[DiscountResponse]
    modifications: list[TicketLineModificationResponse]
    station_orders: list[StationOrderResponse]
    print_jobs: list[PrintJobResponse]
    inventory_movements: list[AuditInventoryMovementResponse]
    audit_events: list[AuditEventResponse]


class CashShiftAuditResponse(BaseModel):
    cash_shift: CashShiftResponse
    summary: CashShiftSummaryResponse
    tickets: list[TicketResponse]
    payments: list[PaymentResponse]
    expenses: list[CashExpenseResponse]
    print_jobs: list[PrintJobResponse]
    audit_events: list[AuditEventResponse]

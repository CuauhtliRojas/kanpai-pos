from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.discount import DiscountResponse
from app.schemas.order import StationOrderResponse
from app.schemas.print_job import PrintJobHistoryItem
from app.schemas.split import TicketSplitResponse
from app.schemas.ticket import TicketResponse, VariantSelectionResponse


class TicketHistoryItem(BaseModel):
    id: int
    folio: str
    table_id: int
    table_name: str
    cash_shift_id: int
    status: str
    payment_status: str
    opened_at: datetime
    paid_at: datetime | None
    cancelled_at: datetime | None
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int
    line_count: int
    payment_count: int
    print_job_count: int
    payment_method_summary: str | None
    latest_print_job_id: int | None
    latest_ticket_print_job_id: int | None
    can_reprint_ticket: bool


class TicketHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TicketHistoryItem]


class TicketReadonlyTable(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_code: str
    display_name: str
    buzzer_number: int | None


class TicketReadonlyLineNote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    note_type: str
    note: str
    created_at: datetime


class TicketReadonlyLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    parent_ticket_line_id: int | None
    product_id: int
    line_type: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    product_name_snapshot: str
    product_sku_snapshot: str | None
    note: str | None
    status: str
    cancel_reason: str | None
    created_at: datetime
    variant_selections: list[VariantSelectionResponse]
    notes: list[TicketReadonlyLineNote]


class TicketReadonlyPayment(BaseModel):
    id: int
    folio: str
    ticket_split_id: int | None
    payment_method_id: int
    payment_method_name: str
    amount_cents: int
    received_cents: int | None
    change_cents: int
    reference: str | None
    status: str
    cancelled_at: datetime | None
    created_at: datetime


class TicketReadonlyResponse(BaseModel):
    ticket: TicketResponse
    table: TicketReadonlyTable
    lines: list[TicketReadonlyLine]
    discounts: list[DiscountResponse]
    payments: list[TicketReadonlyPayment]
    splits: list[TicketSplitResponse]
    print_jobs: list[PrintJobHistoryItem]
    station_orders: list[StationOrderResponse]
    audit_event_count: int
    can_reprint_ticket: bool
    can_reprint_commands: bool
    is_readonly: bool = True

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketOpenRequest(BaseModel):
    employee_id: int
    guest_count: int = 1
    waiter_employee_id: int | None = None
    note: str | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    cash_shift_id: int
    table_id: int
    opened_by_employee_id: int
    waiter_employee_id: int | None
    guest_count: int
    status: str
    payment_status: str
    note: str | None
    opened_at: datetime
    billing_started_at: datetime | None
    paid_at: datetime | None
    inventory_consumed_at: datetime | None
    closed_by_employee_id: int | None
    cancelled_by_employee_id: int | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    subtotal_cents: int
    discount_cents: int
    total_cents: int


class VariantSelectionRequest(BaseModel):
    variant_group_id: int
    variant_option_id: int
    quantity: int = 1


class VariantSelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    variant_group_id: int
    variant_option_id: int
    group_name: str
    quantity: int
    price_delta_cents_snapshot: int
    name_snapshot: str
    sku_snapshot: str | None
    station_id_snapshot: int | None


class TicketLineCreateRequest(BaseModel):
    product_id: int
    employee_id: int
    quantity: int = 1
    note: str | None = None
    variant_selections: list[VariantSelectionRequest] = []


class TicketLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    parent_ticket_line_id: int | None
    package_id: int | None
    package_item_id: int | None
    product_id: int
    line_type: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    price_mode: str
    product_name_snapshot: str
    product_sku_snapshot: str | None
    category_id_snapshot: int | None
    station_id_snapshot: int | None
    note: str | None
    status: str
    created_by_employee_id: int
    cancelled_by_employee_id: int | None
    cancel_reason: str | None
    cancelled_at: datetime | None
    variant_selections: list[VariantSelectionResponse] = []


class TicketTotalsResponse(BaseModel):
    subtotal_cents: int
    discount_cents: int
    total_cents: int


class TicketLinesCreatedResponse(BaseModel):
    ticket_id: int
    lines_created: list[TicketLineResponse]
    ticket_totals: TicketTotalsResponse

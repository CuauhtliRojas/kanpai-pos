from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EqualSplitRequest(BaseModel):
    employee_id: int
    parts: int


class ByLinesSplitRequest(BaseModel):
    employee_id: int
    name: str
    ticket_line_ids: list[int]


class SplitPaymentRequest(BaseModel):
    employee_id: int
    payment_method_id: int
    amount_cents: int
    received_cents: int | None = None
    reference: str | None = None


class TicketSplitLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_line_id: int
    amount_cents: int


class TicketSplitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    name: str
    split_type: str
    parts: int | None
    part_number: int | None
    amount_cents: int
    status: str
    created_by_employee_id: int
    created_at: datetime
    closed_at: datetime | None
    lines: list[TicketSplitLineResponse] = []


class SplitPaymentResponse(BaseModel):
    payment_id: int
    split: TicketSplitResponse
    change_cents: int
    ticket_closed: bool


class CancelSplitsRequest(BaseModel):
    employee_id: int
    reason: str | None = None


class CancelSplitsResponse(BaseModel):
    cancelled_count: int
    ticket_id: int

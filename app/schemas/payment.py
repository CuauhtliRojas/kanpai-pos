from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.ticket import TicketResponse


class StartPaymentRequest(BaseModel):
    employee_id: int


class PaymentCreateRequest(BaseModel):
    employee_id: int
    payment_method_id: int
    amount_cents: int
    received_cents: int | None = None
    reference: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    ticket_id: int
    cash_shift_id: int
    payment_method_id: int
    cashier_employee_id: int
    amount_cents: int
    received_cents: int | None
    change_cents: int
    reference: str | None
    status: str
    cancelled_by_employee_id: int | None
    cancel_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime


class PaymentCreateResponse(BaseModel):
    payment: PaymentResponse
    ticket: TicketResponse
    total_paid_cents: int
    remaining_cents: int
    closed: bool


class PaymentSummaryResponse(BaseModel):
    ticket_id: int
    payments: list[PaymentResponse]
    total_paid_cents: int
    remaining_cents: int
    closed: bool

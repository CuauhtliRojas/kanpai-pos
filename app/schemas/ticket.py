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
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int

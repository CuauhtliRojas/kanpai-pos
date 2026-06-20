from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.print_job import PrintJobResponse


class CashShiftOpenRequest(BaseModel):
    employee_id: int
    opening_cash_cents: int


class CashShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    status: str
    opened_by_employee_id: int
    opened_at: datetime
    opening_cash_cents: int
    closed_by_employee_id: int | None
    closed_at: datetime | None
    declared_cash_cents: int | None
    expected_cash_cents: int | None
    cash_difference_cents: int | None
    closing_note: str | None


class CashShiftSummaryResponse(BaseModel):
    cash_shift_id: int
    folio: str
    status: str
    opened_at: datetime
    opening_cash_cents: int
    total_sales_cents: int
    total_paid_cents: int
    total_cash_cents: int
    total_card_cents: int
    total_transfer_cents: int
    total_expenses_cents: int
    expected_cash_cents: int
    ticket_count: int
    paid_ticket_count: int
    cancelled_ticket_count: int
    active_expense_count: int
    pending_print_jobs_count: int


class CashShiftCloseRequest(BaseModel):
    employee_id: int
    declared_cash_cents: int
    note: str | None = None
    allow_pending_print_jobs: bool = True


class CashShiftCloseResponse(BaseModel):
    cash_shift: CashShiftResponse
    summary: CashShiftSummaryResponse
    print_job: PrintJobResponse
    closed: bool

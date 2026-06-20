from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CashExpenseCreateRequest(BaseModel):
    employee_id: int
    amount_cents: int
    description: str
    category: str | None = None
    payment_method_id: int | None = None
    note: str | None = None


class CashExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    cash_shift_id: int
    registered_by_employee_id: int
    amount_cents: int
    description: str
    category: str | None
    payment_method_id: int | None
    note: str | None
    status: str
    created_at: datetime

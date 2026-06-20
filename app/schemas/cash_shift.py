from datetime import datetime

from pydantic import BaseModel, ConfigDict


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

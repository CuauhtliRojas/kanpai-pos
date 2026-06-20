from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DiscountCreateRequest(BaseModel):
    employee_id: int
    discount_type: str
    amount_cents: int | None = None
    percent_bps: int | None = None
    reason: str
    is_courtesy: bool = False


class DiscountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    discount_type: str = Field(validation_alias="discount_source")
    amount_cents: int
    percent_bps: int | None
    reason: str | None
    is_courtesy: bool
    authorized_by_employee_id: int | None
    created_by_employee_id: int
    created_at: datetime

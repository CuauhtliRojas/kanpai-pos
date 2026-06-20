from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductionActionRequest(BaseModel):
    employee_id: int


class ProductionOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_line_id: int
    quantity: int
    product_name_snapshot: str
    note_snapshot: str | None
    line_action: str


class ProductionOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    station_id: int
    folio: str
    status: str
    received_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    received_by_employee_id: int | None
    started_by_employee_id: int | None
    completed_by_employee_id: int | None
    delivered_by_employee_id: int | None
    created_at: datetime
    lines: list[ProductionOrderLineResponse]

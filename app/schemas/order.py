from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SendRoundRequest(BaseModel):
    employee_id: int


class SendRoundResponse(BaseModel):
    ticket_id: int
    command_batch_id: int
    round_number: int
    station_orders_created: int
    print_jobs_created: int
    lines_sent: int


class StationOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_line_id: int
    quantity: int
    product_name_snapshot: str
    note_snapshot: str | None
    line_action: str


class StationOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    command_batch_id: int
    ticket_id: int
    station_id: int
    folio: str
    status: str
    created_at: datetime
    lines: list[StationOrderLineResponse]


class PrintJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    job_type: str
    printer_id: int
    printer_key_snapshot: str
    ticket_id: int | None
    cash_shift_id: int | None
    station_order_id: int | None
    command_batch_id: int | None
    content_snapshot: str
    status: str
    attempts: int
    idempotency_key: str
    created_at: datetime

from pydantic import BaseModel

from app.schemas.ticket import TicketLineResponse, TicketResponse


class TicketLineCancelRequest(BaseModel):
    employee_id: int
    reason: str | None = None


class TicketCancelRequest(BaseModel):
    employee_id: int
    reason: str | None = None


class TicketLineCancelResponse(BaseModel):
    line: TicketLineResponse
    ticket: TicketResponse
    print_jobs_created: int


class TicketCancelResponse(BaseModel):
    ticket: TicketResponse
    lines_cancelled: int
    payments_cancelled: int
    print_jobs_created: int
    table_released: bool

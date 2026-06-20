from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketLineModifyRequest(BaseModel):
    employee_id: int
    note: str


class TicketLineModificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_line_id: int
    ticket_id: int
    note: str
    created_by_employee_id: int
    created_at: datetime
    print_job_id: int | None

from typing import Literal

from pydantic import BaseModel

PreflightStatus = Literal["OK", "WARNING", "ERROR"]


class PreflightCheck(BaseModel):
    key: str
    status: PreflightStatus
    message: str


class PreflightSummary(BaseModel):
    active_cash_shifts: int
    open_tickets: int
    in_payment_tickets: int
    pending_print_jobs: int
    failed_print_jobs: int
    active_stock_alerts: int


class PreflightResponse(BaseModel):
    status: PreflightStatus
    database: str
    checks: list[PreflightCheck]
    summary: PreflightSummary

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    claimed_at: datetime | None
    claimed_by: str | None
    printed_at: datetime | None
    failed_at: datetime | None
    last_error: str | None
    next_retry_at: datetime | None
    idempotency_key: str
    created_at: datetime


class PrintJobClaimRequest(BaseModel):
    printer_key: str
    worker_id: str


class PrintJobWorkerRequest(BaseModel):
    worker_id: str


class PrintJobFailedRequest(PrintJobWorkerRequest):
    error_message: str


class PrintJobRetryRequest(BaseModel):
    printer_key: str | None = None
    reset_all: bool = False


class PrintJobClaimResponse(BaseModel):
    job: PrintJobResponse | None


class PrintJobRetryResponse(BaseModel):
    jobs_requeued: int

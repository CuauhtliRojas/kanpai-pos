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


class PrintJobHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folio: str
    job_type: str
    printer_id: int
    printer_key: str
    ticket_id: int | None
    cash_shift_id: int | None
    station_order_id: int | None
    command_batch_id: int | None
    status: str
    attempts: int
    claimed_at: datetime | None
    printed_at: datetime | None
    failed_at: datetime | None
    last_error: str | None
    next_retry_at: datetime | None
    created_at: datetime


class PrinterResponse(BaseModel):
    id: int
    key: str
    display_name: str
    role: str
    station_id: int | None
    station_name: str | None
    enabled: bool
    physical_name_hint: str | None
    paper_width_mm: int
    supports_cut: bool
    is_cash_register_printer: bool
    last_job_at: datetime | None
    pending_count: int
    failed_count: int
    status: str


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

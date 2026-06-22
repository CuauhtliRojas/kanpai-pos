from pydantic import BaseModel, ConfigDict


class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    table_code: str
    display_name: str
    status_cache: str
    active: bool
    active_ticket_id: int | None = None
    active_ticket_folio: str | None = None
    active_ticket_status: str | None = None
    active_ticket_total_cents: int | None = None
    active_ticket_payment_status: str | None = None

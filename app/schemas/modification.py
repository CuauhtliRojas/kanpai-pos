from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.ticket import VariantSelectionRequest


class TicketLineModifyRequest(BaseModel):
    employee_id: int
    note: str | None = None
    quantity: int | None = None
    variant_selections: list[VariantSelectionRequest] | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TicketLineModifyRequest":
        has_change = (
            self.note is not None
            or self.quantity is not None
            or self.variant_selections is not None
        )
        if not has_change:
            raise ValueError("Se requiere al menos nota, cantidad o preparación.")
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("La cantidad debe ser un entero positivo.")
        return self


class TicketLineModificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_line_id: int
    ticket_id: int
    note: str
    created_by_employee_id: int
    created_at: datetime
    print_job_id: int | None

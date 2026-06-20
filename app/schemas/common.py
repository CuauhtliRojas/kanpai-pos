from pydantic import BaseModel


class BusinessErrorResponse(BaseModel):
    """Payload público para errores de reglas de negocio."""

    detail: str

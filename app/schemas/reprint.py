from pydantic import BaseModel


class ReprintRequest(BaseModel):
    employee_id: int
    reason: str

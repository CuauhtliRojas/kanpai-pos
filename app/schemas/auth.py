from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EmployeeAuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    full_name: str
    pos_alias: str | None


class PinLoginRequest(BaseModel):
    employee_code: str
    pin: str


class PinLoginResponse(BaseModel):
    employee: EmployeeAuthResponse
    session_token: str
    expires_at: datetime


class LogoutRequest(BaseModel):
    session_token: str


class LogoutResponse(BaseModel):
    status: str


class MeResponse(BaseModel):
    employee: EmployeeAuthResponse
    roles: list[str]
    permissions: list[str]

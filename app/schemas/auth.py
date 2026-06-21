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


class PermissionResponse(BaseModel):
    id: int
    permission_key: str
    description: str | None
    active: bool


class RoleResponse(BaseModel):
    id: int
    role_key: str
    name: str
    active: bool
    permissions: list[PermissionResponse] = []


class EmployeeDetailResponse(BaseModel):
    id: int
    employee_code: str
    full_name: str
    pos_alias: str | None
    active: bool
    sync_status: str
    pin_enabled: bool
    last_login_at: datetime | None
    roles: list[RoleResponse]


class EmployeePermissionsResponse(BaseModel):
    employee_id: int
    roles: list[RoleResponse]
    permissions: list[PermissionResponse]

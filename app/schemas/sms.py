from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class SmsTestRequest(BaseModel):
    employee_id: int
    msisdn: str
    message: str
    confirm: Literal["SEND_SMS_TEST"]


class SmsNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stock_alert_id: int | None
    employee_id: int | None
    msisdn: str
    message: str
    status: str
    test_mode: bool
    response_payload: str | None
    error: str | None
    created_at: datetime
    sent_at: datetime | None

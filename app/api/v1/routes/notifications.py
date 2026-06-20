from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sms import SmsNotificationResponse, SmsTestRequest
from app.services.exceptions import BusinessError, PermissionDeniedError
from app.services.sms_service import list_sms, send_sms

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/sms", response_model=list[SmsNotificationResponse])
def sms_history(db: Session = Depends(get_db)):
    return [SmsNotificationResponse.model_validate(item) for item in list_sms(db)]


@router.post("/sms/test", response_model=SmsNotificationResponse, status_code=201)
def sms_test(payload: SmsTestRequest, db: Session = Depends(get_db)):
    try:
        item = send_sms(db, employee_id=payload.employee_id, msisdn=payload.msisdn, message=payload.message)
        response = SmsNotificationResponse.model_validate(item)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise HTTPException(status_code=403 if isinstance(error, PermissionDeniedError) else 400, detail=str(error)) from None

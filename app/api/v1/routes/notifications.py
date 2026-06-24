from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.security import (
    SessionIdentity,
    require_session_permission,
    require_support_permission,
)
from app.domain.constants import PermissionKey
from app.schemas.sms import SmsNotificationResponse, SmsTestRequest
from app.services.exceptions import BusinessError, PermissionDeniedError
from app.services.sms_service import list_sms, send_sms

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "/sms",
    response_model=list[SmsNotificationResponse],
    dependencies=[Depends(require_support_permission)],
    tags=["notifications", "admin-support"],
    summary="Consultar historial SMS (admin/soporte)",
    description="Historial protegido para diagnóstico; no envía mensajes.",
)
def sms_history(db: Session = Depends(get_db)):
    return [SmsNotificationResponse.model_validate(item) for item in list_sms(db)]


@router.post(
    "/sms/test",
    response_model=SmsNotificationResponse,
    status_code=201,
    dependencies=[Depends(require_session_permission(PermissionKey.SMS_SEND))],
    tags=["notifications", "admin-support"],
    summary="Enviar prueba SMS autorizada (admin/soporte)",
    description="Requiere SMS_SEND y confirm='SEND_SMS_TEST'. Puede contactar al proveedor si SMS_ENABLED=true.",
)
def sms_test(
    payload: SmsTestRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(
        require_session_permission(PermissionKey.SMS_SEND)
    ),
):
    try:
        item = send_sms(
            db,
            employee_id=identity.employee.id,
            msisdn=payload.msisdn,
            message=payload.message,
        )
        response = SmsNotificationResponse.model_validate(item)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise HTTPException(status_code=403 if isinstance(error, PermissionDeniedError) else 400, detail=str(error)) from None

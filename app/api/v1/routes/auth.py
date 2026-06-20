from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LogoutRequest, LogoutResponse, MeResponse, PinLoginRequest, PinLoginResponse
from app.services.auth_service import get_session_identity, login_with_pin, logout
from app.services.exceptions import BusinessError, EntityNotFoundError

router = APIRouter(prefix="/auth", tags=["auth"])


def _error(error: BusinessError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND if isinstance(error, EntityNotFoundError) else status.HTTP_401_UNAUTHORIZED, detail=str(error))


@router.post("/login-pin", response_model=PinLoginResponse)
def login_pin(payload: PinLoginRequest, db: Session = Depends(get_db)) -> PinLoginResponse:
    try:
        session = login_with_pin(db, payload.employee_code, payload.pin)
        response = PinLoginResponse(employee=session.employee, session_token=session.session_token, expires_at=session.expires_at)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _error(error) from None


@router.post("/logout", response_model=LogoutResponse)
def logout_endpoint(payload: LogoutRequest, db: Session = Depends(get_db)) -> LogoutResponse:
    try:
        session = logout(db, payload.session_token)
        db.commit()
        return LogoutResponse(status=session.status)
    except BusinessError as error:
        db.rollback()
        raise _error(error) from None


@router.get("/me", response_model=MeResponse)
def me(
    x_kanpai_session: str | None = Header(default=None, alias="X-Kanpai-Session"),
    session_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MeResponse:
    token = x_kanpai_session or session_token
    if not token:
        raise HTTPException(status_code=401, detail="Falta X-Kanpai-Session.")
    try:
        employee, roles, permissions = get_session_identity(db, token)
        db.commit()
        return MeResponse(employee=employee, roles=roles, permissions=permissions)
    except BusinessError as error:
        db.rollback()
        raise _error(error) from None

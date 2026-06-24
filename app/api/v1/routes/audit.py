from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.security import require_admin_read_permission
from app.core.database import get_db
from app.schemas.audit import (
    AuditEventPage,
    CashShiftAuditResponse,
    TicketAuditResponse,
)
from app.services.audit_query_service import (
    get_cash_shift_audit,
    get_ticket_audit,
    list_audit_events,
)
from app.services.exceptions import EntityNotFoundError, InvalidBusinessDataError

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_admin_read_permission)],
)


def _http_error(error: Exception) -> HTTPException:
    """Mapea fallos esperados de consulta a respuestas 400/404 estables."""
    code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, EntityNotFoundError)
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=code, detail=str(error))


def _parse_pagination(limit: str, offset: str) -> tuple[int, int]:
    """Valida paginación como HTTP 400, incluido texto no numérico."""
    try:
        parsed_limit, parsed_offset = int(limit), int(offset)
    except ValueError as error:
        raise InvalidBusinessDataError("limit y offset deben ser enteros.") from error
    return parsed_limit, parsed_offset


@router.get("/events", response_model=AuditEventPage)
def list_audit_events_endpoint(
    entity_type: str | None = None,
    entity_id: int | None = None,
    event_type: str | None = None,
    actor_employee_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: str = "100",
    offset: str = "0",
    db: Session = Depends(get_db),
) -> AuditEventPage:
    try:
        parsed_limit, parsed_offset = _parse_pagination(limit, offset)
        return AuditEventPage.model_validate(
            list_audit_events(
                db,
                entity_type=entity_type,
                entity_id=entity_id,
                event_type=event_type,
                actor_employee_id=actor_employee_id,
                date_from=date_from,
                date_to=date_to,
                limit=parsed_limit,
                offset=parsed_offset,
            )
        )
    except InvalidBusinessDataError as error:
        raise _http_error(error) from None


@router.get("/tickets/{ticket_id}", response_model=TicketAuditResponse)
def get_ticket_audit_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> TicketAuditResponse:
    try:
        return TicketAuditResponse.model_validate(get_ticket_audit(db, ticket_id))
    except EntityNotFoundError as error:
        raise _http_error(error) from None


@router.get("/cash-shifts/{cash_shift_id}", response_model=CashShiftAuditResponse)
def get_cash_shift_audit_endpoint(
    cash_shift_id: int, db: Session = Depends(get_db)
) -> CashShiftAuditResponse:
    try:
        return CashShiftAuditResponse.model_validate(
            get_cash_shift_audit(db, cash_shift_id)
        )
    except EntityNotFoundError as error:
        raise _http_error(error) from None

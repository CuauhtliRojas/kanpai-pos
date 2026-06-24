from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.security import SessionIdentity, require_session
from app.core.database import get_db
from app.domain.constants import TicketStatus
from app.schemas.split import ByLinesSplitRequest, CancelSplitsRequest, CancelSplitsResponse, EqualSplitRequest, SplitPaymentRequest, SplitPaymentResponse, TicketSplitResponse
from app.services.exceptions import BusinessConflictError, BusinessError, EntityNotFoundError, InvalidBusinessDataError
from app.services.split_service import cancel_ticket_splits, create_equal_splits, create_lines_split, list_splits, pay_split

router = APIRouter(prefix="/pos", tags=["pos-splits"], dependencies=[Depends(require_session)])


def _http(error: BusinessError) -> HTTPException:
    if isinstance(error, EntityNotFoundError):
        code = 404
    elif isinstance(error, InvalidBusinessDataError):
        code = 400
    elif isinstance(error, BusinessConflictError):
        code = 409
    else:
        code = 400
    return HTTPException(status_code=code, detail=str(error))


@router.post("/tickets/{ticket_id}/splits/equal", response_model=list[TicketSplitResponse], status_code=201)
def equal(
    ticket_id: int,
    payload: EqualSplitRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    try:
        result = create_equal_splits(db, ticket_id, identity.employee.id, payload.parts)
        db.commit()
        return [TicketSplitResponse.model_validate(item) for item in result]
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None


@router.post("/tickets/{ticket_id}/splits/by-lines", response_model=TicketSplitResponse, status_code=201)
def by_lines(
    ticket_id: int,
    payload: ByLinesSplitRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    try:
        result = create_lines_split(db, ticket_id, identity.employee.id, payload.name, payload.ticket_line_ids)
        db.commit()
        return TicketSplitResponse.model_validate(result)
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None


@router.get("/tickets/{ticket_id}/splits", response_model=list[TicketSplitResponse])
def get_all(ticket_id: int, db: Session = Depends(get_db)):
    try:
        return [TicketSplitResponse.model_validate(item) for item in list_splits(db, ticket_id)]
    except BusinessError as error:
        raise _http(error) from None


@router.post("/tickets/{ticket_id}/splits/cancel", response_model=CancelSplitsResponse)
def cancel_splits(
    ticket_id: int,
    payload: CancelSplitsRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    try:
        cancelled_count = cancel_ticket_splits(db, ticket_id, identity.employee.id, payload.reason)
        db.commit()
        return CancelSplitsResponse(cancelled_count=cancelled_count, ticket_id=ticket_id)
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None


@router.post("/ticket-splits/{split_id}/payments", response_model=SplitPaymentResponse, status_code=201)
def payment(
    split_id: int,
    payload: SplitPaymentRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    try:
        item = pay_split(db, split_id, identity.employee.id, payload.payment_method_id, payload.amount_cents, payload.received_cents, payload.reference)
        split = item.ticket_split
        response = SplitPaymentResponse(payment_id=item.id, split=TicketSplitResponse.model_validate(split), change_cents=item.change_cents, ticket_closed=item.ticket.status == TicketStatus.PAID)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None

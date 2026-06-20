from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.constants import TicketStatus
from app.schemas.split import ByLinesSplitRequest, EqualSplitRequest, SplitPaymentRequest, SplitPaymentResponse, TicketSplitResponse
from app.services.exceptions import BusinessError, EntityNotFoundError, InvalidBusinessDataError
from app.services.split_service import create_equal_splits, create_lines_split, list_splits, pay_split

router = APIRouter(prefix="/pos", tags=["pos-splits"])


def _http(error: BusinessError) -> HTTPException:
    code = 404 if isinstance(error, EntityNotFoundError) else 400 if isinstance(error, InvalidBusinessDataError) else 409
    return HTTPException(status_code=code, detail=str(error))


@router.post("/tickets/{ticket_id}/splits/equal", response_model=list[TicketSplitResponse], status_code=201)
def equal(ticket_id: int, payload: EqualSplitRequest, db: Session = Depends(get_db)):
    try:
        result = create_equal_splits(db, ticket_id, payload.employee_id, payload.parts)
        db.commit()
        return [TicketSplitResponse.model_validate(item) for item in result]
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None


@router.post("/tickets/{ticket_id}/splits/by-lines", response_model=TicketSplitResponse, status_code=201)
def by_lines(ticket_id: int, payload: ByLinesSplitRequest, db: Session = Depends(get_db)):
    try:
        result = create_lines_split(db, ticket_id, payload.employee_id, payload.name, payload.ticket_line_ids)
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


@router.post("/ticket-splits/{split_id}/payments", response_model=SplitPaymentResponse, status_code=201)
def payment(split_id: int, payload: SplitPaymentRequest, db: Session = Depends(get_db)):
    try:
        item = pay_split(db, split_id, payload.employee_id, payload.payment_method_id, payload.amount_cents, payload.received_cents, payload.reference)
        split = item.ticket_split
        response = SplitPaymentResponse(payment_id=item.id, split=TicketSplitResponse.model_validate(split), change_cents=item.change_cents, ticket_closed=item.ticket.status == TicketStatus.PAID)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _http(error) from None

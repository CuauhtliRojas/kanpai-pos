from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    BusinessErrorResponse,
    CashShiftOpenRequest,
    CashShiftResponse,
    TicketLineCreateRequest,
    TicketLineResponse,
    TicketLinesCreatedResponse,
    TicketOpenRequest,
    TicketResponse,
)
from app.services.cash_shift_service import get_current_cash_shift, open_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    BusinessError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.ticket_service import get_ticket, open_ticket_for_table
from app.services.product_service import add_product_to_ticket, get_ticket_lines

router = APIRouter(prefix="/pos", tags=["pos"])

BUSINESS_ERROR_RESPONSES = {
    400: {"model": BusinessErrorResponse},
    404: {"model": BusinessErrorResponse},
    409: {"model": BusinessErrorResponse},
}


def _to_http_exception(error: BusinessError) -> HTTPException:
    """Convierte errores públicos del dominio a códigos HTTP estables."""
    if isinstance(error, InvalidBusinessDataError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(error, EntityNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, BusinessConflictError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail=str(error))


@router.post(
    "/cash-shifts/open",
    response_model=CashShiftResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def open_cash_shift_endpoint(
    payload: CashShiftOpenRequest, db: Session = Depends(get_db)
) -> CashShiftResponse:
    try:
        cash_shift = open_cash_shift(
            db,
            employee_id=payload.employee_id,
            opening_cash_cents=payload.opening_cash_cents,
        )
        db.commit()
        db.refresh(cash_shift)
        return CashShiftResponse.model_validate(cash_shift)
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/cash-shifts/current",
    response_model=CashShiftResponse,
    responses={404: {"model": BusinessErrorResponse}},
)
def get_current_cash_shift_endpoint(
    db: Session = Depends(get_db),
) -> CashShiftResponse:
    cash_shift = get_current_cash_shift(db)
    if cash_shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un corte de caja abierto.",
        )
    return CashShiftResponse.model_validate(cash_shift)


@router.post(
    "/tables/{table_id}/open-ticket",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def open_ticket_for_table_endpoint(
    table_id: int,
    payload: TicketOpenRequest,
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        ticket = open_ticket_for_table(
            db,
            table_id=table_id,
            employee_id=payload.employee_id,
            guest_count=payload.guest_count,
            waiter_employee_id=payload.waiter_employee_id,
            note=payload.note,
        )
        db.commit()
        db.refresh(ticket)
        return TicketResponse.model_validate(ticket)
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    responses={404: {"model": BusinessErrorResponse}},
)
def get_ticket_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> TicketResponse:
    try:
        return TicketResponse.model_validate(get_ticket(db, ticket_id))
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/tickets/{ticket_id}/lines",
    response_model=list[TicketLineResponse],
    responses={404: {"model": BusinessErrorResponse}},
)
def get_ticket_lines_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> list[TicketLineResponse]:
    try:
        return [
            TicketLineResponse.model_validate(line)
            for line in get_ticket_lines(db, ticket_id)
        ]
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/tickets/{ticket_id}/lines",
    response_model=TicketLinesCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def add_product_to_ticket_endpoint(
    ticket_id: int,
    payload: TicketLineCreateRequest,
    db: Session = Depends(get_db),
) -> TicketLinesCreatedResponse:
    try:
        lines = add_product_to_ticket(
            db,
            ticket_id=ticket_id,
            product_id=payload.product_id,
            employee_id=payload.employee_id,
            quantity=payload.quantity,
            note=payload.note,
        )
        ticket = get_ticket(db, ticket_id)
        db.commit()
        return TicketLinesCreatedResponse(
            ticket_id=ticket.id,
            lines_created=[TicketLineResponse.model_validate(line) for line in lines],
            ticket_totals={
                "subtotal_cents": ticket.subtotal_cents,
                "discount_cents": ticket.discount_cents,
                "tax_cents": ticket.tax_cents,
                "total_cents": ticket.total_cents,
            },
        )
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None

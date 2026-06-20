from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import InventoryMovement, Payment, PrintJob, TicketLine
from app.schemas import (
    BusinessErrorResponse,
    CashExpenseCreateRequest,
    CashExpenseResponse,
    CashShiftCloseRequest,
    CashShiftCloseResponse,
    CashShiftOpenRequest,
    CashShiftResponse,
    CashShiftSummaryResponse,
    InventoryMovementResponse,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentResponse,
    PaymentSummaryResponse,
    PrintJobResponse,
    SendRoundRequest,
    SendRoundResponse,
    StationOrderResponse,
    StartPaymentRequest,
    TicketCancelRequest,
    TicketCancelResponse,
    TicketLineCancelRequest,
    TicketLineCancelResponse,
    TicketLineCreateRequest,
    TicketLineResponse,
    TicketLinesCreatedResponse,
    TicketOpenRequest,
    TicketResponse,
)
from app.services.cash_shift_service import (
    close_cash_shift,
    get_cash_shift_summary,
    get_current_cash_shift,
    open_cash_shift,
)
from app.services.exceptions import (
    BusinessConflictError,
    BusinessError,
    EntityNotFoundError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.services.cancellation_service import cancel_ticket, cancel_ticket_line
from app.services.expense_service import create_cash_expense
from app.services.ticket_service import get_ticket, open_ticket_for_table
from app.services.product_service import add_product_to_ticket, get_ticket_lines
from app.services.order_service import list_ticket_station_orders, send_round
from app.services.payment_service import (
    create_payment,
    get_active_payment_total,
    list_ticket_payments,
    start_payment,
)
from app.services.print_service import list_pending_print_jobs
from app.services.sales_inventory_service import list_ticket_inventory_movements

router = APIRouter(prefix="/pos", tags=["pos"])

BUSINESS_ERROR_RESPONSES = {
    400: {"model": BusinessErrorResponse},
    403: {"model": BusinessErrorResponse},
    404: {"model": BusinessErrorResponse},
    409: {"model": BusinessErrorResponse},
}


def _inventory_movement_response(
    movement: InventoryMovement,
) -> InventoryMovementResponse:
    """Traduce un movimiento persistido al contrato público de inventario."""
    return InventoryMovementResponse(
        id=movement.id,
        folio=movement.folio,
        inventory_item_id=movement.inventory_item_id,
        movement_type=movement.movement_type,
        quantity_base=movement.quantity_base,
        signed_quantity_base=movement.signed_quantity_base,
        unit_cost_cents=movement.unit_cost_cents_snapshot,
        source_type=movement.source_type,
        source_id=movement.source_id,
        reason=movement.reason,
        created_by_employee_id=movement.registered_by_employee_id,
        created_at=movement.created_at,
    )


def _to_http_exception(error: BusinessError) -> HTTPException:
    """Convierte errores públicos del dominio a códigos HTTP estables."""
    if isinstance(error, InvalidBusinessDataError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(error, PermissionDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
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
    "/cash-expenses",
    response_model=CashExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def create_cash_expense_endpoint(
    payload: CashExpenseCreateRequest, db: Session = Depends(get_db)
) -> CashExpenseResponse:
    try:
        expense = create_cash_expense(
            db,
            employee_id=payload.employee_id,
            amount_cents=payload.amount_cents,
            description=payload.description,
            category=payload.category,
            payment_method_id=payload.payment_method_id,
            note=payload.note,
        )
        db.commit()
        db.refresh(expense)
        return CashExpenseResponse.model_validate(expense)
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/cash-shifts/{cash_shift_id}/summary",
    response_model=CashShiftSummaryResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def get_cash_shift_summary_endpoint(
    cash_shift_id: int, db: Session = Depends(get_db)
) -> CashShiftSummaryResponse:
    try:
        return CashShiftSummaryResponse.model_validate(
            get_cash_shift_summary(db, cash_shift_id)
        )
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.post(
    "/cash-shifts/{cash_shift_id}/close",
    response_model=CashShiftCloseResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def close_cash_shift_endpoint(
    cash_shift_id: int,
    payload: CashShiftCloseRequest,
    db: Session = Depends(get_db),
) -> CashShiftCloseResponse:
    try:
        cash_shift = close_cash_shift(
            db,
            cash_shift_id=cash_shift_id,
            employee_id=payload.employee_id,
            declared_cash_cents=payload.declared_cash_cents,
            note=payload.note,
            allow_pending_print_jobs=payload.allow_pending_print_jobs,
        )
        print_job = db.execute(
            select(PrintJob).where(
                PrintJob.idempotency_key == f"CORTE:{cash_shift_id}"
            )
        ).scalar_one()
        response = CashShiftCloseResponse(
            cash_shift=CashShiftResponse.model_validate(cash_shift),
            summary=CashShiftSummaryResponse.model_validate(
                get_cash_shift_summary(db, cash_shift_id)
            ),
            print_job=PrintJobResponse.model_validate(print_job),
            closed=True,
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


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


@router.post(
    "/tickets/{ticket_id}/start-payment",
    response_model=TicketResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def start_payment_endpoint(
    ticket_id: int,
    payload: StartPaymentRequest,
    db: Session = Depends(get_db),
) -> TicketResponse:
    try:
        ticket = start_payment(db, ticket_id, payload.employee_id)
        db.commit()
        db.refresh(ticket)
        return TicketResponse.model_validate(ticket)
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/tickets/{ticket_id}/payments",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def create_payment_endpoint(
    ticket_id: int,
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
) -> PaymentCreateResponse:
    try:
        payment = create_payment(
            db,
            ticket_id=ticket_id,
            employee_id=payload.employee_id,
            payment_method_id=payload.payment_method_id,
            amount_cents=payload.amount_cents,
            received_cents=payload.received_cents,
            reference=payload.reference,
        )
        ticket = get_ticket(db, ticket_id)
        total_paid = get_active_payment_total(db, ticket_id)
        response = PaymentCreateResponse(
            payment=PaymentResponse.model_validate(payment),
            ticket=TicketResponse.model_validate(ticket),
            total_paid_cents=total_paid,
            remaining_cents=max(ticket.total_cents - total_paid, 0),
            closed=ticket.status == "PAID",
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/tickets/{ticket_id}/payments",
    response_model=PaymentSummaryResponse,
    responses={404: {"model": BusinessErrorResponse}},
)
def list_ticket_payments_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> PaymentSummaryResponse:
    try:
        ticket = get_ticket(db, ticket_id)
        payments = list_ticket_payments(db, ticket_id)
        total_paid = get_active_payment_total(db, ticket_id)
        return PaymentSummaryResponse(
            ticket_id=ticket_id,
            payments=[PaymentResponse.model_validate(item) for item in payments],
            total_paid_cents=total_paid,
            remaining_cents=max(ticket.total_cents - total_paid, 0),
            closed=ticket.status == "PAID",
        )
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.get(
    "/tickets/{ticket_id}/inventory-movements",
    response_model=list[InventoryMovementResponse],
    responses={404: {"model": BusinessErrorResponse}},
)
def list_ticket_inventory_movements_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> list[InventoryMovementResponse]:
    """Expone únicamente consumos de venta asociados a líneas del ticket."""
    try:
        return [
            _inventory_movement_response(movement)
            for movement in list_ticket_inventory_movements(db, ticket_id)
        ]
    except BusinessError as error:
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


@router.post(
    "/tickets/{ticket_id}/send-round",
    response_model=SendRoundResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def send_round_endpoint(
    ticket_id: int,
    payload: SendRoundRequest,
    db: Session = Depends(get_db),
) -> SendRoundResponse:
    try:
        batch = send_round(db, ticket_id, payload.employee_id)
        print_jobs_created = db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.command_batch_id == batch.id
            )
        )
        lines_sent = db.scalar(
            select(func.count(TicketLine.id)).where(
                TicketLine.ticket_id == ticket_id,
                TicketLine.round_number == batch.round_number,
            )
        )
        response = SendRoundResponse(
            ticket_id=ticket_id,
            command_batch_id=batch.id,
            round_number=batch.round_number,
            station_orders_created=len(batch.station_orders),
            print_jobs_created=print_jobs_created or 0,
            lines_sent=lines_sent or 0,
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/tickets/{ticket_id}/station-orders",
    response_model=list[StationOrderResponse],
    responses={404: {"model": BusinessErrorResponse}},
)
def list_ticket_station_orders_endpoint(
    ticket_id: int, db: Session = Depends(get_db)
) -> list[StationOrderResponse]:
    try:
        return [
            StationOrderResponse.model_validate(order)
            for order in list_ticket_station_orders(db, ticket_id)
        ]
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.get(
    "/print-jobs/pending",
    response_model=list[PrintJobResponse],
)
def list_pending_print_jobs_endpoint(
    db: Session = Depends(get_db),
) -> list[PrintJobResponse]:
    return [
        PrintJobResponse.model_validate(job) for job in list_pending_print_jobs(db)
    ]


@router.post(
    "/ticket-lines/{line_id}/cancel",
    response_model=TicketLineCancelResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def cancel_ticket_line_endpoint(
    line_id: int,
    payload: TicketLineCancelRequest,
    db: Session = Depends(get_db),
) -> TicketLineCancelResponse:
    try:
        jobs_before = db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.job_type == "CANCELACION_COMANDA"
            )
        ) or 0
        line = cancel_ticket_line(
            db, line_id, payload.employee_id, payload.reason
        )
        ticket = get_ticket(db, line.ticket_id)
        jobs_after = db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.job_type == "CANCELACION_COMANDA"
            )
        ) or 0
        response = TicketLineCancelResponse(
            line=TicketLineResponse.model_validate(line),
            ticket=TicketResponse.model_validate(ticket),
            print_jobs_created=jobs_after - jobs_before,
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/tickets/{ticket_id}/cancel",
    response_model=TicketCancelResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def cancel_ticket_endpoint(
    ticket_id: int,
    payload: TicketCancelRequest,
    db: Session = Depends(get_db),
) -> TicketCancelResponse:
    try:
        jobs_before = db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.job_type == "CANCELACION_COMANDA"
            )
        ) or 0
        lines_to_cancel = db.scalar(
            select(func.count(TicketLine.id)).where(
                TicketLine.ticket_id == ticket_id,
                TicketLine.status != "CANCELLED",
            )
        )
        payments_to_cancel = db.scalar(
            select(func.count(Payment.id)).where(
                Payment.ticket_id == ticket_id,
                Payment.status == "ACTIVE",
            )
        )
        ticket = cancel_ticket(
            db, ticket_id, payload.employee_id, payload.reason
        )
        jobs_after = db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.job_type == "CANCELACION_COMANDA"
            )
        ) or 0
        response = TicketCancelResponse(
            ticket=TicketResponse.model_validate(ticket),
            lines_cancelled=lines_to_cancel or 0,
            payments_cancelled=payments_to_cancel or 0,
            print_jobs_created=jobs_after - jobs_before,
            table_released=ticket.table.status_cache == "FREE",
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None

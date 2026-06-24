from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.security import SessionIdentity, require_session
from app.core.database import get_db
from app.schemas.production import ProductionActionRequest, ProductionOrderResponse
from app.services.exceptions import (
    BusinessConflictError,
    BusinessError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.production_service import list_station_orders, transition_station_order

router = APIRouter(
    prefix="/production", tags=["production"], dependencies=[Depends(require_session)]
)


def _http_error(error: BusinessError) -> HTTPException:
    code = status.HTTP_400_BAD_REQUEST
    if isinstance(error, EntityNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, BusinessConflictError):
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=str(error))


@router.get("/station-orders", response_model=list[ProductionOrderResponse])
def station_orders_endpoint(
    station_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProductionOrderResponse]:
    try:
        return [
            ProductionOrderResponse.model_validate(order)
            for order in list_station_orders(db, station_id, status, date_from, date_to)
        ]
    except InvalidBusinessDataError as error:
        raise _http_error(error) from None


def _transition(
    station_order_id: int, employee_id: int, action: str, db: Session
) -> ProductionOrderResponse:
    try:
        order = transition_station_order(db, station_order_id, employee_id, action)
        response = ProductionOrderResponse.model_validate(order)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _http_error(error) from None


@router.post("/station-orders/{station_order_id}/receive", response_model=ProductionOrderResponse)
def receive_order(
    station_order_id: int,
    payload: ProductionActionRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    return _transition(station_order_id, identity.employee.id, "receive", db)


@router.post("/station-orders/{station_order_id}/start", response_model=ProductionOrderResponse)
def start_order(
    station_order_id: int,
    payload: ProductionActionRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    return _transition(station_order_id, identity.employee.id, "start", db)


@router.post("/station-orders/{station_order_id}/complete", response_model=ProductionOrderResponse)
def complete_order(
    station_order_id: int,
    payload: ProductionActionRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    return _transition(station_order_id, identity.employee.id, "complete", db)


@router.post("/station-orders/{station_order_id}/deliver", response_model=ProductionOrderResponse)
def deliver_order(
    station_order_id: int,
    payload: ProductionActionRequest,
    db: Session = Depends(get_db),
    identity: SessionIdentity = Depends(require_session),
):
    return _transition(station_order_id, identity.employee.id, "deliver", db)

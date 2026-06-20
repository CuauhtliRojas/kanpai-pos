from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reporting import (
    InventoryConsumptionItem,
    OperationalSummaryResponse,
    PrintJobsSummaryResponse,
    SalesByPaymentMethodItem,
    SalesByProductItem,
)
from app.services.exceptions import InvalidBusinessDataError
from app.services.reporting_service import (
    get_inventory_consumption,
    get_operational_summary,
    get_print_jobs_summary,
    get_sales_by_payment_method,
    get_sales_by_product,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _bad_request(error: InvalidBusinessDataError) -> HTTPException:
    """Convierte errores públicos de filtros en HTTP 400 sin exponer trazas."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/operational-summary", response_model=OperationalSummaryResponse)
def operational_summary_endpoint(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> OperationalSummaryResponse:
    try:
        return OperationalSummaryResponse.model_validate(
            get_operational_summary(db, date_from, date_to)
        )
    except InvalidBusinessDataError as error:
        raise _bad_request(error) from None


@router.get(
    "/sales-by-payment-method", response_model=list[SalesByPaymentMethodItem]
)
def sales_by_payment_method_endpoint(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> list[SalesByPaymentMethodItem]:
    try:
        return [
            SalesByPaymentMethodItem.model_validate(item)
            for item in get_sales_by_payment_method(db, date_from, date_to)
        ]
    except InvalidBusinessDataError as error:
        raise _bad_request(error) from None


@router.get("/sales-by-product", response_model=list[SalesByProductItem])
def sales_by_product_endpoint(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> list[SalesByProductItem]:
    try:
        return [
            SalesByProductItem.model_validate(item)
            for item in get_sales_by_product(db, date_from, date_to)
        ]
    except InvalidBusinessDataError as error:
        raise _bad_request(error) from None


@router.get("/inventory-consumption", response_model=list[InventoryConsumptionItem])
def inventory_consumption_endpoint(
    movement_type: str = "SALE_CONSUMPTION",
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> list[InventoryConsumptionItem]:
    try:
        return [
            InventoryConsumptionItem.model_validate(item)
            for item in get_inventory_consumption(
                db, movement_type, date_from, date_to
            )
        ]
    except InvalidBusinessDataError as error:
        raise _bad_request(error) from None


@router.get("/print-jobs-summary", response_model=PrintJobsSummaryResponse)
def print_jobs_summary_endpoint(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> PrintJobsSummaryResponse:
    try:
        return PrintJobsSummaryResponse.model_validate(
            get_print_jobs_summary(db, date_from, date_to)
        )
    except InvalidBusinessDataError as error:
        raise _bad_request(error) from None

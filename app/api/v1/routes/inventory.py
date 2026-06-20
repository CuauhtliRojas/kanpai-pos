from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import InventoryItem, InventoryMovement, PurchaseReceipt
from app.schemas import (
    BusinessErrorResponse,
    InventoryItemResponse,
    InventoryMovementCreateRequest,
    InventoryMovementResponse,
    InventoryStockResponse,
    PurchaseReceiptCreateRequest,
    PurchaseReceiptLineResponse,
    PurchaseReceiptResponse,
    StockAlertResponse,
)
from app.services.exceptions import (
    BusinessConflictError,
    BusinessError,
    EntityNotFoundError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.services.inventory_service import (
    convert_quantity,
    create_inventory_movement,
    get_current_stock,
    list_inventory_items_with_stock,
    process_purchase_receipt,
)
from app.services.stock_alert_service import list_active_stock_alerts

router = APIRouter(prefix="/inventory", tags=["inventory"])

BUSINESS_ERROR_RESPONSES = {
    400: {"model": BusinessErrorResponse},
    403: {"model": BusinessErrorResponse},
    404: {"model": BusinessErrorResponse},
    409: {"model": BusinessErrorResponse},
}


def _to_http_exception(error: BusinessError) -> HTTPException:
    """Mapea únicamente errores esperados del inventario a respuestas públicas."""
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


def _movement_response(movement: InventoryMovement) -> InventoryMovementResponse:
    """Traduce nombres históricos del modelo al contrato público de fase 3-H."""
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


def _receipt_response(receipt: PurchaseReceipt) -> PurchaseReceiptResponse:
    """Construye la recepción pública incluyendo cantidades capturadas y base."""
    return PurchaseReceiptResponse(
        id=receipt.id,
        folio=receipt.folio,
        cash_shift_id=receipt.cash_shift_id,
        registered_by_employee_id=receipt.registered_by_employee_id,
        cash_expense_id=receipt.cash_expense_id,
        supplier_name=receipt.supplier_name,
        invoice_reference=receipt.invoice_reference,
        paid_amount_cents=receipt.amount_paid_cents,
        payment_method_id=receipt.payment_method_id,
        note=receipt.note,
        status=receipt.status,
        created_at=receipt.created_at,
        processed_at=receipt.processed_at,
        lines=[
            PurchaseReceiptLineResponse(
                id=line.id,
                inventory_item_id=line.inventory_item_id,
                quantity=line.captured_quantity,
                unit_id=line.captured_unit_id,
                quantity_base=line.converted_quantity_base,
                unit_cost_cents=line.unit_cost_cents,
                status=line.status,
            )
            for line in receipt.lines
        ],
    )


@router.get("/items", response_model=list[InventoryItemResponse])
def list_inventory_items_endpoint(
    db: Session = Depends(get_db),
) -> list[InventoryItemResponse]:
    return [
        InventoryItemResponse.model_validate(item)
        for item in list_inventory_items_with_stock(db)
    ]


@router.get(
    "/items/{inventory_item_id}/stock",
    response_model=InventoryStockResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def get_inventory_stock_endpoint(
    inventory_item_id: int, db: Session = Depends(get_db)
) -> InventoryStockResponse:
    try:
        return InventoryStockResponse.model_validate(
            get_current_stock(db, inventory_item_id)
        )
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.post(
    "/movements",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def create_inventory_movement_endpoint(
    payload: InventoryMovementCreateRequest, db: Session = Depends(get_db)
) -> InventoryMovementResponse:
    try:
        item = db.get(InventoryItem, payload.inventory_item_id)
        if item is None:
            raise EntityNotFoundError("El insumo no existe.")
        quantity_base = convert_quantity(
            db, payload.quantity, payload.unit_id, item.base_unit_id
        )
        movement = create_inventory_movement(
            db,
            inventory_item_id=payload.inventory_item_id,
            movement_type=payload.movement_type,
            quantity_base=quantity_base,
            employee_id=payload.employee_id,
            reason=payload.reason,
            unit_cost_cents=payload.unit_cost_cents,
            source_type="MANUAL",
        )
        response = _movement_response(movement)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/purchase-receipts",
    response_model=PurchaseReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def process_purchase_receipt_endpoint(
    payload: PurchaseReceiptCreateRequest, db: Session = Depends(get_db)
) -> PurchaseReceiptResponse:
    try:
        receipt = process_purchase_receipt(
            db,
            employee_id=payload.employee_id,
            lines=payload.lines,
            supplier_name=payload.supplier_name,
            invoice_reference=payload.invoice_reference,
            paid_amount_cents=payload.paid_amount_cents,
            payment_method_id=payload.payment_method_id,
            note=payload.note,
        )
        response = _receipt_response(receipt)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get("/stock-alerts/active", response_model=list[StockAlertResponse])
def list_active_stock_alerts_endpoint(
    db: Session = Depends(get_db),
) -> list[StockAlertResponse]:
    return [
        StockAlertResponse.model_validate(alert)
        for alert in list_active_stock_alerts(db)
    ]

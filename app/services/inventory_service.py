import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.constants import (
    InventoryMovementType,
    ReceiptStatus,
    StockStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    InventoryItem,
    InventoryMovement,
    PaymentMethod,
    PurchaseReceipt,
    PurchaseReceiptLine,
    Unit,
    UnitConversion,
)
from app.services.cash_shift_service import get_current_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.expense_service import create_cash_expense
from app.services.folio_service import generate_folio
from app.services.permission_service import (
    get_active_employee,
    require_employee_permission,
)
from app.services.stock_alert_service import evaluate_stock_alert

MOVEMENT_SIGNS = {
    InventoryMovementType.PURCHASE: 1,
    InventoryMovementType.ADJUSTMENT_IN: 1,
    InventoryMovementType.ADJUSTMENT_OUT: -1,
    InventoryMovementType.WASTE: -1,
    InventoryMovementType.SALE_CONSUMPTION: -1,
}


def _decimal_quantity(value: Decimal | float | int) -> Decimal:
    """Normaliza una cantidad pública a Decimal sin heredar error binario."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise InvalidBusinessDataError("La cantidad es inválida.") from error


def get_current_stock(db: Session, inventory_item_id: int) -> dict:
    """Calcula stock desde movimientos firmados, nunca desde un campo editable.

    El resultado incluye la unidad base real (`base_unit_id`), el mínimo
    (`minimum_stock_qty`) y uno de los estados OK, LOW_STOCK u OUT_OF_STOCK.
    """
    item = db.get(InventoryItem, inventory_item_id)
    if item is None:
        raise EntityNotFoundError("El insumo no existe.")
    current = db.scalar(
        select(func.sum(InventoryMovement.signed_quantity_base)).where(
            InventoryMovement.inventory_item_id == inventory_item_id
        )
    )
    current_stock = Decimal(current or 0)
    minimum_stock = Decimal(item.minimum_stock_qty)
    if current_stock <= 0:
        stock_status = StockStatus.OUT
    elif current_stock <= minimum_stock:
        stock_status = StockStatus.LOW
    else:
        stock_status = StockStatus.OK
    return {
        "inventory_item_id": item.id,
        "sku": item.item_code,
        "name": item.name,
        "base_unit_id": item.base_unit_id,
        "base_unit_name": item.base_unit.unit_key,
        "current_stock": current_stock,
        "stock_minimum": minimum_stock,
        "stock_status": stock_status,
    }


def list_inventory_items_with_stock(db: Session) -> list[dict]:
    """Lista insumos y agrega su stock calculado desde el ledger local."""
    items = db.execute(
        select(InventoryItem)
        .where(InventoryItem.active.is_(True))
        .order_by(InventoryItem.item_code)
    ).scalars()
    result = []
    for item in items:
        stock = get_current_stock(db, item.id)
        stock["id"] = item.id
        stock["active"] = item.active
        result.append(stock)
    return result


def convert_quantity(
    db: Session,
    quantity: Decimal | float | int,
    from_unit_id: int,
    to_unit_id: int,
) -> Decimal:
    """Convierte una cantidad usando la tabla activa o su inversa segura.

    La misma unidad conserva el valor. Para una conversión inversa se usa el
    recíproco únicamente cuando el factor almacenado es estrictamente positivo.
    """
    normalized = _decimal_quantity(quantity)
    if normalized <= 0:
        raise InvalidBusinessDataError("La cantidad debe ser mayor a cero.")

    from_unit = db.get(Unit, from_unit_id)
    if from_unit is None:
        raise EntityNotFoundError("La unidad de origen no existe.")
    to_unit = db.get(Unit, to_unit_id)
    if to_unit is None:
        raise EntityNotFoundError("La unidad destino no existe.")
    if not from_unit.active or not to_unit.active:
        raise InvalidBusinessDataError("La unidad está inactiva.")
    if from_unit_id == to_unit_id:
        return normalized

    conversion = db.execute(
        select(UnitConversion).where(
            UnitConversion.from_unit_id == from_unit_id,
            UnitConversion.to_unit_id == to_unit_id,
            UnitConversion.active.is_(True),
        )
    ).scalar_one_or_none()
    if conversion is not None:
        factor = Decimal(conversion.factor)
        if factor <= 0:
            raise InvalidBusinessDataError("La conversión de unidad es inválida.")
        return normalized * factor

    inverse = db.execute(
        select(UnitConversion).where(
            UnitConversion.from_unit_id == to_unit_id,
            UnitConversion.to_unit_id == from_unit_id,
            UnitConversion.active.is_(True),
        )
    ).scalar_one_or_none()
    if inverse is not None and Decimal(inverse.factor) > 0:
        return normalized / Decimal(inverse.factor)
    raise InvalidBusinessDataError("Las unidades son incompatibles.")


def create_inventory_movement(
    db: Session,
    inventory_item_id: int,
    movement_type: str,
    quantity_base: Decimal,
    employee_id: int,
    reason: str,
    unit_cost_cents: int | None = None,
    source_type: str | None = None,
    source_id: int | None = None,
    ticket_line_id: int | None = None,
    require_adjust_permission: bool = True,
) -> InventoryMovement:
    """Registra un movimiento firmado, auditoría y alerta sin hacer commit.

    ``require_adjust_permission`` solo se desactiva desde flujos internos que
    ya autorizaron la operación de negocio, como el consumo por venta.
    """
    item = db.get(InventoryItem, inventory_item_id)
    if item is None:
        raise EntityNotFoundError("El insumo no existe.")
    if not item.active:
        raise BusinessConflictError("El insumo está inactivo.")
    get_active_employee(db, employee_id)
    if require_adjust_permission:
        require_employee_permission(db, employee_id, "INVENTORY_ADJUST")

    normalized_type = movement_type.strip()
    if normalized_type not in MOVEMENT_SIGNS:
        raise InvalidBusinessDataError("El tipo de movimiento es inválido.")
    normalized_quantity = _decimal_quantity(quantity_base)
    if normalized_quantity <= 0:
        raise InvalidBusinessDataError("La cantidad debe ser mayor a cero.")
    if unit_cost_cents is not None and unit_cost_cents < 0:
        raise InvalidBusinessDataError("El costo unitario no puede ser negativo.")
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise InvalidBusinessDataError("El motivo no puede estar vacío.")

    cost = unit_cost_cents or 0
    signed_quantity = normalized_quantity * MOVEMENT_SIGNS[normalized_type]
    movement = InventoryMovement(
        folio=generate_folio(db, "MOVIMIENTO"),
        inventory_item_id=inventory_item_id,
        movement_type=normalized_type,
        quantity_base=normalized_quantity,
        signed_quantity_base=signed_quantity,
        unit_cost_cents_snapshot=cost,
        total_cost_cents=int(normalized_quantity * cost),
        registered_by_employee_id=employee_id,
        ticket_line_id=ticket_line_id,
        source_type=source_type,
        source_id=source_id,
        reason=normalized_reason,
    )
    db.add(movement)
    db.flush()
    db.add(
        AuditEvent(
            event_type=audit_event("INVENTORY_MOVEMENT_CREATED"),
            entity_type="InventoryMovement",
            entity_id=movement.id,
            actor_employee_id=employee_id,
            after_snapshot=json.dumps(
                {
                    "movement_type": normalized_type,
                    "quantity_base": str(normalized_quantity),
                    "signed_quantity_base": str(signed_quantity),
                    "source_type": source_type,
                    "source_id": source_id,
                }
            ),
            reason=normalized_reason,
        )
    )
    db.flush()
    evaluate_stock_alert(db, inventory_item_id, employee_id)
    return movement


def _line_value(line: Any, field: str) -> Any:
    """Lee líneas Pydantic o diccionarios sin acoplar el servicio al API."""
    return line[field] if isinstance(line, dict) else getattr(line, field)


def process_purchase_receipt(
    db: Session,
    employee_id: int,
    lines: list,
    supplier_name: str | None = None,
    invoice_reference: str | None = None,
    paid_amount_cents: int = 0,
    payment_method_id: int | None = None,
    note: str | None = None,
) -> PurchaseReceipt:
    """Procesa una recepción, sus movimientos y gasto opcional sin commit.

    Todas las líneas se validan y convierten antes de crear datos operativos.
    Una compra pagada exige corte abierto y delega el gasto al servicio vigente.
    """
    get_active_employee(db, employee_id)
    require_employee_permission(db, employee_id, "INVENTORY_ADJUST")
    if paid_amount_cents < 0:
        raise InvalidBusinessDataError("El monto pagado no puede ser negativo.")
    if not lines:
        raise InvalidBusinessDataError("La recepción requiere al menos una línea.")

    cash_shift = None
    if paid_amount_cents > 0:
        cash_shift = get_current_cash_shift(db)
        if cash_shift is None:
            raise BusinessConflictError("No existe un corte de caja abierto.")
        require_employee_permission(db, employee_id, "EXPENSE_CREATE")
        if payment_method_id is None:
            raise InvalidBusinessDataError("El método de pago es obligatorio.")
        payment_method = db.get(PaymentMethod, payment_method_id)
        if payment_method is None:
            raise EntityNotFoundError("El método de pago no existe.")
        if not payment_method.active:
            raise BusinessConflictError("El método de pago está inactivo.")

    validated_lines: list[tuple[InventoryItem, Decimal, int, Decimal, int]] = []
    for line in lines:
        item_id = _line_value(line, "inventory_item_id")
        item = db.get(InventoryItem, item_id)
        if item is None:
            raise EntityNotFoundError("El insumo no existe.")
        if not item.active:
            raise BusinessConflictError("El insumo está inactivo.")
        quantity = _decimal_quantity(_line_value(line, "quantity"))
        unit_id = _line_value(line, "unit_id")
        quantity_base = convert_quantity(db, quantity, unit_id, item.base_unit_id)
        unit_cost = _line_value(line, "unit_cost_cents")
        if unit_cost < 0:
            raise InvalidBusinessDataError("El costo unitario no puede ser negativo.")
        validated_lines.append((item, quantity, unit_id, quantity_base, unit_cost))

    expense = None
    if paid_amount_cents > 0:
        expense = create_cash_expense(
            db,
            employee_id=employee_id,
            amount_cents=paid_amount_cents,
            description=f"Compra de almacén - {supplier_name or 'Proveedor no especificado'}",
            category="INVENTORY_PURCHASE",
            payment_method_id=payment_method_id,
            note=note,
        )

    receipt = PurchaseReceipt(
        folio=generate_folio(db, "RECEPCION"),
        cash_shift_id=cash_shift.id if cash_shift else None,
        registered_by_employee_id=employee_id,
        cash_expense_id=expense.id if expense else None,
        receipt_type=InventoryMovementType.PURCHASE,
        status=ReceiptStatus.DRAFT,
        supplier_name=supplier_name.strip()
        if supplier_name and supplier_name.strip()
        else None,
        invoice_reference=(
            invoice_reference.strip()
            if invoice_reference and invoice_reference.strip()
            else None
        ),
        invoice_note=invoice_reference,
        note=note.strip() if note and note.strip() else None,
        amount_paid_cents=paid_amount_cents,
        payment_method_id=payment_method_id if paid_amount_cents > 0 else None,
    )
    db.add(receipt)
    db.flush()

    for item, quantity, unit_id, quantity_base, unit_cost in validated_lines:
        receipt_line = PurchaseReceiptLine(
            purchase_receipt_id=receipt.id,
            inventory_item_id=item.id,
            captured_quantity=quantity,
            captured_unit_id=unit_id,
            converted_quantity_base=quantity_base,
            unit_cost_cents=unit_cost,
            status=ReceiptStatus.PROCESSED,
        )
        db.add(receipt_line)
        db.flush()
        movement = create_inventory_movement(
            db,
            inventory_item_id=item.id,
            movement_type=InventoryMovementType.PURCHASE,
            quantity_base=quantity_base,
            employee_id=employee_id,
            reason=f"Recepción {receipt.folio}",
            unit_cost_cents=unit_cost,
            source_type="PurchaseReceiptLine",
            source_id=receipt_line.id,
        )
        movement.purchase_receipt_line_id = receipt_line.id
        movement.cash_expense_id = expense.id if expense else None

    receipt.status = ReceiptStatus.PROCESSED
    receipt.processed_at = datetime.utcnow()
    db.flush()
    db.add(
        AuditEvent(
            event_type=audit_event("PURCHASE_RECEIPT_PROCESSED"),
            entity_type="PurchaseReceipt",
            entity_id=receipt.id,
            actor_employee_id=employee_id,
            cash_shift_id=receipt.cash_shift_id,
            after_snapshot=json.dumps(
                {
                    "folio": receipt.folio,
                    "status": receipt.status,
                    "line_count": len(validated_lines),
                    "cash_expense_id": receipt.cash_expense_id,
                }
            ),
        )
    )
    db.flush()
    return receipt

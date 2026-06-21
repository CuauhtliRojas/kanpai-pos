from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_key: str
    name: str
    unit_family: str


class InventoryStockResponse(BaseModel):
    inventory_item_id: int
    sku: str
    name: str
    base_unit_id: int
    base_unit_name: str
    current_stock: Decimal
    stock_minimum: Decimal
    stock_status: str


class InventoryItemResponse(BaseModel):
    id: int
    sku: str
    name: str
    base_unit_id: int
    base_unit_name: str
    current_stock: Decimal
    stock_minimum: Decimal
    stock_status: str
    active: bool


class InventoryMovementCreateRequest(BaseModel):
    employee_id: int
    inventory_item_id: int
    movement_type: str
    quantity: Decimal
    unit_id: int
    reason: str
    unit_cost_cents: int | None = None


class InventoryMovementResponse(BaseModel):
    id: int
    folio: str
    inventory_item_id: int
    movement_type: str
    quantity_base: Decimal
    signed_quantity_base: Decimal
    unit_cost_cents: int | None
    source_type: str | None
    source_id: int | None
    reason: str | None
    created_by_employee_id: int
    created_at: datetime


class InventoryMovementHistoryItem(BaseModel):
    id: int
    folio: str
    inventory_item_id: int
    item_name: str
    movement_type: str
    quantity_base: Decimal
    signed_quantity_base: Decimal
    stock_before_base: Decimal
    stock_after_base: Decimal
    source_type: str | None
    source_id: int | None
    ticket_line_id: int | None
    purchase_receipt_line_id: int | None
    cash_expense_id: int | None
    registered_by_employee_id: int
    employee_name: str
    reason: str | None
    created_at: datetime


class PurchaseReceiptLineRequest(BaseModel):
    inventory_item_id: int
    quantity: Decimal
    unit_id: int
    unit_cost_cents: int = 0


class PurchaseReceiptCreateRequest(BaseModel):
    employee_id: int
    supplier_name: str | None = None
    invoice_reference: str | None = None
    paid_amount_cents: int = 0
    payment_method_id: int | None = None
    note: str | None = None
    lines: list[PurchaseReceiptLineRequest]


class PurchaseReceiptLineResponse(BaseModel):
    id: int
    inventory_item_id: int
    quantity: Decimal
    unit_id: int
    quantity_base: Decimal
    unit_cost_cents: int
    status: str


class PurchaseReceiptResponse(BaseModel):
    id: int
    folio: str
    cash_shift_id: int | None
    registered_by_employee_id: int
    cash_expense_id: int | None
    supplier_name: str | None
    invoice_reference: str | None
    paid_amount_cents: int
    payment_method_id: int | None
    note: str | None
    status: str
    created_at: datetime
    processed_at: datetime | None
    lines: list[PurchaseReceiptLineResponse]


class StockAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_item_id: int
    alert_type: str
    status: str
    threshold_quantity: Decimal
    current_quantity: Decimal
    opened_at: datetime
    resolved_at: datetime | None
    message: str

from decimal import Decimal

from pydantic import BaseModel


class OperationalSummaryResponse(BaseModel):
    total_sales_cents: int
    total_paid_cents: int
    total_expenses_cents: int
    net_cash_cents: int
    paid_ticket_count: int
    cancelled_ticket_count: int
    open_ticket_count: int
    in_payment_ticket_count: int
    active_cash_shift_count: int
    pending_print_jobs_count: int
    failed_print_jobs_count: int
    low_stock_alert_count: int
    inventory_negative_item_count: int


class SalesByPaymentMethodItem(BaseModel):
    payment_method_id: int
    method_key: str
    method_name: str
    total_cents: int
    payment_count: int


class SalesByProductItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    quantity_sold: int
    total_cents: int


class InventoryConsumptionItem(BaseModel):
    inventory_item_id: int
    sku: str
    name: str
    movement_type: str
    total_quantity_base: Decimal
    base_unit_name: str
    movement_count: int


class PrintJobsSummaryResponse(BaseModel):
    total_print_jobs: int
    reprint_count: int
    pending_count: int
    claimed_count: int
    printed_count: int
    failed_count: int
    cancelled_count: int
    by_printer: dict[str, int]
    by_job_type: dict[str, int]


class ProductionTimesItem(BaseModel):
    station_id: int
    station_name: str
    orders_count: int
    average_receive_seconds: float | None
    average_prepare_seconds: float | None
    average_total_service_seconds: float | None

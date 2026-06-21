export type OperationalSummary = {
  total_sales_cents: number;
  total_paid_cents: number;
  total_expenses_cents: number;
  net_cash_cents: number;
  paid_ticket_count: number;
  cancelled_ticket_count: number;
  open_ticket_count: number;
  in_payment_ticket_count: number;
  active_cash_shift_count: number;
  pending_print_jobs_count: number;
  failed_print_jobs_count: number;
  low_stock_alert_count: number;
  inventory_negative_item_count: number;
};

export type SalesByProductItem = {
  product_id: number;
  sku: string;
  product_name: string;
  quantity_sold: number;
  total_cents: number;
  variant_breakdown: Array<{ name: string; sku: string | null; quantity_sold: number }>;
};

export type SalesByPaymentMethodItem = {
  payment_method_id: number;
  method_key: string;
  method_name: string;
  total_cents: number;
  payment_count: number;
};

export type InventoryConsumptionItem = {
  inventory_item_id: number;
  sku: string;
  name: string;
  movement_type: string;
  total_quantity_base: string;
  base_unit_name: string;
  movement_count: number;
};

export type ProductionTimesItem = {
  station_id: number;
  station_name: string;
  orders_count: number;
  average_receive_seconds: number | null;
  average_prepare_seconds: number | null;
  average_total_service_seconds: number | null;
};

export type PrintJobsSummary = {
  total_print_jobs: number;
  reprint_count: number;
  pending_count: number;
  claimed_count: number;
  printed_count: number;
  failed_count: number;
  cancelled_count: number;
  by_printer: Record<string, number>;
  by_job_type: Record<string, number>;
};

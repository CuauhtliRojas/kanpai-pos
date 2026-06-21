export type InventoryItem = {
  id: number;
  sku: string;
  name: string;
  base_unit_id: number;
  base_unit_name: string;
  current_stock: string;
  stock_minimum: string;
  stock_status: string;
  active: boolean;
};

export type StockAlert = {
  id: number;
  inventory_item_id: number;
  alert_type: string;
  status: string;
  threshold_quantity: string;
  current_quantity: string;
  opened_at: string;
  resolved_at: string | null;
  message: string;
};

export type InventoryMovementCreateRequest = {
  employee_id: number;
  inventory_item_id: number;
  movement_type: string;
  quantity: number | string;
  unit_id: number;
  reason: string;
  unit_cost_cents?: number | null;
};

export type InventoryMovementResponse = {
  id: number;
  folio: string;
  inventory_item_id: number;
  movement_type: string;
  quantity_base: string;
  signed_quantity_base: string;
  unit_cost_cents: number | null;
  source_type: string | null;
  source_id: number | null;
  reason: string | null;
  created_by_employee_id: number;
  created_at: string;
};

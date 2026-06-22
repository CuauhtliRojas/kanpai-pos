import { apiRequest } from "../../../api/http";
import type {
  InventoryItem,
  InventoryMovementCreateRequest,
  InventoryMovementHistoryItem,
  InventoryMovementHistoryParams,
  InventoryMovementResponse,
  StockAlert,
} from "../types/inventoryTypes";

export function getInventoryItems(): Promise<InventoryItem[]> {
  return apiRequest<InventoryItem[]>("/api/v1/inventory/items");
}

export function getStockAlerts(): Promise<StockAlert[]> {
  return apiRequest<StockAlert[]>("/api/v1/inventory/stock-alerts/active");
}

export function createInventoryMovement(
  payload: InventoryMovementCreateRequest,
): Promise<InventoryMovementResponse> {
  return apiRequest<InventoryMovementResponse>("/api/v1/inventory/movements", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getInventoryMovements(
  params: InventoryMovementHistoryParams,
): Promise<InventoryMovementHistoryItem[]> {
  const qs = new URLSearchParams();
  if (params.inventory_item_id !== undefined) {
    qs.set("inventory_item_id", String(params.inventory_item_id));
  }
  if (params.movement_type) qs.set("movement_type", params.movement_type);
  if (params.source_type) qs.set("source_type", params.source_type);
  if (params.created_from) qs.set("created_from", params.created_from);
  if (params.created_to) qs.set("created_to", params.created_to);
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  if (params.offset !== undefined) qs.set("offset", String(params.offset));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return apiRequest<InventoryMovementHistoryItem[]>(
    `/api/v1/inventory/movements${suffix}`,
  );
}

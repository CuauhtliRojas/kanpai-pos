import { apiRequest } from "../../../api/http";
import type {
  InventoryItem,
  InventoryMovementCreateRequest,
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

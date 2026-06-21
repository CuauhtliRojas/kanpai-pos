import { apiRequest } from "../../../api/http";
import type {
  ProductionAction,
  ProductionActionInput,
  ProductionOrder,
  ProductionStation,
} from "../types/productionTypes";

export function getProductionStations(): Promise<ProductionStation[]> {
  return apiRequest<ProductionStation[]>("/api/v1/catalog/stations");
}

export function getProductionOrders(stationId?: number): Promise<ProductionOrder[]> {
  const search = stationId === undefined ? "" : `?station_id=${stationId}`;
  return apiRequest<ProductionOrder[]>(`/api/v1/production/station-orders${search}`);
}

export function updateProductionOrder(
  action: ProductionAction,
  input: ProductionActionInput,
): Promise<ProductionOrder> {
  return apiRequest<ProductionOrder>(
    `/api/v1/production/station-orders/${input.orderId}/${action}`,
    {
      method: "POST",
      body: JSON.stringify({ employee_id: input.employeeId }),
    },
  );
}

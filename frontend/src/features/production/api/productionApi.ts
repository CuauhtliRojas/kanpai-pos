import { apiRequest } from "../../../api/http";
import type {
  ProductionAction,
  ProductionActionInput,
  ProductionOrder,
  ProductionOrdersParams,
  ProductionStation,
} from "../types/productionTypes";

export function getProductionStations(): Promise<ProductionStation[]> {
  return apiRequest<ProductionStation[]>("/api/v1/catalog/stations");
}

function normalizeProductionOrdersParams(
  params?: number | ProductionOrdersParams,
): ProductionOrdersParams {
  if (typeof params === "number") return { stationId: params };
  return params ?? {};
}

export function getProductionOrders(
  params?: number | ProductionOrdersParams,
): Promise<ProductionOrder[]> {
  const normalizedParams = normalizeProductionOrdersParams(params);
  const searchParams = new URLSearchParams();

  if (normalizedParams.stationId !== undefined) {
    searchParams.set("station_id", String(normalizedParams.stationId));
  }
  if (normalizedParams.status) searchParams.set("status", normalizedParams.status);
  if (normalizedParams.dateFrom) searchParams.set("date_from", normalizedParams.dateFrom);
  if (normalizedParams.dateTo) searchParams.set("date_to", normalizedParams.dateTo);

  const search = searchParams.toString();
  return apiRequest<ProductionOrder[]>(
    `/api/v1/production/station-orders${search ? `?${search}` : ""}`,
  );
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

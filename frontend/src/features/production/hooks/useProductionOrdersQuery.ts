import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductionOrders } from "../api/productionApi";
import type { ProductionOrdersParams } from "../types/productionTypes";

function getStationId(params?: number | ProductionOrdersParams): number | undefined {
  if (typeof params === "number") return params;
  return params?.stationId;
}

export function useProductionOrdersQuery(params?: number | ProductionOrdersParams) {
  const stationId = getStationId(params);

  return useQuery({
    queryKey: queryKeys.production.orders(params),
    queryFn: () => getProductionOrders(params),
    enabled: stationId !== undefined,
    refetchInterval: 10_000,
    retry: false,
  });
}

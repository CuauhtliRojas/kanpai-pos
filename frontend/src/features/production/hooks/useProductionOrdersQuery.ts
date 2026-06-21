import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductionOrders } from "../api/productionApi";

export function useProductionOrdersQuery(stationId?: number) {
  return useQuery({
    queryKey: queryKeys.production.orders(stationId),
    queryFn: () => getProductionOrders(stationId),
    enabled: stationId !== undefined,
    retry: false,
  });
}

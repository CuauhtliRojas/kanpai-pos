import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getStockAlerts } from "../api/inventoryApi";

export function useStockAlertsQuery() {
  return useQuery({
    queryKey: queryKeys.inventory.stockAlerts,
    queryFn: getStockAlerts,
    retry: false,
  });
}

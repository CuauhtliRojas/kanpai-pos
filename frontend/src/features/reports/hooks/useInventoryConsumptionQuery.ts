import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailyInventoryConsumption } from "../api/reportsApi";

export function useInventoryConsumptionQuery() {
  return useQuery({
    queryKey: queryKeys.reports.inventoryConsumption,
    queryFn: getDailyInventoryConsumption,
    retry: false,
  });
}

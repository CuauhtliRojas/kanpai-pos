import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getInventoryConsumption } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useInventoryConsumptionQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.inventoryConsumption(range),
    queryFn: () => getInventoryConsumption(range),
    retry: false,
  });
}

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductionTimes } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useProductionTimesQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.productionTimes(range),
    queryFn: () => getProductionTimes(range),
    retry: false,
  });
}

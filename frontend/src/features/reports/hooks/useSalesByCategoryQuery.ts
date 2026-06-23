import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getSalesByCategory } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useSalesByCategoryQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.salesByCategory(range),
    queryFn: () => getSalesByCategory(range),
    retry: false,
  });
}

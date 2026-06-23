import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getOperationalSummary } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useDailySalesReportQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.summary(range),
    queryFn: () => getOperationalSummary(range),
    retry: false,
  });
}

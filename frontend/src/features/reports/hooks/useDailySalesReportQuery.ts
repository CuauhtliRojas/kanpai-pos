import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailyOperationalSummary } from "../api/reportsApi";

export function useDailySalesReportQuery() {
  return useQuery({ queryKey: queryKeys.reports.dailySales, queryFn: getDailyOperationalSummary, retry: false });
}

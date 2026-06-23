import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getPrintJobsSummary } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function usePrintJobsSummaryQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.printJobs(range),
    queryFn: () => getPrintJobsSummary(range),
    retry: false,
  });
}

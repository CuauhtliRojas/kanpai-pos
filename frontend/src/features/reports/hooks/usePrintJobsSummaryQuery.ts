import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailyPrintJobsSummary } from "../api/reportsApi";

export function usePrintJobsSummaryQuery() {
  return useQuery({ queryKey: queryKeys.reports.printJobs, queryFn: getDailyPrintJobsSummary, retry: false });
}

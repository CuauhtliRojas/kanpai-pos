import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getPendingPrintJobs } from "../api/printingApi";

export function usePrintJobsQuery() {
  return useQuery({ queryKey: queryKeys.printing.jobs, queryFn: getPendingPrintJobs, retry: false });
}

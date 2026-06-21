import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailyProductionTimes } from "../api/reportsApi";

export function useProductionTimesQuery() {
  return useQuery({ queryKey: queryKeys.reports.productionTimes, queryFn: getDailyProductionTimes, retry: false });
}

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getCashShiftSummary } from "../api/cashApi";

export function useCashShiftSummaryQuery(cashShiftId: number | null) {
  return useQuery({
    queryKey: queryKeys.cash.summary(cashShiftId ?? 0),
    queryFn: () => getCashShiftSummary(cashShiftId as number),
    enabled: cashShiftId !== null,
    retry: false,
  });
}

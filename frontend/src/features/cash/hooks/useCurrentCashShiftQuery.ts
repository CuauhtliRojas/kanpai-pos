import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getCurrentCashShift } from "../api/cashApi";

export function useCurrentCashShiftQuery() {
  return useQuery({
    queryKey: queryKeys.cash.current,
    queryFn: getCurrentCashShift,
    retry: false,
  });
}

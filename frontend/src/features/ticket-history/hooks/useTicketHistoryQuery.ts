import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketHistory } from "../api/ticketHistoryApi";
import type { TicketHistoryFilters } from "../types/ticketHistoryTypes";

export function useTicketHistoryQuery(filters: TicketHistoryFilters, enabled = true) {
  return useQuery({
    queryKey: queryKeys.ticketHistory.list(filters),
    queryFn: () => getTicketHistory(filters),
    enabled,
    retry: false,
  });
}

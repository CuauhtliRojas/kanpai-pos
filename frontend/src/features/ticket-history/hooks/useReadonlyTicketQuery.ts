import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getReadonlyTicket } from "../api/ticketHistoryApi";

export function useReadonlyTicketQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.ticketHistory.detail(ticketId ?? 0),
    queryFn: () => getReadonlyTicket(ticketId!),
    enabled: ticketId !== null,
    retry: false,
  });
}

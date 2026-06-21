import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicket } from "../api/tablesApi";

export function useTicketQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.tickets.detail(ticketId ?? 0),
    queryFn: () => getTicket(ticketId as number),
    enabled: ticketId !== null,
    retry: false,
  });
}

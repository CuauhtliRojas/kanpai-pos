import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketLines } from "../api/ticketsApi";

export function useTicketLinesQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.tickets.lines(ticketId ?? 0),
    queryFn: () => getTicketLines(ticketId as number),
    enabled: ticketId !== null,
    retry: false,
  });
}

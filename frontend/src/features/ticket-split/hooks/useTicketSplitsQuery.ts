import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketSplits } from "../api/ticketSplitApi";

export function useTicketSplitsQuery(ticketId: number | null) {
  return useQuery({ queryKey: queryKeys.tickets.splits(ticketId ?? 0), queryFn: () => getTicketSplits(ticketId ?? 0), enabled: ticketId !== null, retry: false });
}

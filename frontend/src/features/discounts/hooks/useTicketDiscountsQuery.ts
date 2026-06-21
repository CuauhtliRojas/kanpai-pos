import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketDiscounts } from "../api/discountsApi";

export function useTicketDiscountsQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.discounts.ticket(ticketId ?? 0),
    queryFn: () => getTicketDiscounts(ticketId as number),
    enabled: ticketId !== null,
    retry: false,
  });
}

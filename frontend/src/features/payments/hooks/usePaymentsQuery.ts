import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketPayments } from "../api/paymentsApi";

export function usePaymentsQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.payments.list(ticketId ?? 0),
    queryFn: () => getTicketPayments(ticketId as number),
    enabled: ticketId !== null,
    retry: false,
  });
}

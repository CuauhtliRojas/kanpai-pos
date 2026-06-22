import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { cancelTicket } from "../api/ticketCancelApi";
import type { TicketCancelRequest } from "../types/ticketCancelTypes";

export function useCancelTicketMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ticketId, payload }: { ticketId: number; payload: TicketCancelRequest }) => cancelTicket(ticketId, payload),
    onSuccess: async (result) => {
      queryClient.setQueryData(queryKeys.tickets.detail(result.ticket.id), result.ticket);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lines(result.ticket.id) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
        queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
        queryClient.invalidateQueries({ queryKey: queryKeys.ticketHistory.all }),
      ]);
    },
  });
}

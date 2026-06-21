import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { cancelTicketLine } from "../api/ticketAdjustmentsApi";
import type {
  CancelTicketLineRequest,
  TicketLineAdjustmentInput,
} from "../types/ticketAdjustmentTypes";

export function useCancelTicketLineMutation() {
  const queryClient = useQueryClient();
  const { activeTicket, setActiveTicket } = useCurrentOperation();
  return useMutation({
    mutationFn: ({ lineId, payload }: TicketLineAdjustmentInput<CancelTicketLineRequest>) =>
      cancelTicketLine(lineId, payload),
    onSuccess: async (result, input) => {
      if (activeTicket?.id === input.ticketId) {
        setActiveTicket(result.ticket);
        queryClient.setQueryData(queryKeys.tickets.detail(input.ticketId), result.ticket);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.detail(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lines(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.commands.stationOrders(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
        queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
      ]);
    },
  });
}

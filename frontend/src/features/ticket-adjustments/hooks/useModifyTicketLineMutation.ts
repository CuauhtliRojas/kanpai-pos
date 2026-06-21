import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { modifyTicketLine } from "../api/ticketAdjustmentsApi";
import type {
  ModifyTicketLineRequest,
  TicketLineAdjustmentInput,
} from "../types/ticketAdjustmentTypes";

export function useModifyTicketLineMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lineId, payload }: TicketLineAdjustmentInput<ModifyTicketLineRequest>) =>
      modifyTicketLine(lineId, payload),
    onSuccess: async (_result, input) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.detail(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lines(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.commands.stationOrders(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
      ]);
    },
  });
}

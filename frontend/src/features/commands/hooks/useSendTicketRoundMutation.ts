import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { sendTicketRound } from "../api/commandsApi";
import type { SendRoundRequest } from "../types/commandTypes";

type SendTicketRoundVariables = {
  ticketId: number;
  payload: SendRoundRequest;
};

export function useSendTicketRoundMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, payload }: SendTicketRoundVariables) =>
      sendTicketRound(ticketId, payload),
    onSuccess: async (_result, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.tickets.detail(variables.ticketId),
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.tickets.lines(variables.ticketId),
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.commands.stationOrders(variables.ticketId),
        }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
      ]);
    },
  });
}

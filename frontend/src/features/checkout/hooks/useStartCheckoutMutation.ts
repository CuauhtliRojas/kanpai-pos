import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { startCheckout } from "../api/checkoutApi";
import type { StartPaymentRequest } from "../types/checkoutTypes";

type StartCheckoutVariables = {
  ticketId: number;
  payload: StartPaymentRequest;
};

export function useStartCheckoutMutation() {
  const queryClient = useQueryClient();
  const { activeTicket, setActiveTicket } = useCurrentOperation();

  return useMutation({
    mutationFn: ({ ticketId, payload }: StartCheckoutVariables) =>
      startCheckout(ticketId, payload),
    onSuccess: async (ticket, variables) => {
      if (activeTicket?.id === variables.ticketId) {
        setActiveTicket(ticket);
      }
      queryClient.setQueryData(queryKeys.tickets.detail(variables.ticketId), ticket);
      queryClient.setQueryData(queryKeys.checkout.current(variables.ticketId), ticket);

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.tickets.detail(variables.ticketId),
        }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
      ]);
    },
  });
}

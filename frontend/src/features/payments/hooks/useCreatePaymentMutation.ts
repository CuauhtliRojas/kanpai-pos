import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { createTicketPayment } from "../api/paymentsApi";
import type { PaymentCreateRequest } from "../types/paymentTypes";

type CreatePaymentVariables = {
  ticketId: number;
  cashShiftId: number;
  payload: PaymentCreateRequest;
};

export function useCreatePaymentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, payload }: CreatePaymentVariables) =>
      createTicketPayment(ticketId, payload),
    onSuccess: async (result, variables) => {
      queryClient.setQueryData(queryKeys.tickets.detail(variables.ticketId), result.ticket);
      if (result.closed) {
        queryClient.removeQueries({
          queryKey: queryKeys.checkout.current(variables.ticketId),
          exact: true,
        });
      } else {
        queryClient.setQueryData(queryKeys.checkout.current(variables.ticketId), result.ticket);
      }

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: queryKeys.tickets.detail(variables.ticketId),
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.payments.list(variables.ticketId),
        }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.cash.summary(variables.cashShiftId),
        }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
        queryClient.invalidateQueries({ queryKey: queryKeys.ticketHistory.all }),
      ]);
    },
  });
}

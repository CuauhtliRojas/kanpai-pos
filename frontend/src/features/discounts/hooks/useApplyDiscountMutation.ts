import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { getTicket } from "../../tables/api/tablesApi";
import { applyTicketDiscount } from "../api/discountsApi";
import type { ApplyDiscountInput } from "../types/discountTypes";

export function useApplyDiscountMutation() {
  const queryClient = useQueryClient();
  const { activeTicket, setActiveTicket } = useCurrentOperation();
  return useMutation({
    mutationFn: ({ ticketId, payload }: ApplyDiscountInput) => applyTicketDiscount(ticketId, payload),
    onSuccess: async (_discount, input) => {
      const ticket = await getTicket(input.ticketId);
      queryClient.setQueryData(queryKeys.tickets.detail(input.ticketId), ticket);
      if (activeTicket?.id === input.ticketId) setActiveTicket(ticket);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.discounts.ticket(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.detail(input.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
      ]);
    },
  });
}

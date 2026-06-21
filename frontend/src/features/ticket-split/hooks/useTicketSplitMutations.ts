import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { createEqualSplits, createLinesSplit, payTicketSplit } from "../api/ticketSplitApi";
import type { ByLinesSplitRequest, EqualSplitRequest, SplitPaymentRequest } from "../types/ticketSplitTypes";

function useRefreshSplits() {
  const client = useQueryClient();
  return async (ticketId: number, cashShiftId?: number) => {
    await Promise.all([
      client.invalidateQueries({ queryKey: queryKeys.tickets.splits(ticketId) }),
      client.invalidateQueries({ queryKey: queryKeys.tickets.detail(ticketId) }),
      client.invalidateQueries({ queryKey: queryKeys.payments.list(ticketId) }),
      client.invalidateQueries({ queryKey: queryKeys.tables.list }),
      ...(cashShiftId === undefined ? [] : [client.invalidateQueries({ queryKey: queryKeys.cash.summary(cashShiftId) })]),
    ]);
  };
}

export function useCreateEqualSplitsMutation() {
  const refresh = useRefreshSplits();
  return useMutation({ mutationFn: ({ ticketId, payload }: { ticketId: number; payload: EqualSplitRequest }) => createEqualSplits(ticketId, payload), onSuccess: (_result, input) => refresh(input.ticketId) });
}
export function useCreateLinesSplitMutation() {
  const refresh = useRefreshSplits();
  return useMutation({ mutationFn: ({ ticketId, payload }: { ticketId: number; payload: ByLinesSplitRequest }) => createLinesSplit(ticketId, payload), onSuccess: (_result, input) => refresh(input.ticketId) });
}
export function usePayTicketSplitMutation() {
  const refresh = useRefreshSplits();
  return useMutation({ mutationFn: ({ splitId, payload }: { ticketId: number; cashShiftId: number; splitId: number; payload: SplitPaymentRequest }) => payTicketSplit(splitId, payload), onSuccess: (_result, input) => refresh(input.ticketId, input.cashShiftId) });
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { closeCashShift } from "../api/cashApi";
import type { CashShiftClose } from "../types/cashTypes";

type CloseCashShiftVariables = {
  cashShiftId: number;
  payload: CashShiftClose;
};

export function useCloseCashShiftMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cashShiftId, payload }: CloseCashShiftVariables) =>
      closeCashShift(cashShiftId, payload),
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.cash.current }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.cash.summary(variables.cashShiftId),
        }),
      ]);
    },
  });
}

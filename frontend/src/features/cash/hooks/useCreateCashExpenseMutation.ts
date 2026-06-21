import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { createCashExpense } from "../api/cashApi";

export function useCreateCashExpenseMutation(cashShiftId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createCashExpense,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.cash.current }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.cash.summary(cashShiftId),
        }),
      ]);
    },
  });
}

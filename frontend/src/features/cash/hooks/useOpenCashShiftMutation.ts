import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { openCashShift } from "../api/cashApi";

export function useOpenCashShiftMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: openCashShift,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.cash.current });
    },
  });
}

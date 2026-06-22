import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { reprintJob } from "../../printing/api/printingApi";

export function useReprintJobMutation(ticketId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reprintJob,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
        queryClient.invalidateQueries({ queryKey: queryKeys.printing.pending }),
        queryClient.invalidateQueries({ queryKey: queryKeys.ticketHistory.detail(ticketId) }),
      ]);
    },
  });
}

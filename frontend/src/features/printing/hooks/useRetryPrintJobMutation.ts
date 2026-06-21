import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { retryFailedPrintJobs } from "../api/printingApi";

export function useRetryPrintJobMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: retryFailedPrintJobs,
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
  });
}

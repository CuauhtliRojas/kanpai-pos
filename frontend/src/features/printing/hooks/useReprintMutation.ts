import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { reprintJob } from "../api/printingApi";

export function useReprintMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reprintJob,
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: queryKeys.printing.jobs }),
  });
}

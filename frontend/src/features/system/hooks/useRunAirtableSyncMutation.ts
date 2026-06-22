import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { runAirtableSync } from "../api/systemApi";

export function useRunAirtableSyncMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runAirtableSync,
    onSettled: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.system.airtableSyncStatus }),
        queryClient.invalidateQueries({ queryKey: queryKeys.catalog.products }),
        queryClient.invalidateQueries({ queryKey: queryKeys.catalog.categories }),
        queryClient.invalidateQueries({ queryKey: queryKeys.catalog.stations }),
        queryClient.invalidateQueries({ queryKey: queryKeys.catalog.paymentMethods }),
      ]);
    },
  });
}

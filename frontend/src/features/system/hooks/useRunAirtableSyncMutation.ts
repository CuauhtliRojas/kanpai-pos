import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { runAirtableSync } from "../api/systemApi";

export function useRunAirtableSyncMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runAirtableSync,
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.system.airtableSyncStatus });
    },
  });
}

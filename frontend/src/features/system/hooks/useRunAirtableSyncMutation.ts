import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import {
  pullAirtableCatalog,
  pushAirtableMovements,
  runAirtableSync,
} from "../api/systemApi";

function useSyncMutationInvalidation() {
  const queryClient = useQueryClient();

  return async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.system.airtableSyncStatus }),
      queryClient.invalidateQueries({ queryKey: queryKeys.catalog.products }),
      queryClient.invalidateQueries({ queryKey: queryKeys.catalog.categories }),
      queryClient.invalidateQueries({ queryKey: queryKeys.catalog.stations }),
      queryClient.invalidateQueries({ queryKey: queryKeys.catalog.paymentMethods }),
    ]);
  };
}

export function useRunAirtableSyncMutation() {
  const invalidateSyncData = useSyncMutationInvalidation();

  return useMutation({
    mutationFn: runAirtableSync,
    onSettled: invalidateSyncData,
  });
}

export function usePullAirtableCatalogMutation() {
  const invalidateSyncData = useSyncMutationInvalidation();

  return useMutation({
    mutationFn: pullAirtableCatalog,
    onSettled: invalidateSyncData,
  });
}

export function usePushAirtableMovementsMutation() {
  const invalidateSyncData = useSyncMutationInvalidation();

  return useMutation({
    mutationFn: pushAirtableMovements,
    onSettled: invalidateSyncData,
  });
}

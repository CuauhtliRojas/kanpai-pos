import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getAirtableSyncStatus } from "../api/systemApi";

export function useAirtableSyncStatusQuery() {
  return useQuery({
    queryKey: queryKeys.system.airtableSyncStatus,
    queryFn: getAirtableSyncStatus,
    refetchInterval: 30_000,
  });
}

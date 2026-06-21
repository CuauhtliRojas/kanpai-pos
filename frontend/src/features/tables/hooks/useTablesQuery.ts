import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTables } from "../api/tablesApi";

export function useTablesQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.tables.list,
    queryFn: getTables,
    enabled,
    retry: false,
  });
}

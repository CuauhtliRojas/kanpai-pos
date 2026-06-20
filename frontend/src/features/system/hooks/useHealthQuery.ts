import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getHealth } from "../api/systemApi";

export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.system.health,
    queryFn: getHealth,
  });
}

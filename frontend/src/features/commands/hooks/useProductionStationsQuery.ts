import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductionStations } from "../api/commandsApi";

export function useProductionStationsQuery(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.catalog.stations,
    queryFn: getProductionStations,
    enabled,
    retry: false,
  });
}

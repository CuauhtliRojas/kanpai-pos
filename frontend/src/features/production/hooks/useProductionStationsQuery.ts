import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductionStations } from "../api/productionApi";

export function useProductionStationsQuery() {
  return useQuery({
    queryKey: queryKeys.production.stations,
    queryFn: getProductionStations,
    retry: false,
  });
}

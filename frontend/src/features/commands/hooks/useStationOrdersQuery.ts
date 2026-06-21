import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getTicketStationOrders } from "../api/commandsApi";

export function useStationOrdersQuery(ticketId: number | null) {
  return useQuery({
    queryKey: queryKeys.commands.stationOrders(ticketId ?? 0),
    queryFn: () => getTicketStationOrders(ticketId as number),
    enabled: ticketId !== null,
    retry: false,
  });
}

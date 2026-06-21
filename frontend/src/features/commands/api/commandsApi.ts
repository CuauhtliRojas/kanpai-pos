import { apiRequest } from "../../../api/http";
import type {
  ProductionStation,
  SendRoundRequest,
  SendRoundResponse,
  StationOrder,
} from "../types/commandTypes";

export function sendTicketRound(
  ticketId: number,
  payload: SendRoundRequest,
): Promise<SendRoundResponse> {
  return apiRequest<SendRoundResponse>(`/api/v1/pos/tickets/${ticketId}/send-round`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTicketStationOrders(ticketId: number): Promise<StationOrder[]> {
  return apiRequest<StationOrder[]>(`/api/v1/pos/tickets/${ticketId}/station-orders`);
}

export function getProductionStations(): Promise<ProductionStation[]> {
  return apiRequest<ProductionStation[]>("/api/v1/catalog/stations");
}

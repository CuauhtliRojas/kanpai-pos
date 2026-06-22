import { apiRequest } from "../../../api/http";
import type {
  ReadonlyTicket,
  TicketHistoryFilters,
  TicketHistoryResponse,
} from "../types/ticketHistoryTypes";

export function getTicketHistory(filters: TicketHistoryFilters): Promise<TicketHistoryResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  });
  return apiRequest<TicketHistoryResponse>(`/api/v1/pos/ticket-history?${params.toString()}`);
}

export function getReadonlyTicket(ticketId: number): Promise<ReadonlyTicket> {
  return apiRequest<ReadonlyTicket>(`/api/v1/pos/tickets/${ticketId}/readonly`);
}

import { apiRequest } from "../../../api/http";
import type { TicketCancelRequest, TicketCancelResponse } from "../types/ticketCancelTypes";

export function cancelTicket(ticketId: number, payload: TicketCancelRequest): Promise<TicketCancelResponse> {
  return apiRequest<TicketCancelResponse>(`/api/v1/pos/tickets/${ticketId}/cancel`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

import { apiRequest } from "../../../api/http";
import type {
  TicketLine,
  TicketLineCreateRequest,
  TicketLinesCreatedResponse,
} from "../types/ticketTypes";

export function getTicketLines(ticketId: number): Promise<TicketLine[]> {
  return apiRequest<TicketLine[]>(`/api/v1/pos/tickets/${ticketId}/lines`);
}

export function addTicketLine(
  ticketId: number,
  payload: TicketLineCreateRequest,
): Promise<TicketLinesCreatedResponse> {
  return apiRequest<TicketLinesCreatedResponse>(
    `/api/v1/pos/tickets/${ticketId}/lines`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

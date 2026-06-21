import { apiRequest } from "../../../api/http";
import type { DiningTable, Ticket, TicketOpenRequest } from "../types/tableTypes";

export function getTables(): Promise<DiningTable[]> {
  return apiRequest<DiningTable[]>("/api/v1/operations/tables");
}

export function openTableTicket(
  tableId: number,
  payload: TicketOpenRequest,
): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/v1/pos/tables/${tableId}/open-ticket`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTicket(ticketId: number): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/v1/pos/tickets/${ticketId}`);
}

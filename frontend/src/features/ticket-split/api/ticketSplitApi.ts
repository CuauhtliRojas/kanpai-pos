import { apiRequest } from "../../../api/http";
import type { ByLinesSplitRequest, CancelSplitsRequest, CancelSplitsResponse, EqualSplitRequest, SplitPaymentRequest, SplitPaymentResponse, TicketSplit } from "../types/ticketSplitTypes";

export function getTicketSplits(ticketId: number): Promise<TicketSplit[]> {
  return apiRequest<TicketSplit[]>(`/api/v1/pos/tickets/${ticketId}/splits`);
}
export function createEqualSplits(ticketId: number, payload: EqualSplitRequest): Promise<TicketSplit[]> {
  return apiRequest<TicketSplit[]>(`/api/v1/pos/tickets/${ticketId}/splits/equal`, { method: "POST", body: JSON.stringify(payload) });
}
export function createLinesSplit(ticketId: number, payload: ByLinesSplitRequest): Promise<TicketSplit> {
  return apiRequest<TicketSplit>(`/api/v1/pos/tickets/${ticketId}/splits/by-lines`, { method: "POST", body: JSON.stringify(payload) });
}
export function payTicketSplit(splitId: number, payload: SplitPaymentRequest): Promise<SplitPaymentResponse> {
  return apiRequest<SplitPaymentResponse>(`/api/v1/pos/ticket-splits/${splitId}/payments`, { method: "POST", body: JSON.stringify(payload) });
}
export function cancelTicketSplits(ticketId: number, payload: CancelSplitsRequest): Promise<CancelSplitsResponse> {
  return apiRequest<CancelSplitsResponse>(`/api/v1/pos/tickets/${ticketId}/splits/cancel`, { method: "POST", body: JSON.stringify(payload) });
}

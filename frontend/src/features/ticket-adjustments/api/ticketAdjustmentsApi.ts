import { apiRequest } from "../../../api/http";
import type {
  CancelTicketLineRequest,
  CancelTicketLineResponse,
  ModifyTicketLineRequest,
  TicketLineModification,
} from "../types/ticketAdjustmentTypes";

export function modifyTicketLine(
  lineId: number,
  payload: ModifyTicketLineRequest,
): Promise<TicketLineModification> {
  return apiRequest<TicketLineModification>(`/api/v1/pos/ticket-lines/${lineId}/modify`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function cancelTicketLine(
  lineId: number,
  payload: CancelTicketLineRequest,
): Promise<CancelTicketLineResponse> {
  return apiRequest<CancelTicketLineResponse>(`/api/v1/pos/ticket-lines/${lineId}/cancel`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

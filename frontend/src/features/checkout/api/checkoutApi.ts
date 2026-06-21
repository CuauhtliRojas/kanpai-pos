import { apiRequest } from "../../../api/http";
import type { Ticket } from "../../tables/types/tableTypes";
import type { StartPaymentRequest } from "../types/checkoutTypes";

export function startCheckout(
  ticketId: number,
  payload: StartPaymentRequest,
): Promise<Ticket> {
  return apiRequest<Ticket>(`/api/v1/pos/tickets/${ticketId}/start-payment`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

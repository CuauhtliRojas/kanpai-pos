import { apiRequest } from "../../../api/http";
import type {
  PaymentCreateRequest,
  PaymentCreateResponse,
  PaymentMethod,
  PaymentSummary,
} from "../types/paymentTypes";

export function getPaymentMethods(): Promise<PaymentMethod[]> {
  return apiRequest<PaymentMethod[]>("/api/v1/catalog/payment-methods");
}

export function getTicketPayments(ticketId: number): Promise<PaymentSummary> {
  return apiRequest<PaymentSummary>(`/api/v1/pos/tickets/${ticketId}/payments`);
}

export function createTicketPayment(
  ticketId: number,
  payload: PaymentCreateRequest,
): Promise<PaymentCreateResponse> {
  return apiRequest<PaymentCreateResponse>(`/api/v1/pos/tickets/${ticketId}/payments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

import { apiRequest } from "../../../api/http";
import type { DiscountCreateRequest, DiscountPreset, TicketDiscount } from "../types/discountTypes";

export function getDiscountPresets(): Promise<DiscountPreset[]> {
  return apiRequest<DiscountPreset[]>("/api/v1/catalog/discount-presets");
}

export function getTicketDiscounts(ticketId: number): Promise<TicketDiscount[]> {
  return apiRequest<TicketDiscount[]>(`/api/v1/pos/tickets/${ticketId}/discounts`);
}

export function applyTicketDiscount(ticketId: number, payload: DiscountCreateRequest): Promise<TicketDiscount> {
  return apiRequest<TicketDiscount>(`/api/v1/pos/tickets/${ticketId}/discounts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

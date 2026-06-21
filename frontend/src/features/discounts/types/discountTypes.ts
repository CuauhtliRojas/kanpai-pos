export type DiscountType = "Monto" | "Porcentaje" | "Cortesia";

export type DiscountCreateRequest = {
  employee_id: number;
  discount_type: DiscountType;
  amount_cents: number | null;
  percent_bps: number | null;
  reason: string;
  is_courtesy: boolean;
};

export type TicketDiscount = {
  id: number;
  ticket_id: number;
  discount_type: DiscountType;
  amount_cents: number;
  percent_bps: number | null;
  reason: string | null;
  is_courtesy: boolean;
  authorized_by_employee_id: number | null;
  created_by_employee_id: number;
  created_at: string;
};

export type ApplyDiscountInput = {
  ticketId: number;
  payload: DiscountCreateRequest;
};

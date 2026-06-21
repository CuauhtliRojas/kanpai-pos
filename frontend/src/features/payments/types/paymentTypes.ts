export type PaymentMethod = {
  id: number;
  method_key: string;
  name: string;
  requires_reference: boolean;
  active: boolean;
};

export type PaymentCreateRequest = {
  employee_id: number;
  payment_method_id: number;
  amount_cents: number;
  received_cents?: number | null;
  reference?: string | null;
};

export type Payment = {
  id: number;
  folio: string;
  ticket_id: number;
  cash_shift_id: number;
  payment_method_id: number;
  cashier_employee_id: number;
  amount_cents: number;
  received_cents: number | null;
  change_cents: number;
  reference: string | null;
  status: string;
  cancelled_by_employee_id: number | null;
  cancel_reason: string | null;
  cancelled_at: string | null;
  created_at: string;
};

export type PaymentSummary = {
  ticket_id: number;
  payments: Payment[];
  total_paid_cents: number;
  remaining_cents: number;
  closed: boolean;
};

export type PaymentCreateResponse = {
  payment: Payment;
  ticket: Ticket;
  total_paid_cents: number;
  remaining_cents: number;
  closed: boolean;
};
import type { Ticket } from "../../tables/types/tableTypes";

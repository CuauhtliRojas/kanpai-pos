export type DiningTable = {
  id: number;
  table_code: string;
  display_name: string;
  buzzer_number: number | null;
  status: string;
  active: boolean;
};

export type TicketOpenRequest = {
  employee_id: number;
  guest_count?: number;
  waiter_employee_id?: number | null;
  note?: string | null;
};

export type Ticket = {
  id: number;
  folio: string;
  cash_shift_id: number;
  table_id: number;
  opened_by_employee_id: number;
  waiter_employee_id: number | null;
  guest_count: number;
  status: string;
  payment_status: string;
  note: string | null;
  opened_at: string;
  billing_started_at: string | null;
  paid_at: string | null;
  inventory_consumed_at: string | null;
  closed_by_employee_id: number | null;
  cancelled_by_employee_id: number | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  subtotal_cents: number;
  discount_cents: number;
  tax_cents: number;
  total_cents: number;
};

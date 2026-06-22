export type AuditEvent = {
  id: number;
  event_type: string;
  entity_type: string;
  entity_id: number;
  actor_employee_id: number | null;
  ticket_id: number | null;
  cash_shift_id: number | null;
  created_at: string;
  before_snapshot: string | null;
  after_snapshot: string | null;
  reason: string | null;
  metadata?: Record<string, unknown> | null;
};

export type AuditEventPage = {
  items: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
};

export type TicketAudit = {
  ticket: { folio: string; status: string; payment_status: string; total_cents: number; opened_at: string; paid_at: string | null; cancel_reason: string | null };
  lines: unknown[];
  payments: unknown[];
  discounts: unknown[];
  modifications: unknown[];
  station_orders: unknown[];
  print_jobs: unknown[];
  inventory_movements: unknown[];
  audit_events: AuditEvent[];
};

export type CashShiftAuditExpense = {
  id: number;
  folio: string;
  cash_shift_id: number;
  registered_by_employee_id: number;
  amount_cents: number;
  description: string;
  category: string | null;
  payment_method_id: number | null;
  note: string | null;
  status: string;
  created_at: string;
};

export type CashShiftAudit = {
  cash_shift: { folio: string; status: string; opened_at: string; closed_at: string | null };
  summary: { total_sales_cents: number; total_paid_cents: number; total_expenses_cents: number; ticket_count: number };
  tickets: unknown[];
  payments: unknown[];
  expenses: CashShiftAuditExpense[];
  print_jobs: unknown[];
  audit_events: AuditEvent[];
};

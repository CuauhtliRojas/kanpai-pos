export type CashShift = {
  id: number;
  folio: string;
  status: string;
  opened_by_employee_id: number;
  opened_at: string;
  opening_cash_cents: number;
  closed_by_employee_id: number | null;
  closed_at: string | null;
  declared_cash_cents: number | null;
  expected_cash_cents: number | null;
  cash_difference_cents: number | null;
  closing_note: string | null;
};

export type CashShiftOpen = {
  employee_id: number;
  opening_cash_cents: number;
};

export type CashShiftSummary = {
  cash_shift_id: number;
  folio: string;
  status: string;
  opened_at: string;
  opening_cash_cents: number;
  total_sales_cents: number;
  total_paid_cents: number;
  total_cash_cents: number;
  total_card_cents: number;
  total_transfer_cents: number;
  total_expenses_cents: number;
  expected_cash_cents: number;
  ticket_count: number;
  paid_ticket_count: number;
  cancelled_ticket_count: number;
  active_expense_count: number;
  pending_print_jobs_count: number;
};

export type CashShiftClose = {
  employee_id: number;
  declared_cash_cents: number;
  note?: string | null;
  allow_pending_print_jobs: boolean;
};

export type CashShiftCloseResult = {
  cash_shift: CashShift;
  summary: CashShiftSummary;
  print_job: unknown;
  closed: boolean;
};

export type CashExpense = {
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

export type CashExpenseCreate = {
  employee_id: number;
  amount_cents: number;
  description: string;
  category?: string | null;
  payment_method_id?: number | null;
  note?: string | null;
};

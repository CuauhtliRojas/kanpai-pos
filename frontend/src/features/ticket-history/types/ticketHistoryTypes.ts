import type { PrintJob } from "../../printing/types/printingTypes";
import type { Ticket } from "../../tables/types/tableTypes";
import type { TicketLine } from "../../tickets/types/ticketTypes";

export type TicketHistoryFilters = {
  cash_shift_id?: number;
  table_id?: number;
  q?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
};

export type TicketHistoryItem = {
  id: number;
  folio: string;
  table_id: number;
  table_name: string;
  cash_shift_id: number;
  status: string;
  payment_status: string;
  opened_at: string;
  paid_at: string | null;
  cancelled_at: string | null;
  subtotal_cents: number;
  discount_cents: number;
  tax_cents: number;
  total_cents: number;
  line_count: number;
  payment_count: number;
  print_job_count: number;
  payment_method_summary: string | null;
  latest_print_job_id: number | null;
  latest_ticket_print_job_id: number | null;
  can_reprint_ticket: boolean;
};

export type TicketHistoryResponse = {
  total: number;
  limit: number;
  offset: number;
  items: TicketHistoryItem[];
};

export type ReadonlyPayment = {
  id: number;
  folio: string;
  ticket_split_id: number | null;
  payment_method_name: string;
  amount_cents: number;
  change_cents: number;
  reference: string | null;
  status: string;
  created_at: string;
};

export type ReadonlyDiscount = {
  id: number;
  discount_type: string;
  amount_cents: number;
  reason: string | null;
};

export type ReadonlyStationOrder = {
  id: number;
  folio: string;
  status: string;
  created_at: string;
};

export type ReadonlyTicket = {
  ticket: Ticket;
  table: { id: number; table_code: string; display_name: string; buzzer_number: number | null };
  lines: (Omit<TicketLine, "variant_selections"> & {
    variant_selections: { id: number; name_snapshot: string; quantity: number }[];
    notes: { id: number; note_type: string; note: string }[];
  })[];
  discounts: ReadonlyDiscount[];
  payments: ReadonlyPayment[];
  splits: { id: number; name: string; amount_cents: number; status: string }[];
  print_jobs: (Omit<PrintJob, "content_snapshot" | "printer_key_snapshot" | "claimed_by" | "idempotency_key"> & { printer_key: string })[];
  station_orders: ReadonlyStationOrder[];
  audit_event_count: number;
  can_reprint_ticket: boolean;
  can_reprint_commands: boolean;
  is_readonly: true;
};

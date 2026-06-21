export type TicketLineCreateRequest = {
  product_id: number;
  employee_id: number;
  quantity?: number;
};

export type TicketLine = {
  id: number;
  ticket_id: number;
  parent_ticket_line_id: number | null;
  package_id: number | null;
  package_item_id: number | null;
  product_id: number;
  line_type: string;
  quantity: number;
  unit_price_cents: number;
  line_total_cents: number;
  price_mode: string;
  product_name_snapshot: string;
  product_sku_snapshot: string | null;
  category_id_snapshot: number | null;
  station_id_snapshot: number | null;
  note: string | null;
  status: string;
  created_by_employee_id: number;
  cancelled_by_employee_id: number | null;
  cancel_reason: string | null;
  cancelled_at: string | null;
};

export type TicketTotals = {
  subtotal_cents: number;
  discount_cents: number;
  tax_cents: number;
  total_cents: number;
};

export type TicketLinesCreatedResponse = {
  ticket_id: number;
  lines_created: TicketLine[];
  ticket_totals: TicketTotals;
};

export type SendRoundRequest = {
  employee_id: number;
};

export type SendRoundResponse = {
  ticket_id: number;
  command_batch_id: number;
  round_number: number;
  station_orders_created: number;
  print_jobs_created: number;
  lines_sent: number;
};

export type StationOrderLine = {
  id: number;
  ticket_line_id: number;
  quantity: number;
  product_name_snapshot: string;
  note_snapshot: string | null;
  line_action: string;
};

export type StationOrder = {
  id: number;
  command_batch_id: number;
  ticket_id: number;
  station_id: number;
  folio: string;
  status: string;
  created_at: string;
  lines: StationOrderLine[];
};

export type ProductionStation = {
  id: number;
  station_key: string;
  name: string;
  printer_key: string | null;
  sort_order: number;
  active: boolean;
  sync_status: string;
};

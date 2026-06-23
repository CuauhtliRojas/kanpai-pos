export type ProductionStation = {
  id: number;
  station_key: string;
  name: string;
  printer_key: string | null;
  sort_order: number;
  active: boolean;
  sync_status: string;
};

export type ProductionOrderStatus =
  | "En cola"
  | "Recibida"
  | "En preparacion"
  | "Terminada"
  | "Entregada"
  | "Cancelada";

export type ProductionOrderLine = {
  id: number;
  ticket_line_id: number;
  quantity: number;
  product_name_snapshot: string;
  note_snapshot: string | null;
  line_action: string;
};

export type ProductionOrder = {
  id: number;
  ticket_id: number;
  station_id: number;
  folio: string;
  status: ProductionOrderStatus;
  received_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  delivered_at: string | null;
  received_by_employee_id: number | null;
  started_by_employee_id: number | null;
  completed_by_employee_id: number | null;
  delivered_by_employee_id: number | null;
  created_at: string;
  lines: ProductionOrderLine[];
};

export type ProductionAction = "receive" | "start" | "complete" | "deliver";

export type ProductionActionInput = {
  orderId: number;
  stationId: number;
  employeeId: number;
};

export type ProductionOrdersParams = {
  stationId?: number;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
};

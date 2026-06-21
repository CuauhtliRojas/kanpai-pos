import type { TicketLine } from "../../tickets/types/ticketTypes";
import type { Ticket } from "../../tables/types/tableTypes";

export type ModifyTicketLineRequest = {
  employee_id: number;
  note: string;
};

export type TicketLineModification = {
  id: number;
  ticket_line_id: number;
  ticket_id: number;
  note: string;
  created_by_employee_id: number;
  created_at: string;
  print_job_id: number | null;
};

export type CancelTicketLineRequest = {
  employee_id: number;
  reason: string;
};

export type CancelTicketLineResponse = {
  line: TicketLine;
  ticket: Ticket;
  print_jobs_created: number;
};

export type TicketLineAdjustmentInput<TPayload> = {
  ticketId: number;
  lineId: number;
  payload: TPayload;
};

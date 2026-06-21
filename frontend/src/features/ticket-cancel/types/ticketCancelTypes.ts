import type { Ticket } from "../../tables/types/tableTypes";

export type TicketCancelRequest = { employee_id: number; reason: string | null };

export type TicketCancelResponse = {
  ticket: Ticket;
  lines_cancelled: number;
  payments_cancelled: number;
  print_jobs_created: number;
  table_released: boolean;
};

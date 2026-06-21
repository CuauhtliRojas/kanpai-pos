export type PrintJobStatus = "Pendiente" | "Tomado" | "Impreso" | "Fallido" | "Cancelado";

export type PrintJob = {
  id: number;
  folio: string;
  job_type: string;
  printer_id: number;
  printer_key_snapshot: string;
  ticket_id: number | null;
  cash_shift_id: number | null;
  station_order_id: number | null;
  command_batch_id: number | null;
  content_snapshot: string;
  status: PrintJobStatus;
  attempts: number;
  claimed_at: string | null;
  claimed_by: string | null;
  printed_at: string | null;
  failed_at: string | null;
  last_error: string | null;
  next_retry_at: string | null;
  idempotency_key: string;
  created_at: string;
};

export type ReprintInput = { jobId: number; employeeId: number; reason: string };
export type RetryPrintJobsResponse = { jobs_requeued: number };

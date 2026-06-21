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

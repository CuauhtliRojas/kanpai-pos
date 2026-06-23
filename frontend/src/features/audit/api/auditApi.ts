import { apiRequest } from "../../../api/http";
import type { AuditEventFilters, AuditEventPage, CashShiftAudit, TicketAudit } from "../types/auditTypes";

function setOptionalParam(searchParams: URLSearchParams, key: string, value: number | string | undefined) {
  if (value === undefined) return;
  const normalized = String(value).trim();
  if (!normalized) return;
  searchParams.set(key, normalized);
}

export function getAuditEvents(filters: AuditEventFilters): Promise<AuditEventPage> {
  const searchParams = new URLSearchParams();
  setOptionalParam(searchParams, "entity_type", filters.entityType);
  setOptionalParam(searchParams, "entity_id", filters.entityId);
  setOptionalParam(searchParams, "event_type", filters.eventType);
  setOptionalParam(searchParams, "actor_employee_id", filters.actorEmployeeId);
  setOptionalParam(searchParams, "date_from", filters.dateFrom);
  setOptionalParam(searchParams, "date_to", filters.dateTo);
  searchParams.set("limit", String(filters.limit));
  searchParams.set("offset", String(filters.offset));

  return apiRequest<AuditEventPage>(`/api/v1/audit/events?${searchParams.toString()}`);
}

export function getTicketAudit(ticketId: number): Promise<TicketAudit> {
  return apiRequest<TicketAudit>(`/api/v1/audit/tickets/${ticketId}`);
}

export function getCashShiftAudit(cashShiftId: number): Promise<CashShiftAudit> {
  return apiRequest<CashShiftAudit>(`/api/v1/audit/cash-shifts/${cashShiftId}`);
}

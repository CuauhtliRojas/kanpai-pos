import { apiRequest } from "../../../api/http";
import type { AuditEventPage, CashShiftAudit, TicketAudit } from "../types/auditTypes";

export function getAuditEvents(): Promise<AuditEventPage> {
  return apiRequest<AuditEventPage>("/api/v1/audit/events?limit=100&offset=0");
}

export function getTicketAudit(ticketId: number): Promise<TicketAudit> {
  return apiRequest<TicketAudit>(`/api/v1/audit/tickets/${ticketId}`);
}

export function getCashShiftAudit(cashShiftId: number): Promise<CashShiftAudit> {
  return apiRequest<CashShiftAudit>(`/api/v1/audit/cash-shifts/${cashShiftId}`);
}

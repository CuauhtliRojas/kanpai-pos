import { apiRequest } from "../../../api/http";
import type { AuditEventPage } from "../types/auditTypes";

export function getAuditEvents(): Promise<AuditEventPage> {
  return apiRequest<AuditEventPage>("/api/v1/audit/events?limit=100&offset=0");
}

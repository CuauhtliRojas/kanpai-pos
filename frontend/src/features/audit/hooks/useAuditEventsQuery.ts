import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getAuditEvents } from "../api/auditApi";
import type { AuditEventFilters } from "../types/auditTypes";

export function useAuditEventsQuery(filters: AuditEventFilters) {
  return useQuery({
    queryKey: queryKeys.audit.events(filters),
    queryFn: () => getAuditEvents(filters),
    retry: false,
  });
}

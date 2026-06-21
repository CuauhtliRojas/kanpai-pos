import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getAuditEvents } from "../api/auditApi";

export function useAuditEventsQuery() {
  return useQuery({ queryKey: queryKeys.audit.events, queryFn: getAuditEvents, retry: false });
}

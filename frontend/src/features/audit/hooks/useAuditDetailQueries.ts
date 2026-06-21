import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getCashShiftAudit, getTicketAudit } from "../api/auditApi";

export function useTicketAuditQuery(ticketId: number | null) {
  return useQuery({ queryKey: queryKeys.audit.ticket(ticketId ?? 0), queryFn: () => getTicketAudit(ticketId ?? 0), enabled: ticketId !== null, retry: false });
}
export function useCashShiftAuditQuery(cashShiftId: number | null) {
  return useQuery({ queryKey: queryKeys.audit.cashShift(cashShiftId ?? 0), queryFn: () => getCashShiftAudit(cashShiftId ?? 0), enabled: cashShiftId !== null, retry: false });
}

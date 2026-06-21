import { RefreshCw } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { AuditEventList } from "../components/AuditEventList";
import { useAuditEventsQuery } from "../hooks/useAuditEventsQuery";
import { useState } from "react";
import type { AuditEvent } from "../types/auditTypes";
import { useCashShiftAuditQuery, useTicketAuditQuery } from "../hooks/useAuditDetailQueries";
import { AuditDetailDialog } from "../components/AuditDetailDialog";

export function AuditPage() {
  const eventsQuery = useAuditEventsQuery();
  const [selection, setSelection] = useState<{ ticketId: number | null; cashShiftId: number | null } | null>(null);
  const ticketQuery = useTicketAuditQuery(selection?.ticketId ?? null);
  const cashShiftQuery = useCashShiftAuditQuery(selection?.ticketId === null ? selection.cashShiftId : null);
  function showDetail(event: AuditEvent) { setSelection({ ticketId: event.ticket_id, cashShiftId: event.cash_shift_id }); }
  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div><p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Eventos</p><h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Auditoría</h1></div>
        <BrutalButton onClick={() => void eventsQuery.refetch()} disabled={eventsQuery.isFetching}><RefreshCw className="h-5 w-5" /> Actualizar</BrutalButton>
      </header>
      {eventsQuery.isPending ? <LoadingState /> : eventsQuery.isError ? (
        <ErrorState title="No se pudo cargar Auditoría" message="Intenta de nuevo." />
      ) : <AuditEventList events={eventsQuery.data?.items ?? []} onDetail={showDetail} />}
      {selection ? <AuditDetailDialog ticket={ticketQuery.data ?? null} cashShift={cashShiftQuery.data ?? null} isLoading={selection.ticketId !== null ? ticketQuery.isPending : cashShiftQuery.isPending} hasError={selection.ticketId !== null ? ticketQuery.isError : cashShiftQuery.isError} onClose={() => setSelection(null)} /> : null}
    </div>
  );
}

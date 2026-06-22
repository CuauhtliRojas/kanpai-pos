import { useMemo, useState } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useTicketHistoryQuery } from "../hooks/useTicketHistoryQuery";
import type { TicketHistoryFilters } from "../types/ticketHistoryTypes";
import { TicketHistoryList } from "./TicketHistoryList";
import { TicketHistorySearch } from "./TicketHistorySearch";
import { TicketReadonlyDialog } from "./TicketReadonlyDialog";

type Props = {
  cashShiftId: number | null;
  initialTableId?: number;
  currentTableId: number | null;
  employeeId: number | null;
  canReprint: boolean;
  onClose: () => void;
};

export function TicketHistoryPanel({ cashShiftId, initialTableId, currentTableId, employeeId, canReprint, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string | undefined>();
  const [tableId, setTableId] = useState<number | undefined>(initialTableId);
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const filters = useMemo<TicketHistoryFilters>(() => ({
    cash_shift_id: cashShiftId ?? undefined,
    table_id: tableId,
    q: query.trim() || undefined,
    status,
    limit: 50,
    offset: 0,
  }), [cashShiftId, query, status, tableId]);
  const historyQuery = useTicketHistoryQuery(filters);
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-[rgba(0,0,0,0.72)]" role="dialog" aria-modal="true">
      <section className="h-full w-full max-w-2xl overflow-y-auto border-l-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="mb-4 flex items-start justify-between gap-3"><div><p className="text-xs font-black uppercase text-[var(--kp-selected)]">Ventas</p><h2 className="text-3xl font-black uppercase">Buscar tickets</h2></div><button type="button" aria-label="Cerrar historial" onClick={onClose} className="flex h-12 w-12 items-center justify-center border-4 border-[var(--kp-ink)]"><X /></button></header>
        <TicketHistorySearch query={query} status={status} tableId={tableId} currentTableId={currentTableId} onQueryChange={setQuery} onStatusChange={setStatus} onTableChange={setTableId} />
        {message ? <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 font-black">{message}</p> : null}
        <div className="mt-4">
          {historyQuery.isPending ? <p className="font-black uppercase">Consultando...</p> : historyQuery.isError ? <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold">No se pudo consultar el historial.</p> : <><p className="mb-2 text-sm font-black uppercase text-[var(--kp-muted)]">{historyQuery.data?.total ?? 0} ticket(s)</p><TicketHistoryList items={historyQuery.data?.items ?? []} onSelect={setSelectedTicketId} /></>}
        </div>
        <BrutalButton type="button" className="mt-4" fullWidth onClick={onClose}>Cerrar historial</BrutalButton>
      </section>
      {selectedTicketId !== null ? <TicketReadonlyDialog ticketId={selectedTicketId} employeeId={employeeId} canReprint={canReprint} onClose={() => setSelectedTicketId(null)} onQueued={() => { setMessage("Reimpresión enviada a cola"); void historyQuery.refetch(); }} /> : null}
    </div>
  );
}

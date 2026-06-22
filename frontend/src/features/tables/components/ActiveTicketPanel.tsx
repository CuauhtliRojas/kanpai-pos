import { ArrowLeftRight, CircleCheckBig } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { DiningTable, Ticket } from "../types/tableTypes";

type ActiveTicketPanelProps = {
  table: DiningTable;
  ticket: Ticket;
  onChangeTable: () => void;
  onSearchTickets: () => void;
};

export function ActiveTicketPanel({
  table,
  ticket,
  onChangeTable,
  onSearchTickets,
}: ActiveTicketPanelProps) {
  return (
    <aside className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
            Mesa actual
          </p>
          <h2 className="mt-1 text-3xl font-black uppercase">
            {table.display_name || table.table_code || `Mesa ${table.id}`}
          </h2>
          <p className="mt-1 flex items-center gap-2 font-black text-[var(--kp-success-text)]">
            <CircleCheckBig className="h-5 w-5" />
            Cuenta activa
          </p>
        </div>
        <div className="flex flex-wrap gap-2"><BrutalButton type="button" size="md" onClick={onSearchTickets}>Buscar tickets</BrutalButton><BrutalButton type="button" size="md" onClick={onChangeTable}><ArrowLeftRight className="h-5 w-5" />Cambiar mesa</BrutalButton></div>
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-2 border-t-4 border-[var(--kp-ink)] pt-3">
        <div>
          <dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Folio</dt>
          <dd className="mt-1 font-black">{ticket.folio}</dd>
        </div>
        <div>
          <dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Estado</dt>
          <dd className="mt-1 font-black">{ticket.status}</dd>
        </div>
        <div className="text-right">
          <dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Total</dt>
          <dd className="mt-1 text-xl font-black">{formatCentsToPesos(ticket.total_cents)}</dd>
        </div>
      </dl>
    </aside>
  );
}

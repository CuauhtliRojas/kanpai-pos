import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";
import type { TicketLine } from "../types/ticketTypes";
import { TicketLineItem } from "./TicketLineItem";

type ActiveTicketLinesPanelProps = {
  ticket: Ticket | null;
  lines: TicketLine[];
  isLoading: boolean;
  hasError: boolean;
};

export function ActiveTicketLinesPanel({
  ticket,
  lines,
  isLoading,
  hasError,
}: ActiveTicketLinesPanelProps) {
  if (!ticket) return null;

  return (
    <aside className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
            Cuenta activa
          </p>
          <h2 className="mt-1 text-2xl font-black uppercase">{ticket.folio}</h2>
        </div>
        <p className="text-xl font-black">{formatCentsToPesos(ticket.total_cents)}</p>
      </div>

      {isLoading ? (
        <p className="mt-4 font-bold">Consultando cuenta...</p>
      ) : hasError ? (
        <p className="mt-4 font-bold">No se pudo cargar la cuenta.</p>
      ) : lines.length === 0 ? (
        <p className="mt-4 font-bold text-[var(--kp-muted)]">Sin productos</p>
      ) : (
        <ul className="mt-3 max-h-64 overflow-y-auto pr-1">
          {lines.map((line) => (
            <TicketLineItem key={line.id} line={line} />
          ))}
        </ul>
      )}

    </aside>
  );
}

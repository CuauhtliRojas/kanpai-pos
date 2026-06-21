import type { ReactNode } from "react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketLine } from "../types/ticketTypes";

export function TicketLineItem({ line, actions }: { line: TicketLine; actions?: ReactNode }) {
  return (
    <li className="border-b-2 border-zinc-700 py-3 last:border-b-0">
      <div className="flex justify-between gap-3">
        <p className="font-black leading-tight">{line.product_name_snapshot}</p>
        <p className="shrink-0 font-black">{formatCentsToPesos(line.line_total_cents)}</p>
      </div>
      <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
        {line.quantity} × {formatCentsToPesos(line.unit_price_cents)}
      </p>
      {line.status === "Capturado" ? (
        <p className="mt-1 text-xs font-black uppercase tracking-wide text-amber-400">
          Pendiente de enviar
        </p>
      ) : null}
      {line.status === "Cancelado" ? (
        <p className="mt-1 text-xs font-black uppercase tracking-wide text-[var(--kp-danger-text)]">
          Cancelado
        </p>
      ) : null}
      {line.note ? (
        <p className="mt-2 border-l-4 border-[var(--kp-selected)] pl-2 text-sm font-bold">
          Nota: {line.note}
        </p>
      ) : null}
      {actions}
    </li>
  );
}

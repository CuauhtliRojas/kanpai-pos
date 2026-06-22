import type { ReactNode } from "react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketLine } from "../types/ticketTypes";

export function TicketLineItem({ line, actions }: { line: TicketLine; actions?: ReactNode }) {
  return (
    <li className="border-b-2 border-[var(--kp-divider)] py-3 last:border-b-0">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
        <div>
          <p className="font-black leading-tight">{line.product_name_snapshot}</p>
          <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
            {line.quantity} × {formatCentsToPesos(line.unit_price_cents)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <p className="shrink-0 font-black">{formatCentsToPesos(line.line_total_cents)}</p>
          {actions}
        </div>
      </div>
      {line.status === "Capturado" ? (
        <p className="mt-1 inline-flex border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-2 py-1 text-xs font-black uppercase tracking-wide text-[var(--kp-warning-contrast)]">
          Pendiente de enviar
        </p>
      ) : null}
      {line.status === "Cancelado" ? (
        <p className="mt-1 text-xs font-black uppercase tracking-wide text-[var(--kp-danger-text)]">
          Cancelado
        </p>
      ) : null}
      {line.status !== "Capturado" && line.status !== "Cancelado" ? (
        <p className="mt-1 inline-flex border-2 border-[var(--kp-ink)] bg-[var(--kp-info-bg)] px-2 py-1 text-xs font-black uppercase tracking-wide">
          Enviado
        </p>
      ) : null}
      {line.note ? (
        <p className="mt-2 border-l-4 border-[var(--kp-selected)] pl-2 text-sm font-bold">
          Nota: {line.note}
        </p>
      ) : null}
    </li>
  );
}

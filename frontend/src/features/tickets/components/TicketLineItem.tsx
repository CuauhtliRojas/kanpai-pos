import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketLine } from "../types/ticketTypes";

export function TicketLineItem({ line }: { line: TicketLine }) {
  return (
    <li className="border-b-2 border-zinc-700 py-3 last:border-b-0">
      <div className="flex justify-between gap-3">
        <p className="font-black leading-tight">{line.product_name_snapshot}</p>
        <p className="shrink-0 font-black">{formatCentsToPesos(line.line_total_cents)}</p>
      </div>
      <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
        {line.quantity} × {formatCentsToPesos(line.unit_price_cents)}
      </p>
      <p className="mt-1 text-xs font-black uppercase tracking-wide text-amber-400">
        Pendiente de enviar
      </p>
    </li>
  );
}

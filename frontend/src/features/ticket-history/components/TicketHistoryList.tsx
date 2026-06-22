import { formatNullableDate } from "../../../shared/lib/formatters";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketHistoryItem } from "../types/ticketHistoryTypes";

type Props = { items: TicketHistoryItem[]; onSelect: (ticketId: number) => void };

export function TicketHistoryList({ items, onSelect }: Props) {
  if (items.length === 0) {
    return <p className="border-4 border-[var(--kp-ink)] p-5 text-center font-black uppercase">No se encontraron tickets</p>;
  }
  return (
    <div className="grid gap-3">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onSelect(item.id)}
          className="grid min-h-24 gap-2 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-left shadow-[var(--kp-shadow-hard-sm)] active:translate-x-1 active:translate-y-1 active:shadow-none sm:grid-cols-[1fr_auto]"
        >
          <div>
            <p className="text-lg font-black">{item.folio}</p>
            <p className="font-bold">{item.table_name} · {item.status}</p>
            <p className="text-sm font-bold text-[var(--kp-muted)]">
              {formatNullableDate(item.paid_at ?? item.opened_at)}
              {item.payment_method_summary ? ` · ${item.payment_method_summary}` : ""}
            </p>
          </div>
          <div className="sm:text-right">
            <p className="text-xl font-black">{formatCentsToPesos(item.total_cents)}</p>
            <p className="text-xs font-black uppercase text-[var(--kp-muted)]">{item.line_count} productos</p>
          </div>
        </button>
      ))}
    </div>
  );
}

import { formatCentsToPesos } from "../../../shared/lib/money";
import type { SalesByProductItem } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

export function SalesByProductPanel({ items }: { items: SalesByProductItem[] }) {
  return (
    <ReportCard title="Ventas por producto">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-2">
          {items.map((item) => (
            <div key={item.product_id} className="flex items-start justify-between gap-4 border-t-2 border-zinc-700 pt-2 first:border-t-0 first:pt-0">
              <div><p className="font-black">{item.product_name}</p><p className="text-sm font-bold text-[var(--kp-muted)]">{item.quantity_sold} vendidos</p></div>
              <p className="shrink-0 font-black">{formatCentsToPesos(item.total_cents)}</p>
            </div>
          ))}
        </div>
      )}
    </ReportCard>
  );
}

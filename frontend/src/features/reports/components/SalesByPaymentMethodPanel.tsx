import { formatCentsToPesos } from "../../../shared/lib/money";
import type { SalesByPaymentMethodItem } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

export function SalesByPaymentMethodPanel({ items }: { items: SalesByPaymentMethodItem[] }) {
  return (
    <ReportCard title="Ventas por forma de pago">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-2">
          {items.map((item) => (
            <div key={item.payment_method_id} className="flex items-start justify-between gap-4 border-t-2 border-zinc-700 pt-2 first:border-t-0 first:pt-0">
              <div>
                <p className="font-black">{item.method_name}</p>
                <p className="text-sm font-bold text-[var(--kp-muted)]">{item.payment_count} pagos</p>
              </div>
              <p className="shrink-0 font-black">{formatCentsToPesos(item.total_cents)}</p>
            </div>
          ))}
        </div>
      )}
    </ReportCard>
  );
}

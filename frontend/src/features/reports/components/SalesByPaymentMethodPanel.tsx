import { formatCentsToPesos } from "../../../shared/lib/money";
import type { SalesByPaymentMethodItem } from "../types/reportTypes";
import { ReportBarRow } from "./ReportBarRow";
import { ReportCard } from "./ReportCard";

export function SalesByPaymentMethodPanel({ items }: { items: SalesByPaymentMethodItem[] }) {
  const maxValue = Math.max(0, ...items.map((item) => item.total_cents));

  return (
    <ReportCard title="Formas de pago">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-1">
          {items.map((item) => (
            <ReportBarRow
              key={item.payment_method_id}
              label={item.method_name}
              value={item.total_cents}
              maxValue={maxValue}
              valueLabel={formatCentsToPesos(item.total_cents)}
              meta={`${item.payment_count} pagos`}
              tone="warning"
            />
          ))}
        </div>
      )}
    </ReportCard>
  );
}

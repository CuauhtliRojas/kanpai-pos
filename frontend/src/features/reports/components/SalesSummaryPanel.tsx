import { formatCentsToPesos } from "../../../shared/lib/money";
import type { OperationalSummary } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

export function SalesSummaryPanel({ summary }: { summary: OperationalSummary }) {
  const items = [
    ["Ventas", formatCentsToPesos(summary.total_sales_cents)],
    ["Tickets", String(summary.paid_ticket_count)],
    ["Cancelaciones", String(summary.cancelled_ticket_count)],
    ["Cuentas abiertas", String(summary.open_ticket_count)],
  ];

  return (
    <ReportCard title="Ventas del día">
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map(([label, value]) => (
          <div key={label} className="bg-zinc-900 p-3">
            <p className="text-xs font-black uppercase text-[var(--kp-muted)]">{label}</p>
            <p className="mt-1 text-2xl font-black">{value}</p>
          </div>
        ))}
      </div>
    </ReportCard>
  );
}

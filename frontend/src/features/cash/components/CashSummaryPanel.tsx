import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { CashShiftSummary } from "../types/cashTypes";

type CashSummaryPanelProps = {
  summary: CashShiftSummary | undefined;
  isLoading: boolean;
  errorMessage: string | null;
};

export function CashSummaryPanel({
  summary,
  isLoading,
  errorMessage,
}: CashSummaryPanelProps) {
  if (isLoading) return <LoadingState />;
  if (errorMessage) {
    return <ErrorState title="No se pudo cargar el resumen" message={errorMessage} />;
  }
  if (!summary) return null;

  const amounts = [
    ["Fondo inicial", summary.opening_cash_cents],
    ["Ventas", summary.total_sales_cents],
    ["Efectivo recibido", summary.total_cash_cents],
    ["Tarjeta", summary.total_card_cents],
    ["Transferencia", summary.total_transfer_cents],
    ["Gastos", summary.total_expenses_cents],
    ["Efectivo esperado", summary.expected_cash_cents],
  ] as const;

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <h2 className="text-2xl font-black uppercase">Resumen</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {amounts.map(([label, value]) => (
          <div key={label} className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
            <p className="text-xs font-black uppercase tracking-[0.1em] text-[var(--kp-muted)]">{label}</p>
            <p className="mt-1 text-2xl font-black">{formatCentsToPesos(value)}</p>
          </div>
        ))}
      </div>
      <div className="mt-3 grid gap-3 text-sm font-black uppercase sm:grid-cols-3">
        <p>Ventas cobradas: {summary.paid_ticket_count}</p>
        <p>Ventas canceladas: {summary.cancelled_ticket_count}</p>
        <p>Gastos registrados: {summary.active_expense_count}</p>
      </div>
    </section>
  );
}

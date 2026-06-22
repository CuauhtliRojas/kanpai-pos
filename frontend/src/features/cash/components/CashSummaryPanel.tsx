import { ListChecks } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { CashShiftSummary } from "../types/cashTypes";

type CashSummaryPanelProps = {
  summary: CashShiftSummary | undefined;
  isLoading: boolean;
  errorMessage: string | null;
  onViewDetails: () => void;
};

export function CashSummaryPanel({
  summary,
  isLoading,
  errorMessage,
  onViewDetails,
}: CashSummaryPanelProps) {
  if (isLoading) return <LoadingState />;
  if (errorMessage) {
    return <ErrorState title="No se pudo cargar el resumen" message={errorMessage} />;
  }
  if (!summary) return null;

  const primaryAmounts = [
    ["Efectivo esperado", summary.expected_cash_cents, "bg-[var(--kp-success-bg)] text-[var(--kp-success-text)]"],
    ["Ventas", summary.total_sales_cents, "bg-[var(--kp-surface-raised)]"],
    ["Gastos", summary.total_expenses_cents, "bg-[var(--kp-surface-raised)]"],
    ["Efectivo recibido", summary.total_cash_cents, "bg-[var(--kp-surface-raised)]"],
  ] as const;

  const secondaryAmounts = [
    ["Fondo inicial", summary.opening_cash_cents],
    ["Ventas cobradas", summary.total_paid_cents],
    ["Tarjeta", summary.total_card_cents],
    ["Transferencia", summary.total_transfer_cents],
  ] as const;

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">Revisa antes de cerrar</p>
          <h2 className="text-2xl font-black uppercase">Resumen de caja</h2>
        </div>
        <BrutalButton type="button" size="md" onClick={onViewDetails}>
          <ListChecks className="h-5 w-5" />
          Ver detalle del turno
        </BrutalButton>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {primaryAmounts.map(([label, value, colorClass]) => (
          <div key={label} className={`border-4 border-[var(--kp-ink)] p-3 ${colorClass}`}>
            <p className="text-xs font-black uppercase tracking-[0.1em]">{label}</p>
            <p className="mt-1 text-2xl font-black">{formatCentsToPesos(value)}</p>
            {label === "Gastos" ? (
              <p className="mt-1 text-xs font-black uppercase">Gastos registrados: {summary.active_expense_count}</p>
            ) : null}
          </div>
        ))}
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {secondaryAmounts.map(([label, value]) => (
          <div key={label} className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2">
            <p className="text-xs font-black uppercase text-[var(--kp-muted)]">{label}</p>
            <p className="text-lg font-black">{formatCentsToPesos(value)}</p>
          </div>
        ))}
      </div>

      <div className="mt-3 grid gap-2 text-sm font-black uppercase sm:grid-cols-2 xl:grid-cols-4">
        <p className="border-l-4 border-[var(--kp-selected)] pl-2">Ventas cobradas: {summary.paid_ticket_count}</p>
        <p className="border-l-4 border-[var(--kp-selected)] pl-2">Ventas canceladas: {summary.cancelled_ticket_count}</p>
        <p className="border-l-4 border-[var(--kp-selected)] pl-2">Gastos registrados: {summary.active_expense_count}</p>
        <p className="border-l-4 border-[var(--kp-selected)] pl-2">Impresiones pendientes: {summary.pending_print_jobs_count}</p>
      </div>
    </section>
  );
}

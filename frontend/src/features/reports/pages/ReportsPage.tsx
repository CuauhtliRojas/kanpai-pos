import { RefreshCw } from "lucide-react";
import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { InventoryConsumptionPanel } from "../components/InventoryConsumptionPanel";
import { KpiTile } from "../components/KpiTile";
import { OperationsPanel } from "../components/OperationsPanel";
import { getPresetRange, ReportDateRangeFilter, type ReportRangePreset } from "../components/ReportDateRangeFilter";
import { SalesByCategoryPanel } from "../components/SalesByCategoryPanel";
import { SalesByPaymentMethodPanel } from "../components/SalesByPaymentMethodPanel";
import { SalesByProductPanel } from "../components/SalesByProductPanel";
import { useDailySalesReportQuery } from "../hooks/useDailySalesReportQuery";
import { useInventoryConsumptionQuery } from "../hooks/useInventoryConsumptionQuery";
import { usePrintJobsSummaryQuery } from "../hooks/usePrintJobsSummaryQuery";
import { useProductionTimesQuery } from "../hooks/useProductionTimesQuery";
import { useSalesByCategoryQuery } from "../hooks/useSalesByCategoryQuery";
import { useSalesByPaymentMethodQuery } from "../hooks/useSalesByPaymentMethodQuery";
import { useSalesByProductQuery } from "../hooks/useSalesByProductQuery";
import type { ReportDateRange } from "../types/reportTypes";

export function ReportsPage() {
  const [preset, setPreset] = useState<ReportRangePreset>("today");
  const [range, setRange] = useState<ReportDateRange>(() => getPresetRange("today"));

  const summaryQuery = useDailySalesReportQuery(range);
  const productsQuery = useSalesByProductQuery(range);
  const paymentMethodsQuery = useSalesByPaymentMethodQuery(range);
  const categoriesQuery = useSalesByCategoryQuery(range);
  const inventoryConsumptionQuery = useInventoryConsumptionQuery(range);
  const timesQuery = useProductionTimesQuery(range);
  const printingQuery = usePrintJobsSummaryQuery(range);
  const queries = [
    summaryQuery,
    productsQuery,
    paymentMethodsQuery,
    categoriesQuery,
    inventoryConsumptionQuery,
    timesQuery,
    printingQuery,
  ];
  const isPending = queries.some((query) => query.isPending);
  const isError = queries.some((query) => query.isError);
  const isFetching = queries.some((query) => query.isFetching);

  function handlePresetChange(nextPreset: ReportRangePreset) {
    setPreset(nextPreset);
    if (nextPreset !== "custom") {
      setRange(getPresetRange(nextPreset));
    }
  }

  return (
    <div className="grid gap-4">
      <header className="grid gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)] xl:grid-cols-[minmax(0,1fr)_auto] xl:items-start">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Administración</p>
          <h1 className="mt-1 text-3xl font-black uppercase leading-none md:text-5xl">Reportes</h1>
          <p className="mt-2 max-w-3xl text-sm font-bold text-[var(--kp-muted)] md:text-base">
            Consulta ventas, operación e inventario del periodo.
          </p>
        </div>
        <BrutalButton onClick={() => void Promise.all(queries.map((query) => query.refetch()))} disabled={isFetching}>
          <RefreshCw className="h-5 w-5" /> Actualizar
        </BrutalButton>
        <div className="xl:col-span-2">
          <ReportDateRangeFilter
            preset={preset}
            range={range}
            onPresetChange={handlePresetChange}
            onRangeChange={(nextRange) => {
              setPreset("custom");
              setRange(nextRange);
            }}
          />
        </div>
      </header>

      {isPending ? <LoadingState /> : isError ? (
        <ErrorState title="No se pudieron cargar los reportes" message="Intenta de nuevo." />
      ) : summaryQuery.data ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores del periodo">
            <KpiTile label="Ventas" value={formatCentsToPesos(summaryQuery.data.total_sales_cents)} tone="success" />
            <KpiTile label="Pagado" value={formatCentsToPesos(summaryQuery.data.total_paid_cents)} tone="success" />
            <KpiTile label="Gastos" value={formatCentsToPesos(summaryQuery.data.total_expenses_cents)} tone={summaryQuery.data.total_expenses_cents > 0 ? "warning" : "neutral"} />
            <KpiTile
              label="Neto caja"
              value={formatCentsToPesos(summaryQuery.data.net_cash_cents)}
              tone={summaryQuery.data.net_cash_cents >= 0 ? "success" : "danger"}
            />
            <KpiTile label="Tickets cobrados" value={summaryQuery.data.paid_ticket_count} tone="neutral" />
            <KpiTile label="Cancelaciones" value={summaryQuery.data.cancelled_ticket_count} tone={summaryQuery.data.cancelled_ticket_count > 0 ? "danger" : "neutral"} />
            <KpiTile label="Cuentas abiertas" value={summaryQuery.data.open_ticket_count} tone={summaryQuery.data.open_ticket_count > 0 ? "warning" : "neutral"} />
            <KpiTile
              label="Impresiones pendientes/fallidas"
              value={`${summaryQuery.data.pending_print_jobs_count}/${summaryQuery.data.failed_print_jobs_count}`}
              detail="Pendientes / fallidas"
              tone={summaryQuery.data.failed_print_jobs_count > 0 ? "danger" : summaryQuery.data.pending_print_jobs_count > 0 ? "warning" : "neutral"}
            />
          </section>

          <section className="grid items-start gap-4 xl:grid-cols-2">
            <SalesByProductPanel items={productsQuery.data ?? []} />
            <SalesByCategoryPanel items={categoriesQuery.data ?? []} />
            <SalesByPaymentMethodPanel items={paymentMethodsQuery.data ?? []} />
            <InventoryConsumptionPanel items={inventoryConsumptionQuery.data ?? []} />
          </section>

          <OperationsPanel times={timesQuery.data ?? []} printing={printingQuery.data} />
        </>
      ) : null}
    </div>
  );
}

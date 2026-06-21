import { RefreshCw } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { OperationsPanel } from "../components/OperationsPanel";
import { ReportCard } from "../components/ReportCard";
import { SalesByProductPanel } from "../components/SalesByProductPanel";
import { SalesSummaryPanel } from "../components/SalesSummaryPanel";
import { useDailySalesReportQuery } from "../hooks/useDailySalesReportQuery";
import { usePrintJobsSummaryQuery } from "../hooks/usePrintJobsSummaryQuery";
import { useProductionTimesQuery } from "../hooks/useProductionTimesQuery";
import { useSalesByProductQuery } from "../hooks/useSalesByProductQuery";

export function ReportsPage() {
  const summaryQuery = useDailySalesReportQuery();
  const productsQuery = useSalesByProductQuery();
  const timesQuery = useProductionTimesQuery();
  const printingQuery = usePrintJobsSummaryQuery();
  const queries = [summaryQuery, productsQuery, timesQuery, printingQuery];
  const isPending = queries.some((query) => query.isPending);
  const isError = queries.some((query) => query.isError);

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div><p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Administración</p><h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Reportes</h1></div>
        <BrutalButton onClick={() => void Promise.all(queries.map((query) => query.refetch()))} disabled={queries.some((query) => query.isFetching)}>
          <RefreshCw className="h-5 w-5" /> Actualizar
        </BrutalButton>
      </header>

      {isPending ? <LoadingState /> : isError ? (
        <ErrorState title="No se pudieron cargar los reportes" message="Intenta de nuevo." />
      ) : summaryQuery.data && productsQuery.data && timesQuery.data ? (
        <>
          <div className="grid items-start gap-4 xl:grid-cols-2">
            <SalesSummaryPanel summary={summaryQuery.data} />
            <SalesByProductPanel items={productsQuery.data} />
          </div>
          <ReportCard title="Ventas por categoría"><p className="font-black uppercase text-[var(--kp-muted)]">En preparación</p></ReportCard>
          <OperationsPanel times={timesQuery.data} printing={printingQuery.data} />
        </>
      ) : null}
    </div>
  );
}

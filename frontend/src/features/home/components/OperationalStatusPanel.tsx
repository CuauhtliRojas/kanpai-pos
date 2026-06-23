import { CircleDollarSign, DatabaseZap, PackageSearch, Printer } from "lucide-react";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { SurfaceCard } from "../../../shared/components/SurfaceCard";
import { useCurrentCashShiftQuery } from "../../cash/hooks/useCurrentCashShiftQuery";
import { useStockAlertsQuery } from "../../inventory/hooks/useStockAlertsQuery";
import { usePrintJobsQuery } from "../../printing/hooks/usePrintJobsQuery";
import { useAirtableSyncStatusQuery } from "../../system/hooks/useAirtableSyncStatusQuery";

type StatusTone = "ok" | "warning" | "danger" | "neutral" | "info";

function syncSummary(status: string | undefined, running: boolean | undefined) {
  if (running) return { label: "Actualizando", tone: "info" as StatusTone };
  if (!status) return { label: "Sin revisar", tone: "neutral" as StatusTone };
  if (status.includes("success")) return { label: "Datos al día", tone: "ok" as StatusTone };
  return { label: "Datos pendientes", tone: "warning" as StatusTone };
}

export function OperationalStatusPanel() {
  const cashQuery = useCurrentCashShiftQuery();
  const syncQuery = useAirtableSyncStatusQuery();
  const printJobsQuery = usePrintJobsQuery();
  const stockAlertsQuery = useStockAlertsQuery();

  const cashShift = cashQuery.data ?? null;
  const printJobs = printJobsQuery.data ?? [];
  const stockAlerts = stockAlertsQuery.data ?? [];
  const sync = syncSummary(syncQuery.data?.last_status, syncQuery.data?.running);

  const items = [
    {
      label: "Caja",
      value: cashQuery.isPending
        ? "Revisando"
        : cashQuery.isError
          ? "No disponible"
          : cashShift
            ? "Abierta"
            : "Cerrada",
      tone: cashQuery.isPending
        ? "info"
        : cashQuery.isError
          ? "warning"
          : cashShift
            ? "ok"
            : "warning",
      icon: CircleDollarSign,
    },
    {
      label: "Datos",
      value: syncQuery.isError ? "Revisar datos" : sync.label,
      tone: syncQuery.isError ? "warning" : sync.tone,
      icon: DatabaseZap,
    },
    {
      label: "Impresión",
      value: printJobsQuery.isPending
        ? "Revisando"
        : printJobsQuery.isError
          ? "No disponible"
          : printJobs.length === 0
            ? "Sin pendientes"
            : `${printJobs.length} pendientes`,
      tone: printJobsQuery.isPending
        ? "info"
        : printJobsQuery.isError
          ? "warning"
          : printJobs.length === 0
            ? "ok"
            : "warning",
      icon: Printer,
    },
    {
      label: "Stock",
      value: stockAlertsQuery.isPending
        ? "Revisando"
        : stockAlertsQuery.isError
          ? "No disponible"
          : stockAlerts.length === 0
            ? "Sin alertas"
            : `${stockAlerts.length} alertas`,
      tone: stockAlertsQuery.isPending
        ? "info"
        : stockAlertsQuery.isError
          ? "warning"
          : stockAlerts.length === 0
            ? "ok"
            : "danger",
      icon: PackageSearch,
    },
  ] satisfies {
    label: string;
    value: string;
    tone: StatusTone;
    icon: typeof CircleDollarSign;
  }[];

  return (
    <SurfaceCard title="Estado operativo" eyebrow="Turno">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="min-w-0 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 shadow-[var(--kp-shadow-hard-sm)]"
            >
              <div className="flex items-center justify-between gap-3">
                <Icon className="h-5 w-5 shrink-0 text-[var(--kp-selected)]" aria-hidden="true" />
                <StatusBadge label={item.value} tone={item.tone} />
              </div>
              <p className="mt-3 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                {item.label}
              </p>
            </div>
          );
        })}
      </div>
    </SurfaceCard>
  );
}

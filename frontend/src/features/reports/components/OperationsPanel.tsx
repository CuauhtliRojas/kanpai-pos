import type { PrintJobsSummary, ProductionTimesItem } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

function formatSeconds(value: number | null): string {
  if (value === null) return "Sin datos";
  if (value < 60) return `${Math.round(value)} s`;
  return `${(value / 60).toFixed(1)} min`;
}

export function OperationsPanel({ times, printing }: { times: ProductionTimesItem[]; printing: PrintJobsSummary | undefined }) {
  const hasFailedPrints = (printing?.failed_count ?? 0) > 0;

  return (
    <ReportCard title="Operación">
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.75fr)]">
        <div className="grid gap-2">
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Producción por estación</p>
          {times.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : times.map((item) => (
            <div key={item.station_id} className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-3">
              <div className="flex justify-between gap-3">
                <p className="font-black">{item.station_name}</p>
                <p className="font-bold">{item.orders_count} comandas</p>
              </div>
              <div className="mt-2 grid gap-1 text-sm font-bold text-[var(--kp-muted)] sm:grid-cols-3">
                <p>Recepción: {formatSeconds(item.average_receive_seconds)}</p>
                <p>Preparación: {formatSeconds(item.average_prepare_seconds)}</p>
                <p>Servicio: {formatSeconds(item.average_total_service_seconds)}</p>
              </div>
            </div>
          ))}
        </div>
        <div className={`border-4 border-[var(--kp-ink)] p-3 ${hasFailedPrints ? "bg-[var(--kp-danger-bg)] text-[var(--kp-danger-text)]" : "bg-[var(--kp-bg-alt)]"}`}>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Impresión</p>
          {printing ? (
            <div className="mt-3 grid grid-cols-2 gap-2">
              <div><p className="text-xs font-black uppercase opacity-80">Total</p><p className="text-2xl font-black">{printing.total_print_jobs}</p></div>
              <div><p className="text-xs font-black uppercase opacity-80">Reimpresiones</p><p className="text-2xl font-black">{printing.reprint_count}</p></div>
              <div><p className="text-xs font-black uppercase opacity-80">Pendientes</p><p className="text-2xl font-black text-[var(--kp-warning-text)]">{printing.pending_count}</p></div>
              <div><p className="text-xs font-black uppercase opacity-80">Fallidas</p><p className="text-2xl font-black text-[var(--kp-danger-text)]">{printing.failed_count}</p></div>
            </div>
          ) : <p className="mt-3 font-bold text-[var(--kp-muted)]">Sin datos</p>}
        </div>
      </div>
    </ReportCard>
  );
}

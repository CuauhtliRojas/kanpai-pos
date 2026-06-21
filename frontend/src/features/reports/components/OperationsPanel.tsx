import type { PrintJobsSummary, ProductionTimesItem } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

function formatSeconds(value: number | null): string {
  if (value === null) return "Sin datos";
  if (value < 60) return `${Math.round(value)} s`;
  return `${(value / 60).toFixed(1)} min`;
}

export function OperationsPanel({ times, printing }: { times: ProductionTimesItem[]; printing: PrintJobsSummary | undefined }) {
  return (
    <ReportCard title="Operación">
      <div className="grid gap-4">
        {times.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : times.map((item) => (
          <div key={item.station_id} className="bg-zinc-900 p-3">
            <div className="flex justify-between gap-3"><p className="font-black">{item.station_name}</p><p className="font-bold">{item.orders_count} comandas</p></div>
            <div className="mt-2 grid gap-1 text-sm font-bold text-[var(--kp-muted)] sm:grid-cols-3">
              <p>Recepción: {formatSeconds(item.average_receive_seconds)}</p>
              <p>Preparación: {formatSeconds(item.average_prepare_seconds)}</p>
              <p>Servicio: {formatSeconds(item.average_total_service_seconds)}</p>
            </div>
          </div>
        ))}
        {printing ? (
          <div className="grid grid-cols-2 gap-3 border-t-2 border-zinc-700 pt-3 sm:grid-cols-4">
            <div><p className="text-xs font-black uppercase text-[var(--kp-muted)]">Impresiones</p><p className="text-xl font-black">{printing.total_print_jobs}</p></div>
            <div><p className="text-xs font-black uppercase text-[var(--kp-muted)]">Reimpresiones</p><p className="text-xl font-black">{printing.reprint_count}</p></div>
            <div><p className="text-xs font-black uppercase text-[var(--kp-muted)]">Pendientes</p><p className="text-xl font-black">{printing.pending_count}</p></div>
            <div><p className="text-xs font-black uppercase text-[var(--kp-muted)]">Fallidas</p><p className="text-xl font-black">{printing.failed_count}</p></div>
          </div>
        ) : null}
      </div>
    </ReportCard>
  );
}

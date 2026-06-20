import { RefreshCw } from "lucide-react";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { SurfaceCard } from "../../../shared/components/SurfaceCard";
import { getErrorMessage } from "../../../shared/lib/errors";
import { formatNullableDate } from "../../../shared/lib/formatters";
import { useAirtableSyncStatusQuery } from "../hooks/useAirtableSyncStatusQuery";

function syncTone(status: string, running: boolean) {
  if (running) {
    return "info";
  }

  if (status.includes("error") || status.includes("missing")) {
    return "danger";
  }

  if (status.includes("disabled") || status === "not_started") {
    return "warning";
  }

  if (status.includes("success")) {
    return "ok";
  }

  return "neutral";
}

function syncLabel(status: string, running: boolean) {
  if (running) {
    return "Actualizando";
  }

  if (status.includes("error") || status.includes("missing")) {
    return "Revisar";
  }

  if (status.includes("disabled")) {
    return "Pausado";
  }

  if (status === "not_started") {
    return "Pendiente";
  }

  if (status.includes("success")) {
    return "Al dia";
  }

  return "Estado";
}

export function AirtableSyncStatusCard() {
  const syncQuery = useAirtableSyncStatusQuery();

  if (syncQuery.isPending) {
    return (
      <SurfaceCard title="Actualizacion" eyebrow="Estado">
        <LoadingState />
      </SurfaceCard>
    );
  }

  if (syncQuery.isError) {
    return (
      <SurfaceCard title="Actualizacion" eyebrow="Estado">
        <ErrorState
          title="Sin conexion"
          message={getErrorMessage(syncQuery.error)}
        />
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard
      title="Actualizacion"
      eyebrow="Estado"
      action={
        <StatusBadge
          label={syncLabel(syncQuery.data.last_status, syncQuery.data.running)}
          tone={syncTone(syncQuery.data.last_status, syncQuery.data.running)}
        />
      }
    >
      <div className="grid gap-4">
        <div className="flex items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-sm font-bold text-[var(--kp-text)]">
          <RefreshCw className="h-6 w-6 text-[var(--kp-selected)]" />
          <span>
            La informacion se revisa automaticamente cada {syncQuery.data.interval_minutes} minutos.
          </span>
        </div>

        <dl className="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
            <dt className="font-black uppercase text-[var(--kp-selected)]">Entrada de datos</dt>
            <dd className="mt-1 text-lg font-black text-[var(--kp-text)]">
              {syncQuery.data.pull_enabled ? "Activa" : "Pausada"}
            </dd>
          </div>
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
            <dt className="font-black uppercase text-[var(--kp-selected)]">Salida de datos</dt>
            <dd className="mt-1 text-lg font-black text-[var(--kp-text)]">
              {syncQuery.data.push_enabled ? "Activa" : "Pausada"}
            </dd>
          </div>
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
            <dt className="font-black uppercase text-[var(--kp-selected)]">Ultimo inicio</dt>
            <dd className="mt-1 text-lg font-black text-[var(--kp-text)]">
              {formatNullableDate(syncQuery.data.last_started_at)}
            </dd>
          </div>
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
            <dt className="font-black uppercase text-[var(--kp-selected)]">Ultimo cierre</dt>
            <dd className="mt-1 text-lg font-black text-[var(--kp-text)]">
              {formatNullableDate(syncQuery.data.last_finished_at)}
            </dd>
          </div>
        </dl>

        {syncQuery.data.last_error ? (
          <ErrorState title="Ultimo problema" message={syncQuery.data.last_error} />
        ) : null}
      </div>
    </SurfaceCard>
  );
}

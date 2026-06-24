import { RefreshCw } from "lucide-react";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { formatNullableDate } from "../../../shared/lib/formatters";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasPermission, hasRole } from "../../auth/lib/permissions";
import { useAirtableSyncStatusQuery } from "../hooks/useAirtableSyncStatusQuery";
import { SyncActionPanel } from "./SyncActionPanel";

function syncTone(status: string, running: boolean) {
  if (running) return "info";
  if (status.includes("error") || status.includes("missing")) return "danger";
  if (
    status.includes("disabled") ||
    status.includes("no_directions") ||
    status.includes("skipped") ||
    status === "not_started"
  ) {
    return "warning";
  }
  if (status.includes("success")) return "ok";
  return "neutral";
}

export function syncLabel(status: string, running: boolean) {
  if (running) return "Actualizando";
  if (status === "success_pull_skipped_active_operation") {
    return "Catálogo omitido";
  }
  if (status.includes("missing")) return "Falta configuración";
  if (status.includes("error")) return "Error";
  if (status.includes("success")) return "Datos actualizados";
  return "Revisar datos";
}

function lastResultLabel(status: string) {
  if (status === "success") return "Datos actualizados";
  if (status === "success_pull_skipped_active_operation") {
    return "Catálogo omitido por operación activa";
  }
  if (status.includes("missing")) return "Falta configuración";
  if (status.includes("error")) return "Error";
  if (status === "manual_running" || status === "running") return "Actualizando";
  if (status === "not_started") return "Aún no se ha realizado";
  return "Revisar datos";
}

export function AirtableSyncStatusCard() {
  const syncQuery = useAirtableSyncStatusQuery();
  const { permissions, roles } = useAuthSession();

  if (syncQuery.isPending) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <LoadingState />
      </section>
    );
  }

  if (syncQuery.isError) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-warning)]">
              Sistema
            </p>
            <h2 className="mt-1 text-2xl font-black uppercase leading-none">
              Actualización de datos
            </h2>
          </div>
          <StatusBadge label="Revisar datos" tone="warning" />
        </div>
        <ErrorState
          title="Revisar sistema"
          message="No se pudo revisar la información. Revisa conexión o pide ayuda."
        />
      </section>
    );
  }

  const statusLabel = syncLabel(syncQuery.data.last_status, syncQuery.data.running);
  const statusTone = syncTone(syncQuery.data.last_status, syncQuery.data.running);

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <header className="flex flex-col gap-3 border-b-4 border-[var(--kp-ink)] pb-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-warning)]">
            Sistema
          </p>
          <h2 className="mt-1 text-2xl font-black uppercase leading-none">
            Actualización de datos
          </h2>
          <p className="mt-2 max-w-3xl text-sm font-bold leading-5 text-[var(--kp-muted)]">
            Revisa catálogo, fotos y movimientos pendientes con oficina.
          </p>
        </div>
        <StatusBadge label={statusLabel} tone={statusTone} />
      </header>

      <div className="mt-3 grid gap-3">
        <div className="flex items-center gap-3 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 py-2 text-sm font-bold">
          <RefreshCw className="h-5 w-5 shrink-0 text-[var(--kp-selected)]" />
          <span>
            Revisión automática cada {syncQuery.data.interval_minutes} minutos.
          </span>
        </div>

        <dl className="grid gap-2 text-sm md:grid-cols-5">
          <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 py-2 md:col-span-2">
            <dt className="text-xs font-black uppercase tracking-[0.1em] text-[var(--kp-muted)]">
              Última revisión
            </dt>
            <dd className="mt-1 font-black">
              {syncQuery.data.last_started_at
                ? formatNullableDate(syncQuery.data.last_started_at)
                : "Aún no se ha realizado"}
            </dd>
          </div>
          <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 py-2 md:col-span-2">
            <dt className="text-xs font-black uppercase tracking-[0.1em] text-[var(--kp-muted)]">
              Terminó
            </dt>
            <dd className="mt-1 font-black">
              {syncQuery.data.last_finished_at
                ? formatNullableDate(syncQuery.data.last_finished_at)
                : "Aún no se ha realizado"}
            </dd>
          </div>
          <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 py-2">
            <dt className="text-xs font-black uppercase tracking-[0.1em] text-[var(--kp-muted)]">
              Resultado
            </dt>
            <dd className="mt-1 font-black">{lastResultLabel(syncQuery.data.last_status)}</dd>
          </div>
        </dl>

        <div className="flex flex-wrap gap-2">
          <span className="inline-flex min-h-9 items-center border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-xs font-black uppercase tracking-[0.08em]">
            Recibir catálogo: {syncQuery.data.pull_enabled ? "Activa" : "Desactivada"}
          </span>
          <span className="inline-flex min-h-9 items-center border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-xs font-black uppercase tracking-[0.08em]">
            Enviar movimientos: {syncQuery.data.push_enabled ? "Activa" : "Desactivada"}
          </span>
        </div>

        <SyncActionPanel
          canRun={hasRole(roles, "ADMIN") || hasPermission(permissions, "SUPPORT_ACCESS")}
          syncEnabled={syncQuery.data.enabled}
          pullEnabled={syncQuery.data.pull_enabled}
          pushEnabled={syncQuery.data.push_enabled}
          running={syncQuery.data.running}
        />

        {syncQuery.data.last_error ? (
          <ErrorState
            title="Revisar sistema"
            message="No se pudo revisar la información. Revisa conexión o pide ayuda."
          />
        ) : null}
      </div>
    </section>
  );
}

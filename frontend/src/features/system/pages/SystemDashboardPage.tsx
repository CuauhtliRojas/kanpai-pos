import { StatusBadge } from "../../../shared/components/StatusBadge";
import { AirtableSyncStatusCard, syncLabel } from "../components/AirtableSyncStatusCard";
import { DiagnosticsPanel } from "../components/DiagnosticsPanel";
import { HealthStatusCard } from "../components/HealthStatusCard";
import { useAirtableSyncStatusQuery } from "../hooks/useAirtableSyncStatusQuery";
import { usePreflightQuery } from "../hooks/usePreflightQuery";

type StatusTone = "ok" | "warning" | "danger" | "neutral" | "info";

const criticalReviewKeys = new Set([
  "database",
  "migrations",
  "seed_admin",
  "single_open_cash_shift",
  "single_active_ticket_per_table",
  "paid_ticket_inventory",
  "cancelled_ticket_payments",
  "print_job_printer_snapshot",
  "sale_inventory_source",
]);

function dataTone(status: string, running: boolean): StatusTone {
  if (running) return "info";
  if (status.includes("error") || status.includes("missing")) return "danger";
  if (status.includes("skipped") || status === "not_started") return "warning";
  if (status.includes("success")) return "ok";
  return "neutral";
}

function DataStatusCard() {
  const syncQuery = useAirtableSyncStatusQuery();

  if (syncQuery.isPending) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
          Datos
        </p>
        <h2 className="mt-1 text-xl font-black uppercase">Revisando</h2>
      </section>
    );
  }

  if (syncQuery.isError) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
              Datos
            </p>
            <h2 className="mt-1 text-xl font-black uppercase">Revisar datos</h2>
          </div>
          <StatusBadge label="Revisar" tone="warning" />
        </div>
        <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
          No se pudo revisar el estado de actualización.
        </p>
      </section>
    );
  }

  const label = syncLabel(syncQuery.data.last_status, syncQuery.data.running);

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
            Datos
          </p>
          <h2 className="mt-1 text-xl font-black uppercase">{label}</h2>
        </div>
        <StatusBadge label={label} tone={dataTone(syncQuery.data.last_status, syncQuery.data.running)} />
      </div>
      <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
        Catálogo, fotos y movimientos.
      </p>
    </section>
  );
}

function ReviewStatusCard() {
  const preflightQuery = usePreflightQuery();

  if (preflightQuery.isPending) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
          Revisión operativa
        </p>
        <h2 className="mt-1 text-xl font-black uppercase">Revisando</h2>
      </section>
    );
  }

  if (preflightQuery.isError) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
              Revisión operativa
            </p>
            <h2 className="mt-1 text-xl font-black uppercase">Revisar</h2>
          </div>
          <StatusBadge label="Revisar" tone="warning" />
        </div>
        <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
          No se pudo completar la revisión.
        </p>
      </section>
    );
  }

  const checks = preflightQuery.data.checks;
  const hasCritical = checks.some(
    (check) => check.status === "ERROR" && criticalReviewKeys.has(check.key),
  );
  const hasReview =
    checks.some((check) => check.status !== "OK") ||
    preflightQuery.data.summary.open_tickets > 0 ||
    preflightQuery.data.summary.in_payment_tickets > 0 ||
    preflightQuery.data.summary.pending_print_jobs > 0 ||
    preflightQuery.data.summary.active_stock_alerts > 0;
  const status = hasCritical
    ? { label: "Atención crítica", tone: "danger" as StatusTone }
    : hasReview
      ? { label: "Revisar antes de operar", tone: "warning" as StatusTone }
      : { label: "Listo para operar", tone: "ok" as StatusTone };

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
            Revisión operativa
          </p>
          <h2 className="mt-1 text-xl font-black uppercase">{status.label}</h2>
        </div>
        <StatusBadge label={status.label} tone={status.tone} />
      </div>
      <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
        Cuentas, impresiones y alertas.
      </p>
    </section>
  );
}

export function SystemDashboardPage() {
  return (
    <div className="grid gap-4">
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-4 py-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
          Administración
        </p>
        <h1 className="mt-1 text-3xl font-black uppercase leading-none md:text-4xl">
          Sistema
        </h1>
        <p className="mt-2 max-w-5xl text-sm font-bold leading-5 text-[var(--kp-muted)] md:text-base">
          Revisa conexión, datos y mantenimiento local.
        </p>
      </section>

      <section className="grid gap-3 xl:grid-cols-3" aria-label="Estado de sistema">
        <HealthStatusCard />
        <DataStatusCard />
        <ReviewStatusCard />
      </section>

      <AirtableSyncStatusCard />
      <DiagnosticsPanel />
    </div>
  );
}

import { AlertTriangle, CheckCircle2, Database, RefreshCw, ShieldAlert } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { useDatabaseStatusQuery } from "../hooks/useDatabaseStatusQuery";
import { usePreflightQuery } from "../hooks/usePreflightQuery";
import { useSeedSummaryQuery } from "../hooks/useSeedSummaryQuery";
import type { PreflightCheck, PreflightSummary } from "../types/systemTypes";

type StatusTone = "ok" | "warning" | "danger" | "neutral" | "info";
type FindingSeverity = "review" | "critical";

type Finding = {
  id: string;
  message: string;
  recommendation: string;
  severity: FindingSeverity;
};

const criticalCheckKeys = new Set([
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

function supportErrorMessage(error: unknown) {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
    return "No tienes permiso para ver esta revisión.";
  }
  return "No se pudo revisar el diagnóstico.";
}

function numberFromText(text: string) {
  return text.match(/\d+/)?.[0] ?? null;
}

function safeFallbackMessage(check: PreflightCheck) {
  const source = check.message || check.key;
  const withoutJson = source.replace(/[{}[\]"]/g, "");
  const normalized = withoutJson.replace(/_/g, " ").replace(/\s+/g, " ").trim();
  if (!normalized) return "Hay un hallazgo por revisar.";
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function translateFinding(check: PreflightCheck): Pick<Finding, "message" | "recommendation"> {
  const message = check.message.toLowerCase();
  const amount = numberFromText(check.message);

  if (check.key === "seed_admin" || message.includes("active admin employee")) {
    return {
      message: "Debe existir exactamente un administrador activo.",
      recommendation: "Revisa empleados administradores.",
    };
  }

  if (check.key === "active_stock_alerts" || message.includes("stock alert(s) are active")) {
    return {
      message: amount
        ? `Hay ${amount} alertas de stock activas.`
        : "Hay alertas de stock activas.",
      recommendation: "Revisa Inventario.",
    };
  }

  if (
    check.key === "failed_print_jobs" ||
    message.includes("print job(s) failed") ||
    message.includes("print job(s) require retry or review")
  ) {
    return {
      message: amount ? `Hay ${amount} impresiones fallidas.` : "Hay impresiones fallidas.",
      recommendation: "Revisa Impresión.",
    };
  }

  if (message.includes("print job(s) are pending")) {
    return {
      message: amount ? `Hay ${amount} impresiones pendientes.` : "Hay impresiones pendientes.",
      recommendation: "Revisa Impresión.",
    };
  }

  if (message.includes("open ticket(s)")) {
    return {
      message: amount ? `Hay ${amount} cuentas abiertas.` : "Hay cuentas abiertas.",
      recommendation: "Revisa Mesas o Caja.",
    };
  }

  if (message.includes("ticket(s) in checkout")) {
    return {
      message: amount ? `Hay ${amount} cuentas en cobro.` : "Hay cuentas en cobro.",
      recommendation: "Revisa Mesas o Caja.",
    };
  }

  if (check.key === "single_open_cash_shift") {
    return {
      message: "Hay más de una caja abierta.",
      recommendation: "Revisa Caja.",
    };
  }

  if (check.key === "single_active_ticket_per_table") {
    return {
      message: "Hay más de una cuenta activa en una mesa.",
      recommendation: "Revisa Mesas o Caja.",
    };
  }

  if (check.key === "print_job_printer_snapshot") {
    return {
      message: "Hay impresiones con datos incompletos.",
      recommendation: "Revisa Impresión.",
    };
  }

  return {
    message: safeFallbackMessage(check),
    recommendation: "Revisa el detalle con el encargado.",
  };
}

function findingSeverity(check: PreflightCheck): FindingSeverity {
  if (check.status === "ERROR" && criticalCheckKeys.has(check.key)) return "critical";
  if (check.status === "ERROR" && check.key === "failed_print_jobs") return "critical";
  return "review";
}

function buildFindings(checks: PreflightCheck[], summary: PreflightSummary): Finding[] {
  const findingsById = new Map<string, Finding>();

  const addFinding = (finding: Finding) => {
    if (!findingsById.has(finding.id)) {
      findingsById.set(finding.id, finding);
    }
  };

  checks
    .filter((check) => check.status !== "OK")
    .forEach((check) => {
      addFinding({
        id: check.key,
        ...translateFinding(check),
        severity: findingSeverity(check),
      });
    });

  if (summary.open_tickets > 0) {
    addFinding({
      id: "summary_open_tickets",
      message: `Hay ${summary.open_tickets} cuentas abiertas.`,
      recommendation: "Revisa Mesas o Caja.",
      severity: "review",
    });
  }

  if (summary.in_payment_tickets > 0) {
    addFinding({
      id: "summary_in_payment_tickets",
      message: `Hay ${summary.in_payment_tickets} cuentas en cobro.`,
      recommendation: "Revisa Mesas o Caja.",
      severity: "review",
    });
  }

  if (summary.pending_print_jobs > 0) {
    addFinding({
      id: "summary_pending_print_jobs",
      message: `Hay ${summary.pending_print_jobs} impresiones pendientes.`,
      recommendation: "Revisa Impresión.",
      severity: "review",
    });
  }

  return Array.from(findingsById.values());
}

export function systemReviewStatus(findings: Finding[]) {
  if (findings.some((finding) => finding.severity === "critical")) {
    return { label: "Atención crítica", tone: "danger" as StatusTone };
  }
  if (findings.length > 0) {
    return { label: "Revisar antes de operar", tone: "warning" as StatusTone };
  }
  return { label: "Listo para operar", tone: "ok" as StatusTone };
}

function hasBaseData(summary: {
  tables: number;
  categories: number;
  stations: number;
  payment_methods: number;
}) {
  return (
    summary.tables > 0 &&
    summary.categories > 0 &&
    summary.stations > 0 &&
    summary.payment_methods > 0
  );
}

function Counter({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1">
      <dt className="text-[10px] font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
        {label}
      </dt>
      <dd className="text-lg font-black">{value}</dd>
    </div>
  );
}

export function DiagnosticsPanel() {
  const databaseQuery = useDatabaseStatusQuery();
  const seedSummaryQuery = useSeedSummaryQuery();
  const preflightQuery = usePreflightQuery();

  const baseReady = databaseQuery.data?.status?.toLowerCase() === "ok";
  const baseDataReady = seedSummaryQuery.data ? hasBaseData(seedSummaryQuery.data) : false;
  const findings = preflightQuery.data
    ? buildFindings(preflightQuery.data.checks, preflightQuery.data.summary)
    : [];
  const reviewStatus = systemReviewStatus(findings);
  const isRefreshing =
    databaseQuery.isFetching || seedSummaryQuery.isFetching || preflightQuery.isFetching;

  const refreshReview = () => {
    void databaseQuery.refetch();
    void seedSummaryQuery.refetch();
    void preflightQuery.refetch();
  };

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <header className="mb-3 flex flex-col gap-3 border-b-4 border-[var(--kp-ink)] pb-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-warning)]">
            Diagnóstico
          </p>
          <h2 className="mt-1 text-2xl font-black uppercase leading-none">Datos locales</h2>
        </div>
        <BrutalButton type="button" size="sm" onClick={refreshReview} disabled={isRefreshing}>
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Actualizar revisión
        </BrutalButton>
      </header>

      <div className="grid gap-3 lg:grid-cols-3">
        <article className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-selected)]">
                Base local
              </p>
              <h3 className="mt-1 text-lg font-black uppercase">Conexión</h3>
            </div>
            <Database className="h-5 w-5 shrink-0 text-[var(--kp-warning)]" aria-hidden="true" />
          </div>
          <div className="mt-2">
            {databaseQuery.isPending ? (
              <LoadingState />
            ) : databaseQuery.isError ? (
              <ErrorState message={supportErrorMessage(databaseQuery.error)} />
            ) : (
              <StatusBadge
                label={baseReady ? "Conectado" : "Atención crítica"}
                tone={baseReady ? "ok" : "danger"}
              />
            )}
          </div>
        </article>

        <article className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-selected)]">
                Catálogos
              </p>
              <h3 className="mt-1 text-lg font-black uppercase">
                {baseDataReady ? "Datos base cargados" : "Faltan datos base"}
              </h3>
            </div>
            <CheckCircle2 className="h-5 w-5 shrink-0 text-[var(--kp-success)]" aria-hidden="true" />
          </div>
          {seedSummaryQuery.isPending ? (
            <div className="mt-2">
              <LoadingState />
            </div>
          ) : seedSummaryQuery.isError ? (
            <div className="mt-2">
              <ErrorState message={supportErrorMessage(seedSummaryQuery.error)} />
            </div>
          ) : (
            <dl className="mt-2 grid grid-cols-4 gap-1">
              <Counter label="Mesas" value={seedSummaryQuery.data.tables} />
              <Counter label="Categorías" value={seedSummaryQuery.data.categories} />
              <Counter label="Estaciones" value={seedSummaryQuery.data.stations} />
              <Counter label="Pagos" value={seedSummaryQuery.data.payment_methods} />
            </dl>
          )}
        </article>

        <article className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-selected)]">
                Revisión operativa
              </p>
              <h3 className="mt-1 text-lg font-black uppercase">{reviewStatus.label}</h3>
            </div>
            <ShieldAlert className="h-5 w-5 shrink-0 text-[var(--kp-info)]" aria-hidden="true" />
          </div>
          {preflightQuery.isPending ? (
            <div className="mt-2">
              <LoadingState />
            </div>
          ) : preflightQuery.isError ? (
            <div className="mt-2">
              <ErrorState message={supportErrorMessage(preflightQuery.error)} />
            </div>
          ) : (
            <dl className="mt-2 grid grid-cols-4 gap-1">
              <Counter label="Cuentas" value={preflightQuery.data.summary.open_tickets} />
              <Counter label="Cobro" value={preflightQuery.data.summary.in_payment_tickets} />
              <Counter label="Impr." value={preflightQuery.data.summary.pending_print_jobs} />
              <Counter label="Stock" value={preflightQuery.data.summary.active_stock_alerts} />
            </dl>
          )}
        </article>
      </div>

      <div className="mt-3">
        <div className="mb-2 flex items-center justify-between gap-3">
          <h3 className="text-sm font-black uppercase tracking-[0.14em]">Hallazgos</h3>
          <StatusBadge label={reviewStatus.label} tone={reviewStatus.tone} />
        </div>
        {preflightQuery.isPending ? (
          <LoadingState />
        ) : preflightQuery.isError ? (
          <ErrorState message={supportErrorMessage(preflightQuery.error)} />
        ) : findings.length > 0 ? (
          <ul className="grid max-h-64 gap-2 overflow-y-auto pr-1">
            {findings.map((finding) => (
              <li
                key={finding.id}
                className={[
                  "grid gap-2 border-2 border-[var(--kp-ink)] p-2 text-sm font-bold md:grid-cols-[auto_1fr_auto] md:items-center",
                  finding.severity === "critical"
                    ? "bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]"
                    : "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
                ].join(" ")}
              >
                <span className="inline-flex items-center gap-1 text-xs font-black uppercase tracking-[0.08em]">
                  <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {finding.severity === "critical" ? "Crítica" : "Revisar"}
                </span>
                <span>{finding.message}</span>
                <span className="font-black">{finding.recommendation}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-success)] p-2 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-success-contrast)]">
            No hay hallazgos pendientes.
          </p>
        )}
      </div>
    </section>
  );
}

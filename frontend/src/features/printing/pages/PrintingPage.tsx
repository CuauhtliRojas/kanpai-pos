import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasPermission } from "../../auth/lib/permissions";
import { PrintJobList } from "../components/PrintJobList";
import { usePrintJobsQuery } from "../hooks/usePrintJobsQuery";
import { useReprintMutation } from "../hooks/useReprintMutation";
import { useRetryPrintJobMutation } from "../hooks/useRetryPrintJobMutation";
import type { PrintJobStatus } from "../types/printingTypes";

function getReprintErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 403) return "Pide ayuda al encargado.";
  return "No se pudo preparar el reintento. Pide ayuda al encargado.";
}

const SUMMARY_ORDER: PrintJobStatus[] = ["Fallido", "Pendiente", "Tomado", "Impreso", "Cancelado"];

const SUMMARY_CONFIG: Record<PrintJobStatus, { label: string; className: string }> = {
  Pendiente: {
    label: "Pendiente",
    className: "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  },
  Tomado: {
    label: "En proceso",
    className: "bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
  },
  Impreso: {
    label: "Impreso",
    className: "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
  },
  Fallido: {
    label: "Fallo",
    className: "bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
  },
  Cancelado: {
    label: "Cancelado",
    className: "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
  },
};

export function PrintingPage() {
  const { employee, permissions } = useAuthSession();
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const jobsQuery = usePrintJobsQuery();
  const retryMutation = useRetryPrintJobMutation();
  const reprintMutation = useReprintMutation();

  const jobs = jobsQuery.data ?? [];

  const statusCounts = jobs.reduce<Partial<Record<PrintJobStatus, number>>>((acc, job) => {
    acc[job.status] = (acc[job.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Operacion</p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Impresion</h1>
          <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
            Revisa tickets y comandas que siguen en cola.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <BrutalButton
            type="button"
            onClick={() => void jobsQuery.refetch()}
            disabled={jobsQuery.isFetching}
          >
            <RefreshCw className="h-5 w-5" /> Actualizar
          </BrutalButton>
          <BrutalButton
            type="button"
            onClick={() => {
              setRetryMessage(null);
              void retryMutation
                .mutateAsync()
                .then((result) =>
                  setRetryMessage(
                    result.jobs_requeued > 0
                      ? `Se enviaron nuevamente ${result.jobs_requeued} ${result.jobs_requeued === 1 ? "impresion fallida" : "impresiones fallidas"}.`
                      : "No habia impresiones fallidas para volver a intentar.",
                  ),
                )
                .catch(() => undefined);
            }}
            disabled={retryMutation.isPending}
          >
            Reintentar fallidas
          </BrutalButton>
        </div>
      </header>

      {retryMessage ? (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-info)] p-3 font-black text-[var(--kp-info-contrast)] shadow-[var(--kp-shadow-hard-sm)]">
          {retryMessage}
        </p>
      ) : null}
      {retryMutation.isError ? (
        <p
          role="alert"
          className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)] shadow-[var(--kp-shadow-hard-sm)]"
        >
          No se pudo preparar el reintento. Pide ayuda al encargado.
        </p>
      ) : null}

      {!jobsQuery.isPending && !jobsQuery.isError && jobs.length > 0 ? (
        <div className="flex flex-wrap items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
          <span className="text-sm font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            {jobs.length === 1 ? "1 trabajo" : `${jobs.length} trabajos`}
          </span>
          {SUMMARY_ORDER.filter((s) => statusCounts[s]).map((s) => (
            <span
              key={s}
              className={`border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase tracking-[0.08em] ${SUMMARY_CONFIG[s].className}`}
            >
              {SUMMARY_CONFIG[s].label}: {statusCounts[s]}
            </span>
          ))}
        </div>
      ) : null}

      {jobsQuery.isPending ? (
        <LoadingState />
      ) : jobsQuery.isError ? (
        <ErrorState title="No se pudo cargar la cola de impresion" message="Pide ayuda al encargado." />
      ) : (
        <PrintJobList
          jobs={jobs}
          canReprint={hasPermission(permissions, "REPRINT")}
          activeJobId={activeJobId}
          isReprinting={reprintMutation.isPending}
          reprintError={getReprintErrorMessage(reprintMutation.error)}
          onReprint={async (jobId, reason) => {
            if (!employee) return;
            setActiveJobId(jobId);
            await reprintMutation.mutateAsync({ jobId, employeeId: employee.id, reason });
          }}
        />
      )}
    </div>
  );
}

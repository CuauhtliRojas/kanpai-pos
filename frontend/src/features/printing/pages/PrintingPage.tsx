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

function getPrintingErrorMessage(error: unknown, action: "retry" | "reprint"): string | null {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 403) return "Pide ayuda al encargado.";
  return action === "retry" ? "No se pudo imprimir." : "No se pudo reimprimir.";
}

export function PrintingPage() {
  const { employee, permissions } = useAuthSession();
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const jobsQuery = usePrintJobsQuery();
  const retryMutation = useRetryPrintJobMutation();
  const reprintMutation = useReprintMutation();

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Operación</p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Impresión</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <BrutalButton
            onClick={() => {
              setRetryMessage(null);
              void retryMutation.mutateAsync()
                .then((result) => setRetryMessage(
                  result.jobs_requeued > 0
                    ? "Trabajos listos para imprimir."
                    : "Sin trabajos para reintentar.",
                ))
                .catch(() => undefined);
            }}
            disabled={retryMutation.isPending}
          >
            Reintentar
          </BrutalButton>
          <BrutalButton onClick={() => void jobsQuery.refetch()} disabled={jobsQuery.isFetching}>
            <RefreshCw className="h-5 w-5" /> Actualizar
          </BrutalButton>
        </div>
      </header>

      {retryMessage ? (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-info)] p-3 font-black text-[var(--kp-info-contrast)] shadow-[var(--kp-shadow-hard-sm)]">{retryMessage}</p>
      ) : null}
      {retryMutation.isError ? (
        <ErrorState title="No se pudo imprimir" message={getPrintingErrorMessage(retryMutation.error, "retry") ?? "Pide ayuda al encargado."} />
      ) : null}
      {jobsQuery.isPending ? (
        <LoadingState />
      ) : jobsQuery.isError ? (
        <ErrorState title="No se pudo cargar Impresión" message="Pide ayuda al encargado." />
      ) : (
        <PrintJobList
          jobs={jobsQuery.data ?? []}
          canReprint={hasPermission(permissions, "REPRINT")}
          activeJobId={activeJobId}
          isReprinting={reprintMutation.isPending}
          errorMessage={getPrintingErrorMessage(reprintMutation.error, "reprint")}
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

import { RefreshCw } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { AuditEventList } from "../components/AuditEventList";
import { useAuditEventsQuery } from "../hooks/useAuditEventsQuery";

export function AuditPage() {
  const eventsQuery = useAuditEventsQuery();
  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div><p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Eventos</p><h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Auditoría</h1></div>
        <BrutalButton onClick={() => void eventsQuery.refetch()} disabled={eventsQuery.isFetching}><RefreshCw className="h-5 w-5" /> Actualizar</BrutalButton>
      </header>
      {eventsQuery.isPending ? <LoadingState /> : eventsQuery.isError ? (
        <ErrorState title="No se pudo cargar Auditoría" message="Intenta de nuevo." />
      ) : <AuditEventList events={eventsQuery.data?.items ?? []} />}
    </div>
  );
}

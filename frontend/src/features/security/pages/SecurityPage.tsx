import { RefreshCw } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useEmployeesQuery } from "../hooks/useEmployeesQuery";
import { EmployeeList } from "../components/EmployeeList";

export function SecurityPage() {
  const employeesQuery = useEmployeesQuery();
  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
            Solo lectura
          </p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Empleados</h1>
        </div>
        <BrutalButton
          onClick={() => void employeesQuery.refetch()}
          disabled={employeesQuery.isFetching}
        >
          <RefreshCw className="h-5 w-5" /> Actualizar
        </BrutalButton>
      </header>

      {employeesQuery.isPending ? (
        <LoadingState />
      ) : employeesQuery.isError ? (
        <ErrorState title="No se pudo cargar Empleados" message="Intenta de nuevo." />
      ) : (
        <EmployeeList employees={employeesQuery.data ?? []} />
      )}
    </div>
  );
}

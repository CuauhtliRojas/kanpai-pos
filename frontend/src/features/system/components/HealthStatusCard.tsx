import { Activity } from "lucide-react";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { SurfaceCard } from "../../../shared/components/SurfaceCard";
import { getErrorMessage } from "../../../shared/lib/errors";
import { useHealthQuery } from "../hooks/useHealthQuery";

export function HealthStatusCard() {
  const healthQuery = useHealthQuery();

  if (healthQuery.isPending) {
    return (
      <SurfaceCard title="Sistema" eyebrow="Estado">
        <LoadingState />
      </SurfaceCard>
    );
  }

  if (healthQuery.isError) {
    return (
      <SurfaceCard title="Sistema" eyebrow="Estado">
        <ErrorState
          title="Sin conexion"
          message={getErrorMessage(healthQuery.error)}
        />
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard
      title="Sistema"
      eyebrow="Estado"
      action={<StatusBadge label="Conectado" tone="ok" />}
    >
      <div className="grid gap-3 text-sm font-bold text-[var(--kp-text)]">
        <div className="flex items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
          <Activity className="h-6 w-6 text-[var(--kp-selected)]" />
          <span className="font-black uppercase">Listo para operar</span>
        </div>
        <p>Modo: local</p>
        <p>Datos: disponibles en esta computadora</p>
      </div>
    </SurfaceCard>
  );
}

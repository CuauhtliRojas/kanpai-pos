import { Activity } from "lucide-react";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { SurfaceCard } from "../../../shared/components/SurfaceCard";
import { useHealthQuery } from "../hooks/useHealthQuery";

export function HealthStatusCard() {
  const healthQuery = useHealthQuery();

  if (healthQuery.isPending) {
    return (
      <SurfaceCard title="Datos locales" eyebrow="Sistema">
        <LoadingState />
      </SurfaceCard>
    );
  }

  if (healthQuery.isError) {
    return (
      <SurfaceCard title="Datos locales" eyebrow="Sistema">
        <ErrorState
          title="Sin conexión"
          message="Revisa el sistema o pide ayuda."
        />
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard
      title="Datos locales"
      eyebrow="Sistema"
      action={<StatusBadge label="Conectado" tone="ok" />}
    >
      <div className="grid gap-3 text-sm font-bold text-[var(--kp-text)]">
        <div className="flex items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
          <Activity className="h-6 w-6 text-[var(--kp-selected)]" />
          <span className="font-black uppercase">Listo para operar</span>
        </div>
        <p>La información está disponible en esta computadora.</p>
        <p className="text-xs text-[var(--kp-muted)]">
          Si ves “Sin conexión”, revisa el sistema o pide ayuda.
        </p>
      </div>
    </SurfaceCard>
  );
}

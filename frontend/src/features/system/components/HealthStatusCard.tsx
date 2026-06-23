import { LoadingState } from "../../../shared/components/LoadingState";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { useHealthQuery } from "../hooks/useHealthQuery";

export function HealthStatusCard() {
  const healthQuery = useHealthQuery();

  if (healthQuery.isPending) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
          Conexión local
        </p>
        <div className="mt-3">
          <LoadingState />
        </div>
      </section>
    );
  }

  if (healthQuery.isError) {
    return (
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
              Conexión local
            </p>
            <h2 className="mt-1 text-xl font-black uppercase">Sin conexión</h2>
          </div>
          <StatusBadge label="Sin conexión" tone="danger" />
        </div>
        <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
          No se pudo conectar con el sistema local.
        </p>
      </section>
    );
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
            Conexión local
          </p>
          <h2 className="mt-1 text-xl font-black uppercase">Conectado</h2>
        </div>
        <StatusBadge label="Conectado" tone="ok" />
      </div>
      <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
        El sistema local responde correctamente.
      </p>
    </section>
  );
}

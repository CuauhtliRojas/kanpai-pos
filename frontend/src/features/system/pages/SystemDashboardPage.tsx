import { AirtableSyncStatusCard } from "../components/AirtableSyncStatusCard";
import { HealthStatusCard } from "../components/HealthStatusCard";

export function SystemDashboardPage() {
  return (
    <div className="grid gap-4">
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
          Inicio
        </p>
        <h1 className="mt-2 text-4xl font-black uppercase leading-none md:text-6xl">
          Kanpai POS
        </h1>
        <p className="mt-3 max-w-5xl text-base font-bold leading-7 text-[var(--kp-muted)] md:text-lg">
          Sistema de venta listo para operar en barra: inicia sesion, abre caja,
          elige mesa, agrega productos, envia comanda y cobra.
        </p>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <HealthStatusCard />
        <AirtableSyncStatusCard />
      </section>

      <section className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)] md:grid-cols-3">
        <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-selected)] p-4 text-[var(--kp-selected-contrast)] shadow-[var(--kp-shadow-hard-sm)]">
          <p className="text-xs font-black uppercase tracking-[0.16em]">Primero</p>
          <p className="mt-2 text-2xl font-black uppercase">Iniciar sesion</p>
        </div>
        <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)]">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">
            Luego
          </p>
          <p className="mt-2 text-2xl font-black uppercase">Abrir caja</p>
        </div>
        <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)]">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">
            Despues
          </p>
          <p className="mt-2 text-2xl font-black uppercase">Vender</p>
        </div>
      </section>
    </div>
  );
}

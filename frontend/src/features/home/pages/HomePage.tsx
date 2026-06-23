import { OperationalStatusPanel } from "../components/OperationalStatusPanel";
import { QuickAccessPanel } from "../components/QuickAccessPanel";
import { QuickStartPanel } from "../components/QuickStartPanel";

export function HomePage() {
  return (
    <div className="grid gap-4">
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-4 py-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
          Sistema
        </p>
        <h1 className="mt-1 text-3xl font-black uppercase leading-none md:text-4xl">
          Inicio operativo
        </h1>
        <p className="mt-2 max-w-5xl text-sm font-bold leading-5 text-[var(--kp-muted)] md:text-base">
          Revisa el turno y empieza a vender.
        </p>
      </section>

      <QuickStartPanel />
      <QuickAccessPanel />
      <OperationalStatusPanel />
    </div>
  );
}

import { CircleDollarSign } from "lucide-react";
import { Link } from "react-router";

export function PosBlockedByCashPanel() {
  return (
    <section className="grid justify-items-start gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] p-6 text-[var(--kp-warning-text)] shadow-[var(--kp-shadow-hard)]">
      <CircleDollarSign className="h-12 w-12" />
      <div>
        <h2 className="text-3xl font-black uppercase">Primero abre caja.</h2>
        <p className="mt-2 font-bold">Las mesas estarán disponibles cuando la caja esté abierta.</p>
      </div>
      <Link
        to="/cash"
        className="inline-flex min-h-[var(--kp-touch-lg)] items-center border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-6 text-lg font-black uppercase tracking-[0.08em] text-[var(--kp-warning-contrast)] shadow-[var(--kp-shadow-hard)] transition active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
      >
        Ir a caja
      </Link>
    </section>
  );
}

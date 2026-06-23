import { ArrowRight } from "lucide-react";
import { Link } from "react-router";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasAnyPermission } from "../../auth/lib/permissions";

const cashPermissions = ["CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE"] as const;

const stepCardClassName =
  "flex flex-col border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)]";

const stepLinkClassName =
  "mt-3 inline-flex min-h-[var(--kp-touch-md)] items-center justify-between gap-3 border-2 border-[var(--kp-warning)] bg-[var(--kp-bg)] px-3 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-text-on-dark)] shadow-[var(--kp-shadow-hard-sm)] transition hover:-translate-y-0.5 hover:shadow-[var(--kp-shadow-hard)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[var(--kp-info)]";

function StepBadge({ children }: { children: string }) {
  return (
    <span className="inline-flex w-fit border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-2 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--kp-warning-contrast)]">
      {children}
    </span>
  );
}

export function QuickStartPanel() {
  const { permissions } = useAuthSession();
  const canAccessCash = hasAnyPermission(permissions, cashPermissions);

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <h2 className="text-sm font-black uppercase tracking-[0.16em]">Arranque rápido</h2>
      <div className="mt-2 grid gap-3 md:grid-cols-3">
        <article className={stepCardClassName}>
          <StepBadge>Paso 1</StepBadge>
          <h3 className="mt-2 text-lg font-black uppercase">Abrir caja</h3>
          <p className="mt-1 flex-1 text-xs font-bold leading-4 text-[var(--kp-muted)]">
            Prepara el turno para registrar ventas y gastos.
          </p>
          {canAccessCash ? (
            <Link to="/cash" className={stepLinkClassName}>
              <span>Ir a caja</span>
              <ArrowRight className="h-4 w-4 shrink-0" aria-hidden="true" />
            </Link>
          ) : (
            <div className="mt-3 flex min-h-[var(--kp-touch-md)] items-center border-2 border-dashed border-[var(--kp-ink)] bg-[var(--kp-surface-soft)] px-3 text-xs font-black uppercase tracking-[0.06em] text-[var(--kp-muted)]">
              Sin permiso para caja
            </div>
          )}
        </article>

        <article className={stepCardClassName}>
          <StepBadge>Paso 2</StepBadge>
          <h3 className="mt-2 text-lg font-black uppercase">Elegir mesa</h3>
          <p className="mt-1 flex-1 text-xs font-bold leading-4 text-[var(--kp-muted)]">
            Selecciona dónde se tomará el pedido.
          </p>
          <Link to="/pos" className={stepLinkClassName}>
            <span>Ir a mesas</span>
            <ArrowRight className="h-4 w-4 shrink-0" aria-hidden="true" />
          </Link>
        </article>

        <article className={stepCardClassName}>
          <StepBadge>Paso 3</StepBadge>
          <h3 className="mt-2 text-lg font-black uppercase">Enviar y cobrar</h3>
          <p className="mt-1 flex-1 text-xs font-bold leading-4 text-[var(--kp-muted)]">
            Manda la comanda y registra el pago.
          </p>
          <Link to="/pos" className={stepLinkClassName}>
            <span>Ir a venta</span>
            <ArrowRight className="h-4 w-4 shrink-0" aria-hidden="true" />
          </Link>
        </article>
      </div>
    </section>
  );
}

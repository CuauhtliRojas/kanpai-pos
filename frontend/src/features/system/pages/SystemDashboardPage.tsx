import { ArrowRight } from "lucide-react";
import { Link } from "react-router";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasAnyPermission } from "../../auth/lib/permissions";
import { AirtableSyncStatusCard } from "../components/AirtableSyncStatusCard";
import { HealthStatusCard } from "../components/HealthStatusCard";

const cashPermissions = ["CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE"] as const;

const quickAccessItems = [
  { label: "Caja", description: "Turno y gastos", to: "/cash", requiresCashAccess: true },
  { label: "Mesas", description: "Pedidos activos", to: "/pos", requiresCashAccess: false },
  {
    label: "Producción",
    description: "Comandas",
    to: "/production",
    requiresCashAccess: false,
  },
  {
    label: "Impresión",
    description: "Tickets pendientes",
    to: "/printing",
    requiresCashAccess: false,
  },
  {
    label: "Inventario",
    description: "Stock y alertas",
    to: "/inventory",
    requiresCashAccess: false,
  },
] as const;

const stepCardClassName =
  "flex flex-col border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)]";

const stepLinkClassName =
  "mt-3 inline-flex min-h-[var(--kp-touch-md)] items-center justify-between gap-3 border-2 border-[var(--kp-warning)] bg-[var(--kp-bg)] px-3 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-text-on-dark)] shadow-[var(--kp-shadow-hard-sm)] transition hover:-translate-y-0.5 hover:shadow-[var(--kp-shadow-hard)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[var(--kp-info)]";

const quickLinkClassName =
  "group flex min-h-[var(--kp-touch-md)] min-w-0 items-center justify-between gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-3 py-2 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition hover:-translate-y-0.5 hover:bg-[var(--kp-surface-raised)] hover:shadow-[var(--kp-shadow-hard)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[var(--kp-info)]";

function StepBadge({ children }: { children: string }) {
  return (
    <span className="inline-flex w-fit border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-2 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--kp-warning-contrast)]">
      {children}
    </span>
  );
}

export function SystemDashboardPage() {
  const { permissions } = useAuthSession();
  const canAccessCash = hasAnyPermission(permissions, cashPermissions);

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

      <section aria-labelledby="quick-access-title">
        <h2
          id="quick-access-title"
          className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-text-on-dark)]"
        >
          Accesos rápidos
        </h2>
        <nav className="grid grid-cols-2 gap-2 md:grid-cols-5" aria-label="Accesos rápidos">
          {quickAccessItems.map((item) => {
            const content = (
              <>
                <span className="min-w-0">
                  <span className="block truncate text-xs font-black uppercase tracking-[0.06em]">
                    {item.label}
                  </span>
                  <span className="block truncate text-[10px] font-bold text-[var(--kp-muted)]">
                    {item.description}
                  </span>
                </span>
                <ArrowRight
                  className="h-4 w-4 shrink-0 text-[var(--kp-selected)] transition-transform group-hover:translate-x-1"
                  aria-hidden="true"
                />
              </>
            );

            if (item.requiresCashAccess && !canAccessCash) {
              return (
                <div
                  key={item.label}
                  className="flex min-h-[var(--kp-touch-md)] min-w-0 items-center justify-between gap-2 border-2 border-dashed border-[var(--kp-ink)] bg-[var(--kp-surface-soft)] px-3 py-2 text-[var(--kp-muted)]"
                  aria-label="Caja: sin permiso"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-xs font-black uppercase tracking-[0.06em]">
                      {item.label}
                    </span>
                    <span className="block truncate text-[10px] font-bold">{item.description}</span>
                  </span>
                  <span className="shrink-0 text-[9px] font-black uppercase">Sin permiso</span>
                </div>
              );
            }

            return (
              <Link key={item.label} to={item.to} className={quickLinkClassName}>
                {content}
              </Link>
            );
          })}
        </nav>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <HealthStatusCard />
        <AirtableSyncStatusCard />
      </section>
    </div>
  );
}

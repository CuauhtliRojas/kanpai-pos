import { ArrowRight } from "lucide-react";
import { Link } from "react-router";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasAnyPermission } from "../../auth/lib/permissions";

const cashPermissions = ["CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE"] as const;

const quickAccessItems = [
  { label: "Caja", description: "Turno y gastos", to: "/cash", requiresCashAccess: true },
  { label: "Mesas / Venta", description: "Pedidos activos", to: "/pos", requiresCashAccess: false },
  { label: "Producción", description: "Comandas", to: "/production", requiresCashAccess: false },
  { label: "Impresión", description: "Tickets pendientes", to: "/printing", requiresCashAccess: false },
  { label: "Inventario", description: "Stock y alertas", to: "/inventory", requiresCashAccess: false },
] as const;

const quickLinkClassName =
  "group flex min-h-[var(--kp-touch-md)] min-w-0 items-center justify-between gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-3 py-2 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition hover:-translate-y-0.5 hover:bg-[var(--kp-surface-raised)] hover:shadow-[var(--kp-shadow-hard)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[var(--kp-info)]";

export function QuickAccessPanel() {
  const { permissions } = useAuthSession();
  const canAccessCash = hasAnyPermission(permissions, cashPermissions);

  return (
    <section aria-labelledby="quick-access-title">
      <h2
        id="quick-access-title"
        className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-text-on-dark)]"
      >
        Accesos rápidos
      </h2>
      <nav className="grid grid-cols-2 gap-2 md:grid-cols-5" aria-label="Accesos rápidos">
        {quickAccessItems.map((item) => {
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
            </Link>
          );
        })}
      </nav>
    </section>
  );
}

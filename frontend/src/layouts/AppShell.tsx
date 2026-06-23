import { useMemo, useState } from "react";
import { LogOut, Menu, X } from "lucide-react";
import { NavLink, Outlet } from "react-router";
import { useAirtableSyncStatusQuery } from "../features/system/hooks/useAirtableSyncStatusQuery";
import { BrandMark } from "../shared/components/BrandMark";
import { SessionSummary } from "../features/auth/components/SessionSummary";
import { useAuthSession } from "../features/auth/hooks/useAuthSession";
import { CurrentTableSummary } from "../features/operations/components/CurrentTableSummary";
import {
  navigationItems,
  resolveNavigationItemAccess,
  type NavigationItem,
  type NavigationItemAccess,
} from "./navigationItems";

type MenuItemProps = {
  item: NavigationItem;
  access: Exclude<NavigationItemAccess, "denied">;
  onNavigate: () => void;
};

function MenuItem({ item, access, onNavigate }: MenuItemProps) {
  return (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      onClick={onNavigate}
      className={({ isActive }) =>
        [
          "flex min-h-[var(--kp-touch-md)] items-center gap-3 border-2 border-[var(--kp-ink)] px-3 shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
          isActive
            ? "bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)]"
            : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
        ].join(" ")
      }
    >
      <item.icon className="h-5 w-5 shrink-0" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center justify-between gap-2">
          <span className="text-xs font-black uppercase tracking-[0.08em]">{item.label}</span>
          {access === "coming_soon" ? (
            <span className="shrink-0 text-[9px] font-black uppercase">No disponible</span>
          ) : null}
        </span>
        <span className="block truncate text-[11px] font-bold normal-case leading-tight tracking-normal opacity-70">
          {item.description}
        </span>
      </span>
    </NavLink>
  );
}

function resolveEstadoSignal(
  status: string | undefined,
  running: boolean | undefined,
  isError: boolean,
): { value: string; className: string } {
  if (isError) {
    return {
      value: "Sin conexión",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  if (running) {
    return {
      value: "Actualizando",
      className: "border-[var(--kp-ink)] bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
    };
  }

  if (!status || status === "not_started" || status.includes("disabled") || status.includes("no_directions")) {
    return {
      value: "Pendiente",
      className: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
    };
  }

  if (status.includes("error") || status.includes("missing")) {
    return {
      value: "Revisar",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  if (status.includes("success")) {
    return {
      value: "Al día",
      className: "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
    };
  }

  return {
    value: "Pendiente",
    className: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  };
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { logout, permissions, roles } = useAuthSession();
  const syncQuery = useAirtableSyncStatusQuery();
  const visibleNavigationGroups = useMemo(
    () =>
      (["Operación", "Servicio", "Administración"] as const)
        .map((group) => ({
          group,
          items: navigationItems
            .filter((item) => item.group === group)
            .map((item) => ({
              item,
              access: resolveNavigationItemAccess(item, roles, permissions),
            }))
            .filter(
              (
                entry,
              ): entry is {
                item: NavigationItem;
                access: Exclude<NavigationItemAccess, "denied">;
              } => entry.access !== "denied",
            ),
        }))
        .filter((entry) => entry.items.length > 0),
    [permissions, roles],
  );

  const statusSignal = resolveEstadoSignal(
    syncQuery.data?.last_status,
    syncQuery.data?.running,
    syncQuery.isError,
  );

  return (
    <div className="min-h-screen bg-[var(--kp-bg)] text-[var(--kp-text)]">
      <header className="sticky top-0 z-30 h-[var(--kp-topbar-height)] border-b-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] text-[var(--kp-text-on-dark)]">
        <div className="grid h-full grid-cols-[auto_1fr_auto] items-center gap-3 px-3">
          <button
            type="button"
            aria-label="Abrir menú"
            onClick={() => setMenuOpen(true)}
            className="flex h-10 w-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-ink)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex min-w-0 items-center gap-2 overflow-hidden">
            <div className="flex h-9 shrink-0 items-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-1 sm:px-2">
              <BrandMark variant="icon" className="h-6 w-6 sm:hidden" />
              <BrandMark variant="logo" className="hidden h-6 w-auto sm:block" />
            </div>
            <SessionSummary />
            <CurrentTableSummary />
          </div>

          <div
            title="Estado de los datos"
            aria-label={`Datos: ${statusSignal.value}`}
            className={`flex min-h-10 min-w-20 flex-col items-center justify-center border-2 px-2 text-center font-black uppercase leading-none sm:min-w-24 ${statusSignal.className}`}
          >
            <span className="text-[8px] tracking-[0.14em] opacity-75">Datos</span>
            <span className="mt-1 text-[10px] tracking-[0.06em] sm:text-xs">{statusSignal.value}</span>
          </div>
        </div>
      </header>

      {menuOpen ? (
        <div
          className="fixed inset-0 z-40 bg-[rgba(0,0,0,0.62)]"
          onClick={() => setMenuOpen(false)}
        >
          <aside
            className="h-full w-[min(90vw,24rem)] overflow-y-auto border-r-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)] mb-1">
                  Navegación
                </p>
                {/* Aquí está la magia: un contenedor flex con gap para separar las imágenes */}
                <div className="flex items-center gap-2">
                  <BrandMark variant="icon" className="h-10 w-auto" />
                  <BrandMark variant="logo" className="h-10 w-auto max-w-full" />
                </div>
              </div>
              <button
                type="button"
                aria-label="Cerrar menú"
                onClick={() => setMenuOpen(false)}
                className="flex h-12 w-12 items-center justify-center border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <nav className="grid gap-4" aria-label="Navegación principal">
              {visibleNavigationGroups.map(({ group, items }) => (
                <section key={group} aria-labelledby={`navigation-${group}`}>
                  <h2
                    id={`navigation-${group}`}
                    className="mb-1.5 border-b-2 border-[var(--kp-divider)] pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-[var(--kp-muted)]"
                  >
                    {group}
                  </h2>
                  <div className="grid gap-2">
                    {items.map(({ item, access }) => (
                      <MenuItem
                        key={item.to}
                        item={item}
                        access={access}
                        onNavigate={() => setMenuOpen(false)}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </nav>

            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                void logout().catch(() => undefined);
              }}
              className="mt-4 flex min-h-[var(--kp-touch-md)] w-full items-center gap-3 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
            >
              <LogOut className="h-6 w-6" />
              Cerrar sesión
            </button>
          </aside>
        </div>
      ) : null}

      <main className="min-h-[calc(100vh-var(--kp-topbar-height))] p-3 md:p-4">
        <Outlet />
      </main>

      <footer className="sr-only">
        Navegación administrativa oculta. Área principal reservada para operación POS.
      </footer>
    </div>
  );
}

import { useState } from "react";
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
  access: NavigationItemAccess;
  onNavigate: () => void;
};

function MenuItem({ item, access, onNavigate }: MenuItemProps) {
  if (access === "denied") {
    return (
      <div className="flex min-h-[var(--kp-touch-md)] items-center justify-between gap-3 border-4 border-dashed border-[var(--kp-ink)] bg-[var(--kp-surface-soft)] px-4 text-sm font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
        <span className="flex items-center gap-3">
          <item.icon className="h-6 w-6" />
          {item.label}
        </span>
        <span className="text-[10px]">Sin permiso</span>
      </div>
    );
  }

  return (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      onClick={onNavigate}
      className={({ isActive }) =>
        [
          "flex min-h-[var(--kp-touch-md)] items-center justify-between gap-3 border-4 border-[var(--kp-ink)] px-4 text-sm font-black uppercase tracking-[0.08em] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
          isActive
            ? "bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)]"
            : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
        ].join(" ")
      }
    >
      <span className="flex items-center gap-3">
        <item.icon className="h-6 w-6" />
        {item.label}
      </span>
      {access === "coming_soon" ? <span className="text-[10px]">No disponible</span> : null}
    </NavLink>
  );
}

function resolveEstadoSignal(
  status: string | undefined,
  running: boolean | undefined,
  isError: boolean,
): { label: string; className: string } {
  if (isError) {
    return {
      label: "SIN CONEXIÓN",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  if (running) {
    return {
      label: "ACTUALIZANDO DATOS",
      className: "border-[var(--kp-ink)] bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
    };
  }

  if (!status || status === "not_started" || status.includes("disabled") || status.includes("no_directions")) {
    return {
      label: "ACTUALIZACIÓN PENDIENTE",
      className: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
    };
  }

  if (status.includes("error") || status.includes("missing")) {
    return {
      label: "REVISAR CONEXIÓN",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  if (status.includes("success")) {
    return {
      label: "DATOS AL DÍA",
      className: "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
    };
  }

  return {
    label: "ACTUALIZACIÓN PENDIENTE",
    className: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  };
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { logout, permissions, roles } = useAuthSession();
  const syncQuery = useAirtableSyncStatusQuery();

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
            title="Estado de actualización de datos"
            className={`flex min-h-9 max-w-44 items-center border-4 px-2 text-center text-[9px] font-black uppercase leading-tight tracking-[0.04em] sm:px-3 sm:text-xs sm:tracking-[0.08em] ${statusSignal.className}`}
          >
            {statusSignal.label}
          </div>
        </div>
      </header>

      {menuOpen ? (
        <div className="fixed inset-0 z-40 bg-[rgba(0,0,0,0.72)]">
          <aside className="h-full w-full max-w-md overflow-y-auto border-r-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">
                  Navegación
                </p>
                <BrandMark variant="logo" className="mt-1 h-10 w-auto max-w-full" />
              </div>
              <button
                type="button"
                aria-label="Cerrar menú"
                onClick={() => setMenuOpen(false)}
                className="flex h-12 w-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
              >
                <X className="h-7 w-7" />
              </button>
            </div>

            <nav className="grid gap-3">
              {navigationItems.map((item) => (
                <MenuItem
                  key={item.to}
                  item={item}
                  access={resolveNavigationItemAccess(item, roles, permissions)}
                  onNavigate={() => setMenuOpen(false)}
                />
              ))}
            </nav>

            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                void logout().catch(() => undefined);
              }}
              className="mt-5 flex min-h-[var(--kp-touch-md)] w-full items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-4 text-sm font-black uppercase tracking-[0.08em] text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
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




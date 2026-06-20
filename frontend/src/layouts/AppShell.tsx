import { useState } from "react";
import {
  BarChart3,
  Boxes,
  CircleDollarSign,
  ClipboardList,
  DatabaseZap,
  Home,
  Menu,
  Printer,
  ReceiptText,
  ShieldCheck,
  Utensils,
  X,
} from "lucide-react";
import { NavLink, Outlet } from "react-router";
import { useAirtableSyncStatusQuery } from "../features/system/hooks/useAirtableSyncStatusQuery";
import { BrandMark } from "../shared/components/BrandMark";

const menuItems = [
  { to: "/", label: "Inicio", icon: Home, enabled: true },
  { to: "/system", label: "Estado", icon: DatabaseZap, enabled: true },
  { to: "/cash", label: "Caja", icon: CircleDollarSign, enabled: false },
  { to: "/pos", label: "POS", icon: ReceiptText, enabled: false },
  { to: "/production", label: "Produccion", icon: Utensils, enabled: false },
  { to: "/printing", label: "Impresion", icon: Printer, enabled: false },
  { to: "/inventory", label: "Inventario", icon: Boxes, enabled: false },
  { to: "/reports", label: "Reportes", icon: BarChart3, enabled: false },
  { to: "/audit", label: "Auditoria", icon: ClipboardList, enabled: false },
  { to: "/security", label: "Permisos", icon: ShieldCheck, enabled: false },
];

function resolveEstadoSignal(
  status: string | undefined,
  running: boolean | undefined,
  isError: boolean,
): { label: string; className: string } {
  if (isError) {
    return {
      label: "SIN CONEXION",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  if (running) {
    return {
      label: "ACTUALIZANDO",
      className: "border-[var(--kp-ink)] bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
    };
  }

  if (!status || status === "not_started") {
    return {
      label: "PENDIENTE",
      className: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
    };
  }

  if (status.includes("error") || status.includes("missing")) {
    return {
      label: "SIN CONEXION",
      className: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
    };
  }

  return {
    label: "CONECTADO",
    className: "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
  };
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const EstadoQuery = useAirtableSyncStatusQuery();

  const EstadoSignal = resolveEstadoSignal(
    EstadoQuery.data?.last_status,
    EstadoQuery.data?.running,
    EstadoQuery.isError,
  );

  return (
    <div className="min-h-screen bg-[var(--kp-bg)] text-[var(--kp-text)]">
      <header className="sticky top-0 z-30 h-[var(--kp-topbar-height)] border-b-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] text-[var(--kp-text-on-dark)]">
        <div className="grid h-full grid-cols-[auto_1fr_auto] items-center gap-3 px-3">
          <button
            type="button"
            aria-label="Abrir Menu"
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
            <div className="min-w-0 truncate text-xs font-black uppercase tracking-[0.08em] sm:text-sm">
              CAJERO: SIN SESION
            </div>
            <div className="hidden text-xs font-black uppercase tracking-[0.08em] md:block">
              MESA: SIN MESA
            </div>
          </div>

          <div
            className={`flex min-h-9 items-center border-4 px-3 text-xs font-black uppercase tracking-[0.08em] ${EstadoSignal.className}`}
          >
            {EstadoSignal.label}
          </div>
        </div>
      </header>

      {menuOpen ? (
        <div className="fixed inset-0 z-40 bg-[rgba(0,0,0,0.72)]">
          <aside className="h-full w-full max-w-md border-r-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">
                  Menu
                </p>
                <BrandMark variant="logo" className="mt-1 h-10 w-auto max-w-full" />
              </div>
              <button
                type="button"
                aria-label="Cerrar Menu"
                onClick={() => setMenuOpen(false)}
                className="flex h-12 w-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
              >
                <X className="h-7 w-7" />
              </button>
            </div>

            <nav className="grid gap-3">
              {menuItems.map((item) =>
                item.enabled ? (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    onClick={() => setMenuOpen(false)}
                    className={({ isActive }) =>
                      [
                        "flex min-h-[var(--kp-touch-md)] items-center gap-3 border-4 border-[var(--kp-ink)] px-4 text-sm font-black uppercase tracking-[0.08em] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
                        isActive
                          ? "bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)]"
                          : "bg-[var(--kp-surface-raised)] text-[var(--kp-ink)]",
                      ].join(" ")
                    }
                  >
                    <item.icon className="h-6 w-6" />
                    {item.label}
                  </NavLink>
                ) : (
                  <div
                    key={item.to}
                    className="flex min-h-[var(--kp-touch-md)] items-center justify-between gap-3 border-4 border-dashed border-[var(--kp-ink)] bg-[var(--kp-surface-soft)] px-4 text-sm font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]"
                  >
                    <span className="flex items-center gap-3">
                      <item.icon className="h-6 w-6" />
                      {item.label}
                    </span>
                    <span className="text-[10px]">FUTURO</span>
                  </div>
                ),
              )}
            </nav>
          </aside>
        </div>
      ) : null}

      <main className="min-h-[calc(100vh-var(--kp-topbar-height))] p-3 md:p-4">
        <Outlet />
      </main>

      <footer className="sr-only">
        Navegacion administrativa oculta. Area principal reservada para operacion POS.
      </footer>
    </div>
  );
}




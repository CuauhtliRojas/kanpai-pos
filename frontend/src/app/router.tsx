import { HashRouter, Navigate, Outlet, Route, Routes } from "react-router";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { useAuthSession } from "../features/auth/hooks/useAuthSession";
import { AccessDeniedPanel } from "../features/auth/components/AccessDeniedPanel";
import { PermissionGate } from "../features/auth/components/PermissionGate";
import { CashPage } from "../features/cash/pages/CashPage";
import { PosTablesPage } from "../features/tables/pages/PosTablesPage";
import { SystemDashboardPage } from "../features/system/pages/SystemDashboardPage";
import { AppShell } from "../layouts/AppShell";
import { navigationItems, type NavigationItem } from "../layouts/navigationItems";
import { ComingSoonPage } from "../shared/components/ComingSoonPage";

const moduleNavigationItems = navigationItems.filter(
  (item) => item.to !== "/" && item.to !== "/system",
);

function ModulePlaceholder({ item }: { item: NavigationItem }) {
  const page = <ComingSoonPage title={item.label} />;
  if (item.status === "coming_soon") return page;

  return (
    <PermissionGate
      anyOf={item.anyPermission}
      allOf={item.allPermissions}
      fallback={<AccessDeniedPanel />}
    >
      {page}
    </PermissionGate>
  );
}

function SessionBootstrap() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--kp-bg)] p-4 text-[var(--kp-text)]">
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-info)] p-5 font-black uppercase tracking-[0.08em] text-[var(--kp-info-contrast)] shadow-[var(--kp-shadow-hard)]">
        Recuperando sesión...
      </div>
    </main>
  );
}

function RequireAuth() {
  const { isAuthenticated, isBootstrapping } = useAuthSession();
  if (isBootstrapping) return <SessionBootstrap />;
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

function LoginRoute() {
  const { isAuthenticated, isBootstrapping } = useAuthSession();
  if (isBootstrapping) return <SessionBootstrap />;
  return isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />;
}

export function AppRouter() {
  return (
    <HashRouter>
      <Routes>
        <Route path="login" element={<LoginRoute />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppShell />}>
            <Route index element={<SystemDashboardPage />} />
            <Route path="system" element={<SystemDashboardPage />} />
            <Route
              path="cash"
              element={
                <PermissionGate
                  anyOf={["CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE"]}
                  fallback={<AccessDeniedPanel />}
                >
                  <CashPage />
                </PermissionGate>
              }
            />
            <Route path="pos" element={<PosTablesPage />} />
            {moduleNavigationItems
              .filter((item) => item.to !== "/cash" && item.to !== "/pos")
              .map((item) => (
                <Route
                  key={item.to}
                  path={item.to.slice(1)}
                  element={<ModulePlaceholder item={item} />}
                />
              ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </HashRouter>
  );
}

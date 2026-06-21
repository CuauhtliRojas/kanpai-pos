import { HashRouter, Navigate, Outlet, Route, Routes } from "react-router";
import { LoginPage } from "../features/auth/pages/LoginPage";
import { useAuthSession } from "../features/auth/hooks/useAuthSession";
import { SystemDashboardPage } from "../features/system/pages/SystemDashboardPage";
import { AppShell } from "../layouts/AppShell";

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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </HashRouter>
  );
}

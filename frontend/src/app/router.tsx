import { HashRouter, Navigate, Route, Routes } from "react-router";
import { AppShell } from "../layouts/AppShell";
import { SystemDashboardPage } from "../features/system/pages/SystemDashboardPage";

export function AppRouter() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<SystemDashboardPage />} />
          <Route path="system" element={<SystemDashboardPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

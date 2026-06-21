import { createContext, useContext } from "react";
import type { EmployeeAuthResponse, PinLoginRequest } from "../types/authTypes";

export type AuthSessionContextValue = {
  employee: EmployeeAuthResponse | null;
  sessionToken: string | null;
  expiresAt: string | null;
  roles: string[];
  permissions: string[];
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (payload: PinLoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
};

export const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

export function useAuthSession(): AuthSessionContextValue {
  const context = useContext(AuthSessionContext);
  if (!context) {
    throw new Error("useAuthSession debe usarse dentro de AuthSessionProvider.");
  }
  return context;
}

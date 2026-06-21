import type { PinLoginResponse, StoredAuthSession } from "../types/authTypes";

const AUTH_SESSION_STORAGE_KEY = "kanpai.auth.session.v1";

export function isSessionExpired(expiresAt: string): boolean {
  const expirationTime = Date.parse(expiresAt);
  return !Number.isFinite(expirationTime) || expirationTime <= Date.now();
}

export function saveSession(session: StoredAuthSession | PinLoginResponse): void {
  const storedSession: StoredAuthSession =
    "session_token" in session
      ? {
          employee: session.employee,
          sessionToken: session.session_token,
          expiresAt: session.expires_at,
          roles: [],
          permissions: [],
        }
      : session;

  localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(storedSession));
}

export function readSession(): StoredAuthSession | null {
  const serializedSession = localStorage.getItem(AUTH_SESSION_STORAGE_KEY);

  if (!serializedSession) {
    return null;
  }

  try {
    const session = JSON.parse(serializedSession) as Partial<StoredAuthSession>;
    const isValid =
      typeof session.sessionToken === "string" &&
      typeof session.expiresAt === "string" &&
      typeof session.employee?.id === "number" &&
      typeof session.employee.employee_code === "string" &&
      typeof session.employee.full_name === "string" &&
      (typeof session.employee.pos_alias === "string" || session.employee.pos_alias === null);

    if (!isValid || isSessionExpired(session.expiresAt as string)) {
      clearSession();
      return null;
    }

    return {
      ...(session as StoredAuthSession),
      roles: Array.isArray(session.roles)
        ? session.roles.filter((role): role is string => typeof role === "string")
        : [],
      permissions: Array.isArray(session.permissions)
        ? session.permissions.filter(
            (permission): permission is string => typeof permission === "string",
          )
        : [],
    };
  } catch {
    clearSession();
    return null;
  }
}

export function clearSession(): void {
  localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
}

// Esta capa puede migrarse a almacenamiento seguro de Tauri en una fase futura.

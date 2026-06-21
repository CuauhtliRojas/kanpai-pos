import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { queryKeys } from "../../../api/queryKeys";
import { getMe } from "../api/authApi";
import {
  AuthSessionContext,
  type AuthSessionContextValue,
} from "../hooks/useAuthSession";
import { useLoginMutation } from "../hooks/useLoginMutation";
import { useLogoutMutation } from "../hooks/useLogoutMutation";
import {
  clearSession,
  isSessionExpired,
  readSession,
  saveSession,
} from "../lib/sessionStorage";
import type { PinLoginRequest, StoredAuthSession } from "../types/authTypes";

type AuthSessionProviderProps = { children: ReactNode };

export function AuthSessionProvider({ children }: AuthSessionProviderProps) {
  const queryClient = useQueryClient();
  const loginMutation = useLoginMutation();
  const logoutMutation = useLogoutMutation();
  const [session, setSession] = useState<StoredAuthSession | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const discardSession = useCallback(() => {
    clearSession();
    setSession(null);
    queryClient.removeQueries({ queryKey: queryKeys.auth.me });
  }, [queryClient]);

  useEffect(() => {
    const storedSession = readSession();
    if (!storedSession) {
      setIsBootstrapping(false);
      return;
    }

    let active = true;
    void queryClient
      .fetchQuery({
        queryKey: queryKeys.auth.me,
        queryFn: () => getMe(storedSession.sessionToken),
        staleTime: 0,
        retry: false,
      })
      .then((profile) => {
        if (!active) return;
        const refreshedSession = {
          ...storedSession,
          employee: profile.employee,
          roles: profile.roles,
          permissions: profile.permissions,
        };
        saveSession(refreshedSession);
        setSession(refreshedSession);
      })
      .catch(() => {
        if (active) discardSession();
      })
      .finally(() => {
        if (active) setIsBootstrapping(false);
      });

    return () => {
      active = false;
    };
  }, [discardSession, queryClient]);

  useEffect(() => {
    if (!session) return;

    const remainingMs = Date.parse(session.expiresAt) - Date.now();
    if (remainingMs <= 0) {
      discardSession();
      return;
    }

    const expirationTimer = window.setTimeout(discardSession, remainingMs);
    return () => window.clearTimeout(expirationTimer);
  }, [discardSession, session]);

  const login = useCallback(
    async (payload: PinLoginRequest) => {
      const response = await loginMutation.mutateAsync(payload);
      const profile = await queryClient.fetchQuery({
        queryKey: queryKeys.auth.me,
        queryFn: () => getMe(response.session_token),
        staleTime: 0,
        retry: false,
      });
      const authenticatedSession: StoredAuthSession = {
        employee: profile.employee,
        sessionToken: response.session_token,
        expiresAt: response.expires_at,
        roles: profile.roles,
        permissions: profile.permissions,
      };
      saveSession(authenticatedSession);
      queryClient.removeQueries({ queryKey: queryKeys.auth.me });
      setSession(authenticatedSession);
    },
    [loginMutation, queryClient],
  );

  const logout = useCallback(async () => {
    try {
      if (session?.sessionToken) {
        await logoutMutation.mutateAsync(session.sessionToken);
      }
    } finally {
      discardSession();
    }
  }, [discardSession, logoutMutation, session?.sessionToken]);

  const refreshMe = useCallback(async () => {
    if (!session || isSessionExpired(session.expiresAt)) {
      discardSession();
      return;
    }

    try {
      const profile = await queryClient.fetchQuery({
        queryKey: queryKeys.auth.me,
        queryFn: () => getMe(session.sessionToken),
        staleTime: 0,
        retry: false,
      });
      const refreshedSession = {
        ...session,
        employee: profile.employee,
        roles: profile.roles,
        permissions: profile.permissions,
      };
      saveSession(refreshedSession);
      setSession(refreshedSession);
    } catch (error) {
      discardSession();
      throw error;
    }
  }, [discardSession, queryClient, session]);

  const value = useMemo<AuthSessionContextValue>(
    () => ({
      employee: session?.employee ?? null,
      sessionToken: session?.sessionToken ?? null,
      expiresAt: session?.expiresAt ?? null,
      roles: session?.roles ?? [],
      permissions: session?.permissions ?? [],
      isAuthenticated: session !== null && !isSessionExpired(session.expiresAt),
      isBootstrapping,
      login,
      logout,
      refreshMe,
    }),
    [isBootstrapping, login, logout, refreshMe, session],
  );

  return <AuthSessionContext.Provider value={value}>{children}</AuthSessionContext.Provider>;
}

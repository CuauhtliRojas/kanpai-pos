import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import {
  getEmployeeDetail,
  getEmployeePermissions,
  getEmployees,
  getPermissions,
  getRoles,
} from "../api/securityApi";

export function useEmployeesQuery() {
  return useQuery({
    queryKey: queryKeys.security.employees,
    queryFn: getEmployees,
    retry: false,
  });
}

export function useEmployeeDetailQuery(
  employeeId: number | null,
  sessionToken: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.security.employeeDetail(employeeId ?? 0),
    queryFn: () => {
      if (employeeId === null || !sessionToken) {
        throw new Error("No hay sesión activa.");
      }
      return getEmployeeDetail(employeeId, sessionToken);
    },
    enabled: enabled && employeeId !== null && Boolean(sessionToken),
    retry: false,
  });
}

export function useEmployeePermissionsQuery(
  employeeId: number | null,
  sessionToken: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.security.employeePermissions(employeeId ?? 0),
    queryFn: () => {
      if (employeeId === null || !sessionToken) {
        throw new Error("No hay sesión activa.");
      }
      return getEmployeePermissions(employeeId, sessionToken);
    },
    enabled: enabled && employeeId !== null && Boolean(sessionToken),
    retry: false,
  });
}

export function useRolesQuery(sessionToken: string | null) {
  return useQuery({
    queryKey: queryKeys.security.roles,
    queryFn: () => {
      if (!sessionToken) {
        throw new Error("No hay sesión activa.");
      }
      return getRoles(sessionToken);
    },
    enabled: Boolean(sessionToken),
    retry: false,
  });
}

export function usePermissionsQuery(sessionToken: string | null) {
  return useQuery({
    queryKey: queryKeys.security.permissions,
    queryFn: () => {
      if (!sessionToken) {
        throw new Error("No hay sesión activa.");
      }
      return getPermissions(sessionToken);
    },
    enabled: Boolean(sessionToken),
    retry: false,
  });
}

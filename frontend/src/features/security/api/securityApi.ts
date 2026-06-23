import { apiRequest } from "../../../api/http";
import type {
  EmployeeDetail,
  EmployeeListItem,
  EmployeePermissions,
  Permission,
  Role,
} from "../types/securityTypes";

function sessionHeaders(sessionToken: string) {
  return { "X-Kanpai-Session": sessionToken };
}

export function getEmployees(): Promise<EmployeeListItem[]> {
  return apiRequest<EmployeeListItem[]>("/api/v1/operations/employees");
}

export function getEmployeeDetail(
  employeeId: number,
  sessionToken: string,
): Promise<EmployeeDetail> {
  return apiRequest<EmployeeDetail>(`/api/v1/operations/employees/${employeeId}`, {
    headers: sessionHeaders(sessionToken),
  });
}

export function getEmployeePermissions(
  employeeId: number,
  sessionToken: string,
): Promise<EmployeePermissions> {
  return apiRequest<EmployeePermissions>(
    `/api/v1/operations/employees/${employeeId}/permissions`,
    {
      headers: sessionHeaders(sessionToken),
    },
  );
}

export function getRoles(sessionToken: string): Promise<Role[]> {
  return apiRequest<Role[]>("/api/v1/operations/roles", {
    headers: sessionHeaders(sessionToken),
  });
}

export function getPermissions(sessionToken: string): Promise<Permission[]> {
  return apiRequest<Permission[]>("/api/v1/operations/permissions", {
    headers: sessionHeaders(sessionToken),
  });
}

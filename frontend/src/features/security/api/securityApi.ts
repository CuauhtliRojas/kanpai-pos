import { apiRequest } from "../../../api/http";
import type { Employee } from "../types/securityTypes";

export function getEmployees(): Promise<Employee[]> {
  return apiRequest<Employee[]>("/api/v1/operations/employees");
}

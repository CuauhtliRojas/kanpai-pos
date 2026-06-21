import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getEmployees } from "../api/securityApi";

export function useEmployeesQuery() {
  return useQuery({
    queryKey: queryKeys.security.employees,
    queryFn: getEmployees,
    retry: false,
  });
}

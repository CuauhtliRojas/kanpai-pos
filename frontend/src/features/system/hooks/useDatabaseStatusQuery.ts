import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { getDatabaseStatus } from "../api/systemApi";

export function useDatabaseStatusQuery() {
  const { sessionToken } = useAuthSession();

  return useQuery({
    queryKey: [...queryKeys.system.databaseStatus, sessionToken ?? "sin-sesion"],
    queryFn: () => {
      if (!sessionToken) throw new Error("No hay sesión activa.");
      return getDatabaseStatus(sessionToken);
    },
    enabled: Boolean(sessionToken),
    retry: false,
  });
}

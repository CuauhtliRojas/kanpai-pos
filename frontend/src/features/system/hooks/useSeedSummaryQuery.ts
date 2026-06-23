import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { getSeedSummary } from "../api/systemApi";

export function useSeedSummaryQuery() {
  const { sessionToken } = useAuthSession();

  return useQuery({
    queryKey: [...queryKeys.system.seedSummary, sessionToken ?? "sin-sesion"],
    queryFn: () => {
      if (!sessionToken) throw new Error("No hay sesión activa.");
      return getSeedSummary(sessionToken);
    },
    enabled: Boolean(sessionToken),
    retry: false,
  });
}

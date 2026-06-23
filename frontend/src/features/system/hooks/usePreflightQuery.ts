import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { getPreflight } from "../api/systemApi";

export function usePreflightQuery() {
  const { sessionToken } = useAuthSession();

  return useQuery({
    queryKey: [...queryKeys.system.preflight, sessionToken ?? "sin-sesion"],
    queryFn: () => {
      if (!sessionToken) throw new Error("No hay sesión activa.");
      return getPreflight(sessionToken);
    },
    enabled: Boolean(sessionToken),
    retry: false,
  });
}

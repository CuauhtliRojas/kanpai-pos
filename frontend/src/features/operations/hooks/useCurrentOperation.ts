import { createContext, useContext } from "react";
import type { CurrentOperationContextValue } from "../types/operationTypes";

export const CurrentOperationContext =
  createContext<CurrentOperationContextValue | null>(null);

export function useCurrentOperation(): CurrentOperationContextValue {
  const context = useContext(CurrentOperationContext);
  if (!context) {
    throw new Error(
      "useCurrentOperation debe usarse dentro de CurrentOperationProvider.",
    );
  }
  return context;
}

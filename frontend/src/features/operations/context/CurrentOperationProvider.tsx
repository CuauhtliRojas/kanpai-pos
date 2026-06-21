import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import type { DiningTable, Ticket } from "../../tables/types/tableTypes";
import {
  CurrentOperationContext,
} from "../hooks/useCurrentOperation";
import type {
  CurrentOperationContextValue,
  CurrentOperationState,
} from "../types/operationTypes";

type CurrentOperationProviderProps = {
  children: ReactNode;
};

const emptyOperation: CurrentOperationState = {
  selectedTable: null,
  activeTicket: null,
};

export function CurrentOperationProvider({
  children,
}: CurrentOperationProviderProps) {
  const { employee } = useAuthSession();
  const [operation, setOperation] = useState<CurrentOperationState>(emptyOperation);
  const [knownTickets, setKnownTickets] = useState<Record<number, Ticket>>({});

  const clearCurrentOperation = useCallback(() => {
    setOperation(emptyOperation);
    setKnownTickets({});
  }, []);

  useEffect(() => {
    clearCurrentOperation();
  }, [clearCurrentOperation, employee?.id]);

  const selectTable = useCallback((table: DiningTable) => {
    setOperation({
      selectedTable: table,
      activeTicket: knownTickets[table.id] ?? null,
    });
  }, [knownTickets]);

  const setActiveTicket = useCallback((ticket: Ticket | null) => {
    setOperation((current) => ({ ...current, activeTicket: ticket }));
    if (ticket) {
      setKnownTickets((current) => ({ ...current, [ticket.table_id]: ticket }));
    }
  }, []);

  const setCurrentOperation = useCallback((table: DiningTable, ticket: Ticket) => {
    setOperation({ selectedTable: table, activeTicket: ticket });
    setKnownTickets((current) => ({ ...current, [table.id]: ticket }));
  }, []);

  const value = useMemo<CurrentOperationContextValue>(
    () => ({
      ...operation,
      selectTable,
      setActiveTicket,
      setCurrentOperation,
      clearCurrentOperation,
    }),
    [clearCurrentOperation, operation, selectTable, setActiveTicket, setCurrentOperation],
  );

  return (
    <CurrentOperationContext.Provider value={value}>
      {children}
    </CurrentOperationContext.Provider>
  );
}

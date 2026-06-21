import type { DiningTable, Ticket } from "../../tables/types/tableTypes";

export type CurrentOperationState = {
  selectedTable: DiningTable | null;
  activeTicket: Ticket | null;
};

export type CurrentOperationContextValue = CurrentOperationState & {
  selectTable: (table: DiningTable) => void;
  setActiveTicket: (ticket: Ticket | null) => void;
  setCurrentOperation: (table: DiningTable, ticket: Ticket) => void;
  clearCurrentOperation: () => void;
};

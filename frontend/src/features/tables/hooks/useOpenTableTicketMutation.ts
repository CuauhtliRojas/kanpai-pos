import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { openTableTicket } from "../api/tablesApi";
import type { DiningTable, TicketOpenRequest } from "../types/tableTypes";

type OpenTableTicketVariables = {
  table: DiningTable;
  payload: TicketOpenRequest;
};

export function useOpenTableTicketMutation() {
  const queryClient = useQueryClient();
  const { setCurrentOperation } = useCurrentOperation();

  return useMutation({
    mutationFn: ({ table, payload }: OpenTableTicketVariables) =>
      openTableTicket(table.id, payload),
    onSuccess: async (ticket, variables) => {
      const occupiedTable = { ...variables.table, status: "Ocupada" };
      setCurrentOperation(occupiedTable, ticket);
      queryClient.setQueryData(queryKeys.tickets.detail(ticket.id), ticket);
      await queryClient.invalidateQueries({ queryKey: queryKeys.tables.list });
    },
  });
}

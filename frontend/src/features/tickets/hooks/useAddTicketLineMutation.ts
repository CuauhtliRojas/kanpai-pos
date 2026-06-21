import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import type { Ticket } from "../../tables/types/tableTypes";
import { addTicketLine } from "../api/ticketsApi";
import type { TicketLineCreateRequest } from "../types/ticketTypes";

type AddTicketLineVariables = {
  ticketId: number;
  payload: TicketLineCreateRequest;
};

export function useAddTicketLineMutation() {
  const queryClient = useQueryClient();
  const { activeTicket, setActiveTicket } = useCurrentOperation();

  return useMutation({
    mutationFn: ({ ticketId, payload }: AddTicketLineVariables) =>
      addTicketLine(ticketId, payload),
    onSuccess: async (result, variables) => {
      if (activeTicket?.id === variables.ticketId) {
        const updatedTicket: Ticket = { ...activeTicket, ...result.ticket_totals };
        setActiveTicket(updatedTicket);
        queryClient.setQueryData(queryKeys.tickets.detail(variables.ticketId), updatedTicket);
      }

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.detail(variables.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lines(variables.ticketId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.tables.list }),
      ]);
    },
  });
}

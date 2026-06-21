import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { updateProductionOrder } from "../api/productionApi";
import type { ProductionAction } from "../types/productionTypes";

export function useProductionActionMutation(action: ProductionAction) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { orderId: number; stationId: number; employeeId: number }) =>
      updateProductionOrder(action, input),
    onSuccess: async (_order, input) => {
      await queryClient.invalidateQueries({
        queryKey: queryKeys.production.orders(input.stationId),
      });
    },
  });
}

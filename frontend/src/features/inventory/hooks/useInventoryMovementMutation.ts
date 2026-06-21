import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { createInventoryMovement } from "../api/inventoryApi";

export function useInventoryMovementMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createInventoryMovement,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.inventory.items }),
        queryClient.invalidateQueries({ queryKey: queryKeys.inventory.stockAlerts }),
      ]);
    },
  });
}

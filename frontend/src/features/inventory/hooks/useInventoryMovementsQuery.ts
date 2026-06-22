import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getInventoryMovements } from "../api/inventoryApi";
import type { InventoryMovementHistoryParams } from "../types/inventoryTypes";

export function useInventoryMovementsQuery(
  params: InventoryMovementHistoryParams,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.inventory.movements(params),
    queryFn: () => getInventoryMovements(params),
    enabled,
    retry: false,
  });
}

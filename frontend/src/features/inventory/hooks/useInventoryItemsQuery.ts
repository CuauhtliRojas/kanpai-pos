import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getInventoryItems } from "../api/inventoryApi";

export function useInventoryItemsQuery() {
  return useQuery({
    queryKey: queryKeys.inventory.items,
    queryFn: getInventoryItems,
    retry: false,
  });
}

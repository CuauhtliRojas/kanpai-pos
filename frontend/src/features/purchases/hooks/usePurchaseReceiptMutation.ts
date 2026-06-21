import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { createPurchaseReceipt } from "../api/purchasesApi";

export function usePurchaseReceiptMutation() {
  const client = useQueryClient();
  return useMutation({ mutationFn: createPurchaseReceipt, onSuccess: async () => { await Promise.all([client.invalidateQueries({ queryKey: queryKeys.inventory.items }), client.invalidateQueries({ queryKey: queryKeys.inventory.stockAlerts }), client.invalidateQueries({ queryKey: queryKeys.cash.current })]); } });
}

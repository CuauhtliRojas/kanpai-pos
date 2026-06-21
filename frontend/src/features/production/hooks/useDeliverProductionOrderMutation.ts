import { useProductionActionMutation } from "./useProductionActionMutation";

export function useDeliverProductionOrderMutation() {
  return useProductionActionMutation("deliver");
}

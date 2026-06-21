import { useProductionActionMutation } from "./useProductionActionMutation";

export function useFinishProductionOrderMutation() {
  return useProductionActionMutation("complete");
}

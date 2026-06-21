import { useProductionActionMutation } from "./useProductionActionMutation";

export function useAcceptProductionOrderMutation() {
  return useProductionActionMutation("receive");
}

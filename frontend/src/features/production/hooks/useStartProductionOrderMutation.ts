import { useProductionActionMutation } from "./useProductionActionMutation";

export function useStartProductionOrderMutation() {
  return useProductionActionMutation("start");
}

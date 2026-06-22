import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDiscountPresets } from "../api/discountsApi";

export function useDiscountPresetsQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.discounts.presets,
    queryFn: getDiscountPresets,
    enabled,
    retry: false,
  });
}

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProductVariantGroups } from "../api/variantsApi";

export function useProductVariantGroupsQuery(productId: number | null) {
  return useQuery({
    queryKey: queryKeys.catalog.productVariantGroups(productId ?? 0),
    queryFn: () => getProductVariantGroups(productId ?? 0),
    enabled: productId !== null,
    retry: false,
  });
}

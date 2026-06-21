import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getProducts } from "../api/productsApi";

export function useProductsQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.catalog.products,
    queryFn: getProducts,
    enabled,
    retry: false,
  });
}

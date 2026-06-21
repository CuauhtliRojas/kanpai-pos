import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getCategories } from "../api/productsApi";

export function useCategoriesQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.catalog.categories,
    queryFn: getCategories,
    enabled,
    retry: false,
  });
}

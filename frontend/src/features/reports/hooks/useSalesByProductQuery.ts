import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailySalesByProduct } from "../api/reportsApi";

export function useSalesByProductQuery() {
  return useQuery({ queryKey: queryKeys.reports.salesByProduct, queryFn: getDailySalesByProduct, retry: false });
}

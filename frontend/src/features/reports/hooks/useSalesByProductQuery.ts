import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getSalesByProduct } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useSalesByProductQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.salesByProduct(range),
    queryFn: () => getSalesByProduct(range),
    retry: false,
  });
}

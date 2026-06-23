import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getSalesByPaymentMethod } from "../api/reportsApi";
import type { ReportDateRange } from "../types/reportTypes";

export function useSalesByPaymentMethodQuery(range: ReportDateRange) {
  return useQuery({
    queryKey: queryKeys.reports.salesByPaymentMethod(range),
    queryFn: () => getSalesByPaymentMethod(range),
    retry: false,
  });
}

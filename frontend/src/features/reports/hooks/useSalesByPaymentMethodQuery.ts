import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getDailySalesByPaymentMethod } from "../api/reportsApi";

export function useSalesByPaymentMethodQuery() {
  return useQuery({
    queryKey: queryKeys.reports.salesByPaymentMethod,
    queryFn: getDailySalesByPaymentMethod,
    retry: false,
  });
}

import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../api/queryKeys";
import { getPaymentMethods } from "../api/paymentsApi";

export function usePaymentMethodsQuery(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.catalog.paymentMethods,
    queryFn: getPaymentMethods,
    enabled,
    retry: false,
  });
}

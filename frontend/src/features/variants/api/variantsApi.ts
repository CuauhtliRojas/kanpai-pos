import { apiRequest } from "../../../api/http";
import type { VariantGroup } from "../types/variantTypes";

export function getProductVariantGroups(productId: number): Promise<VariantGroup[]> {
  return apiRequest<VariantGroup[]>(`/api/v1/catalog/products/${productId}/variant-groups`);
}

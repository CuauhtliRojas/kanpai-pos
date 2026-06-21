import { apiRequest } from "../../../api/http";
import type { PurchaseReceiptCreateRequest, PurchaseReceiptResponse } from "../types/purchaseTypes";

export function createPurchaseReceipt(payload: PurchaseReceiptCreateRequest): Promise<PurchaseReceiptResponse> {
  return apiRequest<PurchaseReceiptResponse>("/api/v1/inventory/purchase-receipts", { method: "POST", body: JSON.stringify(payload) });
}

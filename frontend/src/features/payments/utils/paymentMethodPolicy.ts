import type { PaymentMethod } from "../types/paymentTypes";

function methodText(method: PaymentMethod | null | undefined): string {
  return `${method?.method_key ?? ""} ${method?.name ?? ""}`.toLocaleLowerCase("es-MX");
}

export function isCashMethod(method: PaymentMethod | null | undefined): boolean {
  return methodText(method).includes("efectivo");
}

export function isCardMethod(method: PaymentMethod | null | undefined): boolean {
  const text = methodText(method);
  return text.includes("tarjeta") || text.includes("card");
}

export function isTransferMethod(method: PaymentMethod | null | undefined): boolean {
  return methodText(method).includes("transfer");
}

export function requiresPaymentReference(method: PaymentMethod | null | undefined): boolean {
  if (!method || isCashMethod(method) || isCardMethod(method)) return false;
  if (isTransferMethod(method)) return true;
  return method.requires_reference;
}

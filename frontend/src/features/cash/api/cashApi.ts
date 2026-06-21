import { ApiError, apiRequest } from "../../../api/http";
import type {
  CashExpense,
  CashExpenseCreate,
  CashShift,
  CashShiftClose,
  CashShiftCloseResult,
  CashShiftOpen,
  CashShiftSummary,
} from "../types/cashTypes";

export async function getCurrentCashShift(): Promise<CashShift | null> {
  try {
    return await apiRequest<CashShift>("/api/v1/pos/cash-shifts/current");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function openCashShift(payload: CashShiftOpen): Promise<CashShift> {
  return apiRequest<CashShift>("/api/v1/pos/cash-shifts/open", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCashShiftSummary(cashShiftId: number): Promise<CashShiftSummary> {
  return apiRequest<CashShiftSummary>(
    `/api/v1/pos/cash-shifts/${cashShiftId}/summary`,
  );
}

export function closeCashShift(
  cashShiftId: number,
  payload: CashShiftClose,
): Promise<CashShiftCloseResult> {
  return apiRequest<CashShiftCloseResult>(
    `/api/v1/pos/cash-shifts/${cashShiftId}/close`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function createCashExpense(payload: CashExpenseCreate): Promise<CashExpense> {
  return apiRequest<CashExpense>("/api/v1/pos/cash-expenses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

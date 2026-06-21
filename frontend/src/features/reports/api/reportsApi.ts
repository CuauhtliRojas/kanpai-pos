import { apiRequest } from "../../../api/http";
import type {
  InventoryConsumptionItem,
  OperationalSummary,
  PrintJobsSummary,
  ProductionTimesItem,
  SalesByPaymentMethodItem,
  SalesByProductItem,
} from "../types/reportTypes";

function todaySearch(): string {
  const now = new Date();
  const date = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
  return `?date_from=${date}&date_to=${date}`;
}

export function getDailyOperationalSummary(): Promise<OperationalSummary> {
  return apiRequest<OperationalSummary>(`/api/v1/reports/operational-summary${todaySearch()}`);
}

export function getDailySalesByProduct(): Promise<SalesByProductItem[]> {
  return apiRequest<SalesByProductItem[]>(`/api/v1/reports/sales-by-product${todaySearch()}`);
}

export function getDailySalesByPaymentMethod(): Promise<SalesByPaymentMethodItem[]> {
  return apiRequest<SalesByPaymentMethodItem[]>(`/api/v1/reports/sales-by-payment-method${todaySearch()}`);
}

export function getDailyInventoryConsumption(): Promise<InventoryConsumptionItem[]> {
  return apiRequest<InventoryConsumptionItem[]>(`/api/v1/reports/inventory-consumption${todaySearch()}`);
}

export function getDailyProductionTimes(): Promise<ProductionTimesItem[]> {
  return apiRequest<ProductionTimesItem[]>(`/api/v1/reports/production-times${todaySearch()}`);
}

export function getDailyPrintJobsSummary(): Promise<PrintJobsSummary> {
  return apiRequest<PrintJobsSummary>(`/api/v1/reports/print-jobs-summary${todaySearch()}`);
}

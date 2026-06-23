import { apiRequest } from "../../../api/http";
import type {
  InventoryConsumptionItem,
  OperationalSummary,
  PrintJobsSummary,
  ProductionTimesItem,
  ReportDateRange,
  SalesByCategoryItem,
  SalesByPaymentMethodItem,
  SalesByProductItem,
} from "../types/reportTypes";

function rangeSearch(range: ReportDateRange): string {
  const searchParams = new URLSearchParams();
  searchParams.set("date_from", range.dateFrom);
  searchParams.set("date_to", range.dateTo);
  return `?${searchParams.toString()}`;
}

export function getOperationalSummary(range: ReportDateRange): Promise<OperationalSummary> {
  return apiRequest<OperationalSummary>(`/api/v1/reports/operational-summary${rangeSearch(range)}`);
}

export function getSalesByProduct(range: ReportDateRange): Promise<SalesByProductItem[]> {
  return apiRequest<SalesByProductItem[]>(`/api/v1/reports/sales-by-product${rangeSearch(range)}`);
}

export function getSalesByPaymentMethod(range: ReportDateRange): Promise<SalesByPaymentMethodItem[]> {
  return apiRequest<SalesByPaymentMethodItem[]>(`/api/v1/reports/sales-by-payment-method${rangeSearch(range)}`);
}

export function getSalesByCategory(range: ReportDateRange): Promise<SalesByCategoryItem[]> {
  return apiRequest<SalesByCategoryItem[]>(`/api/v1/reports/sales-by-category${rangeSearch(range)}`);
}

export function getInventoryConsumption(range: ReportDateRange): Promise<InventoryConsumptionItem[]> {
  return apiRequest<InventoryConsumptionItem[]>(`/api/v1/reports/inventory-consumption${rangeSearch(range)}`);
}

export function getProductionTimes(range: ReportDateRange): Promise<ProductionTimesItem[]> {
  return apiRequest<ProductionTimesItem[]>(`/api/v1/reports/production-times${rangeSearch(range)}`);
}

export function getPrintJobsSummary(range: ReportDateRange): Promise<PrintJobsSummary> {
  return apiRequest<PrintJobsSummary>(`/api/v1/reports/print-jobs-summary${rangeSearch(range)}`);
}

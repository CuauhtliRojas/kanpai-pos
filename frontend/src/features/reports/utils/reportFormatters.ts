export function formatReportQuantity(value: number | string | null | undefined): string {
  if (value == null) return "0";

  const numericValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numericValue)) return String(value);

  return new Intl.NumberFormat("es-MX", {
    maximumFractionDigits: 3,
  }).format(numericValue);
}

export function formatSoldLabel(quantity: number): string {
  return quantity === 1 ? "1 vendido" : `${formatReportQuantity(quantity)} vendidos`;
}

export function formatBasisPoints(value: number | null): string | null {
  if (value === null) return null;
  return `${new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 }).format(value / 100)}%`;
}

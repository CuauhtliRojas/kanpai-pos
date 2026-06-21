export function parsePesosToCents(value: string): number | null {
  const normalized = value.trim();
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(normalized);

  if (!match) return null;

  const pesos = Number(match[1]);
  const cents = Number((match[2] ?? "").padEnd(2, "0"));
  if (!Number.isSafeInteger(pesos)) return null;

  const total = pesos * 100 + cents;
  return Number.isSafeInteger(total) ? total : null;
}

export function formatCentsToPesos(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "$0.00";

  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

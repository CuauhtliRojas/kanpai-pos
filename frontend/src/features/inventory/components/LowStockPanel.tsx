import { useMemo, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { formatNullableDate } from "../../../shared/lib/formatters";
import type { InventoryItem, StockAlert } from "../types/inventoryTypes";
import { formatInventoryQuantity } from "../lib/inventoryFormatters";

type Props = {
  alerts: StockAlert[];
  items: InventoryItem[];
};

function toNumber(value: string | number): number {
  const parsed = typeof value === "string" ? Number.parseFloat(value) : value;
  return Number.isFinite(parsed) ? parsed : 0;
}

function getFallbackName(message: string, fallbackId: number): string {
  const beforeColon = message.split(":")[0]?.trim();
  if (beforeColon && beforeColon.length > 1 && !beforeColon.toLowerCase().startsWith("stock")) {
    return beforeColon;
  }

  return `Insumo #${fallbackId}`;
}

function getAlertStatus(alert: StockAlert): "agotado" | "bajo" {
  const current = toNumber(alert.current_quantity);
  if (current <= 0) return "agotado";

  const alertType = alert.alert_type.toLowerCase();
  if (
    alertType.includes("agotado") ||
    alertType.includes("sin_stock") ||
    alertType.includes("sin stock")
  ) {
    return "agotado";
  }

  return "bajo";
}

function getStatusLabel(status: "agotado" | "bajo"): string {
  return status === "agotado" ? "Agotado" : "Bajo stock";
}

export function LowStockPanel({ alerts, items }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  const itemById = useMemo(() => {
    return new Map(items.map((item) => [item.id, item]));
  }, [items]);

  if (alerts.length === 0) return null;

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]">
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls="inventory-stock-alerts"
        onClick={() => setIsExpanded((current) => !current)}
        className="flex w-full items-center justify-between gap-4 border-b-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-4 py-3 text-left text-[var(--kp-warning-contrast)]"
      >
        <span className="flex min-w-0 items-center gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span className="min-w-0">
            <span className="block text-sm font-black uppercase tracking-[0.1em]">
              Alertas de stock
            </span>
            <span className="block text-xs font-bold">
              {alerts.length === 1
                ? "1 insumo requiere revisión."
                : `${alerts.length} insumos requieren revisión.`}
            </span>
          </span>
        </span>

        <span className="inline-flex shrink-0 items-center gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-3 py-1 text-xs font-black uppercase text-[var(--kp-text)]">
          {isExpanded ? "Ocultar" : "Mostrar"}
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </span>
      </button>

      {isExpanded ? (
        <div id="inventory-stock-alerts" className="overflow-x-auto">
          <div className="min-w-[920px]">
            <div className="grid grid-cols-[minmax(260px,1fr)_130px_150px_150px_170px] gap-3 border-b-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-4 py-2 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
              <span>Insumo</span>
              <span>Estado</span>
              <span className="text-right">Actual</span>
              <span className="text-right">Mínimo</span>
              <span>Abierta</span>
            </div>

            <div className="max-h-72 overflow-y-auto divide-y-2 divide-[var(--kp-ink)]">
              {alerts.map((alert) => {
                const item = itemById.get(alert.inventory_item_id);
                const status = getAlertStatus(alert);
                const unit = item?.base_unit_name ?? "";
                const name = item?.name ?? getFallbackName(alert.message, alert.inventory_item_id);
                const sku = item?.sku ?? `#${alert.inventory_item_id}`;

                return (
                  <div
                    key={alert.id}
                    className="grid grid-cols-[minmax(260px,1fr)_130px_150px_150px_170px] items-center gap-3 px-4 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-black uppercase">{name}</p>
                      <p className="text-xs font-bold text-[var(--kp-muted)]">{sku}</p>
                    </div>

                    <span
                      className={[
                        "inline-flex w-fit border-2 border-[var(--kp-ink)] px-2 py-0.5 text-xs font-black uppercase",
                        status === "agotado"
                          ? "bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]"
                          : "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
                      ].join(" ")}
                    >
                      {getStatusLabel(status)}
                    </span>

                    <span className="text-right text-sm font-black">
                      {formatInventoryQuantity(alert.current_quantity)}{" "}
                      <span className="text-xs text-[var(--kp-muted)]">{unit}</span>
                    </span>

                    <span className="text-right text-sm font-bold text-[var(--kp-muted)]">
                      {formatInventoryQuantity(alert.threshold_quantity)}{" "}
                      <span className="text-xs">{unit}</span>
                    </span>

                    <span className="text-xs font-bold text-[var(--kp-muted)]">
                      {formatNullableDate(alert.opened_at)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

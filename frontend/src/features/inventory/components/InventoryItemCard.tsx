import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import type { InventoryItem } from "../types/inventoryTypes";
import { formatInventoryQuantity } from "../lib/inventoryFormatters";

type Props = {
  item: InventoryItem;
  onAdjust?: (item: InventoryItem) => void;
  onViewMovements?: (item: InventoryItem) => void;
};

type StatusInfo = { label: string; badgeClass: string; iconType: "ok" | "warning" | "danger" };

function getStatusInfo(status: string): StatusInfo {
  const lower = status.toLowerCase();
  if (lower.includes("agotado") || lower.includes("sin stock")) {
    return {
      label: "Agotado",
      badgeClass:
        "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
      iconType: "danger",
    };
  }
  if (lower.includes("bajo") || lower.includes("minimo") || lower.includes("mínimo")) {
    return {
      label: "Bajo stock",
      badgeClass:
        "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
      iconType: "warning",
    };
  }
  return {
    label: "Correcto",
    badgeClass:
      "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
    iconType: "ok",
  };
}

export function InventoryItemCard({ item, onAdjust, onViewMovements }: Props) {
  const si = getStatusInfo(item.stock_status);
  const hasActions = (onAdjust && item.active) || onViewMovements;
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-black uppercase leading-tight">{item.name}</p>
          <p className="mt-0.5 text-xs font-bold text-[var(--kp-muted)]">{item.sku}</p>
        </div>
        <span
          className={`inline-flex shrink-0 items-center gap-1 border-2 px-2 py-0.5 text-xs font-black uppercase ${si.badgeClass}`}
        >
          {si.iconType === "danger" && <XCircle className="h-3 w-3" />}
          {si.iconType === "warning" && <AlertTriangle className="h-3 w-3" />}
          {si.iconType === "ok" && <CheckCircle className="h-3 w-3" />}
          {si.label}
        </span>
      </div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Stock
          </p>
          <p className="text-xl font-black leading-none">
            {formatInventoryQuantity(item.current_stock)}{" "}
            <span className="text-xs font-bold text-[var(--kp-muted)]">
              {item.base_unit_name}
            </span>
          </p>
          <p className="mt-0.5 text-xs font-bold text-[var(--kp-muted)]">
            Min: {formatInventoryQuantity(item.stock_minimum)} {item.base_unit_name}
          </p>
        </div>
        {hasActions && (
          <div className="flex shrink-0 gap-2">
            {onViewMovements && (
              <button
                type="button"
                onClick={() => onViewMovements(item)}
                className="min-h-[var(--kp-touch-sm)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-xs font-black uppercase shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
              >
                Movimientos
              </button>
            )}
            {onAdjust && item.active && (
              <button
                type="button"
                onClick={() => onAdjust(item)}
                className="min-h-[var(--kp-touch-sm)] border-4 border-[var(--kp-ink)] bg-[var(--kp-accent)] px-3 text-xs font-black uppercase text-[var(--kp-accent-contrast)] shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
              >
                Ajustar
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

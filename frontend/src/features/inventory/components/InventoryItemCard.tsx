import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import type { InventoryItem } from "../types/inventoryTypes";

type Props = {
  item: InventoryItem;
  onAdjust?: (item: InventoryItem) => void;
};

function StatusChip({ status }: { status: string }) {
  const lower = status.toLowerCase();
  if (lower.includes("agotado") || lower.includes("sin stock")) {
    return (
      <span className="inline-flex items-center gap-1 border-2 border-[var(--kp-ink)] bg-[var(--kp-danger)] px-2 py-0.5 text-xs font-black uppercase text-[var(--kp-danger-contrast)]">
        <XCircle className="h-3 w-3" /> Agotado
      </span>
    );
  }
  if (lower.includes("bajo") || lower.includes("minimo") || lower.includes("mínimo")) {
    return (
      <span className="inline-flex items-center gap-1 border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-2 py-0.5 text-xs font-black uppercase text-[var(--kp-warning-contrast)]">
        <AlertTriangle className="h-3 w-3" /> Bajo stock
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 border-2 border-[var(--kp-ink)] bg-[var(--kp-success)] px-2 py-0.5 text-xs font-black uppercase text-[var(--kp-success-contrast)]">
      <CheckCircle className="h-3 w-3" /> Disponible
    </span>
  );
}

export function InventoryItemCard({ item, onAdjust }: Props) {
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard-sm)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-black uppercase">{item.name}</p>
          <p className="mt-0.5 text-xs font-bold text-[var(--kp-muted)]">{item.sku}</p>
        </div>
        <StatusChip status={item.stock_status} />
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.1em] text-[var(--kp-muted)]">Stock</p>
          <p className="text-2xl font-black leading-none">
            {item.current_stock}{" "}
            <span className="text-sm font-bold text-[var(--kp-muted)]">{item.base_unit_name}</span>
          </p>
          <p className="mt-0.5 text-xs font-bold text-[var(--kp-muted)]">
            Mínimo: {item.stock_minimum} {item.base_unit_name}
          </p>
        </div>
        {onAdjust && item.active && (
          <button
            type="button"
            onClick={() => onAdjust(item)}
            className="min-h-[var(--kp-touch-sm)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-xs font-black uppercase shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
          >
            Ajustar
          </button>
        )}
      </div>
    </div>
  );
}

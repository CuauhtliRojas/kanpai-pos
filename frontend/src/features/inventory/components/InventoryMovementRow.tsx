import type { InventoryItem, InventoryMovementHistoryItem } from "../types/inventoryTypes";
import { formatInventoryQuantity } from "../lib/inventoryFormatters";
import { formatNullableDate } from "../../../shared/lib/formatters";

const SOURCE_TYPE_LABELS: Record<string, string> = {
  Manual: "Manual",
  "Linea ticket": "Venta",
  PurchaseReceiptLine: "Recepción",
  "Componente de paquete": "Paquete",
  "Opcion variante": "Variante",
};

function formatSourceType(source: string | null): string {
  if (!source) return "Manual";
  return SOURCE_TYPE_LABELS[source] ?? source.replace(/_/g, " ");
}

function getMovementTypeBadgeClass(type: string): string {
  if (type === "Compra" || type === "Ajuste entrada") {
    return "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]";
  }
  if (type === "Merma") {
    return "bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]";
  }
  if (type === "Ajuste salida" || type === "Consumo venta") {
    return "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]";
  }
  return "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]";
}

function parseSignedQty(
  signedValue: string,
  unitName?: string,
): { text: string; positive: boolean } {
  const num = parseFloat(signedValue);
  if (!Number.isFinite(num)) {
    return { text: unitName ? `${signedValue} ${unitName}` : signedValue, positive: true };
  }
  const fmt = formatInventoryQuantity(Math.abs(num));
  const text =
    num >= 0
      ? `+${fmt}${unitName ? ` ${unitName}` : ""}`
      : `-${fmt}${unitName ? ` ${unitName}` : ""}`;
  return { text, positive: num >= 0 };
}

type Props = {
  movement: InventoryMovementHistoryItem;
  item?: InventoryItem;
  showItemName: boolean;
};

export function InventoryMovementRow({ movement, item, showItemName }: Props) {
  const unitName = item?.base_unit_name;
  const { text: qtyText, positive } = parseSignedQty(
    movement.signed_quantity_base,
    unitName,
  );
  const badgeClass = getMovementTypeBadgeClass(movement.movement_type);
  const hasTags =
    movement.purchase_receipt_line_id !== null ||
    movement.ticket_line_id !== null ||
    movement.cash_expense_id !== null;

  return (
    <div className="border-b-2 border-[var(--kp-ink)] px-4 py-3 last:border-b-0">
      {/* Line 1: tipo, folio, cantidad, fecha */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span
          className={`shrink-0 border-2 border-[var(--kp-ink)] px-2 py-0.5 text-xs font-black uppercase ${badgeClass}`}
        >
          {movement.movement_type}
        </span>
        <span className="text-xs font-bold text-[var(--kp-muted)]">{movement.folio}</span>
        <span
          className={`ml-auto text-sm font-black ${
            positive ? "text-[var(--kp-success)]" : "text-[var(--kp-danger)]"
          }`}
        >
          {qtyText}
        </span>
        <span className="shrink-0 text-xs text-[var(--kp-muted)]">
          {formatNullableDate(movement.created_at)}
        </span>
      </div>

      {/* Line 2: insumo (modo general), stock antes/después, origen, empleado */}
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs font-bold">
        {showItemName && (
          <span className="font-black uppercase text-[var(--kp-text)]">
            {movement.item_name}
          </span>
        )}
        {(movement.stock_before_base !== null || movement.stock_after_base !== null) && (
          <span className="text-[var(--kp-muted)]">
            {movement.stock_before_base !== null
              ? formatInventoryQuantity(movement.stock_before_base)
              : "—"}
            {" → "}
            {movement.stock_after_base !== null
              ? formatInventoryQuantity(movement.stock_after_base)
              : "—"}
            {unitName ? ` ${unitName}` : ""}
          </span>
        )}
        <span className="text-[var(--kp-muted)]">{formatSourceType(movement.source_type)}</span>
        {movement.employee_name && (
          <span className="text-[var(--kp-muted)]">{movement.employee_name}</span>
        )}
      </div>

      {/* Line 3: motivo e indicadores */}
      {(movement.reason ?? hasTags) ? (
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          {movement.reason && (
            <span className="italic text-xs text-[var(--kp-muted)]">
              {movement.reason}
            </span>
          )}
          {movement.purchase_receipt_line_id !== null && (
            <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-1.5 py-0.5 text-xs font-bold">
              Recepción
            </span>
          )}
          {movement.ticket_line_id !== null && (
            <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-1.5 py-0.5 text-xs font-bold">
              Venta
            </span>
          )}
          {movement.cash_expense_id !== null && (
            <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-1.5 py-0.5 text-xs font-bold">
              Gasto asociado
            </span>
          )}
        </div>
      ) : null}
    </div>
  );
}

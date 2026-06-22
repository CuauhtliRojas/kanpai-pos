import { useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { InventoryItem, InventoryMovementCreateRequest } from "../types/inventoryTypes";
import { formatInventoryQuantity } from "../lib/inventoryFormatters";

type AdjustType = "aumentar" | "reducir" | "merma";

type AdjustOption = {
  value: AdjustType;
  label: string;
  movementType: string;
  copy: string;
  previewLabel: string;
};

const ADJUST_OPTIONS: AdjustOption[] = [
  {
    value: "aumentar",
    label: "Aumentar",
    movementType: "Ajuste entrada",
    copy: "Aumenta existencias por conteo, corrección o entrada manual.",
    previewLabel: "Se aumentará",
  },
  {
    value: "reducir",
    label: "Reducir",
    movementType: "Ajuste salida",
    copy: "Reduce existencias por corrección o salida manual.",
    previewLabel: "Se reducirá",
  },
  {
    value: "merma",
    label: "Merma",
    movementType: "Merma",
    copy: "Registra pérdida, caducidad, derrame o merma.",
    previewLabel: "Se registrará merma de",
  },
];

type Props = {
  item: InventoryItem;
  employeeId: number;
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onSubmit: (payload: InventoryMovementCreateRequest) => void;
};

export function InventoryAdjustmentDialog({
  item,
  employeeId,
  isSaving,
  errorMessage,
  onClose,
  onSubmit,
}: Props) {
  const [adjustType, setAdjustType] = useState<AdjustType>("aumentar");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");

  const parsedQty = Number(quantity);
  const selectedOption = ADJUST_OPTIONS.find((o) => o.value === adjustType)!;

  const qtyValid =
    quantity.trim() !== "" && Number.isFinite(parsedQty) && parsedQty > 0;

  const canSubmit = qtyValid && reason.trim() !== "" && !isSaving;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      employee_id: employeeId,
      inventory_item_id: item.id,
      movement_type: selectedOption.movementType,
      quantity: parsedQty,
      unit_id: item.base_unit_id,
      reason: reason.trim(),
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="adj-dialog-title"
    >
      <form
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]"
        onSubmit={handleSubmit}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] p-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Inventario
            </p>
            <h2 id="adj-dialog-title" className="mt-0.5 text-xl font-black uppercase">
              Ajustar inventario
            </h2>
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={onClose}
            disabled={isSaving}
            className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid gap-4 p-4">
          {/* Item info */}
          <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
            <p className="font-black uppercase">{item.name}</p>
            <p className="text-xs font-bold text-[var(--kp-muted)]">{item.sku}</p>
            <div className="mt-2 flex flex-wrap gap-4 text-sm font-bold">
              <span>
                Stock actual:{" "}
                <strong>
                  {formatInventoryQuantity(item.current_stock)} {item.base_unit_name}
                </strong>
              </span>
              <span className="text-[var(--kp-muted)]">
                Mínimo: {formatInventoryQuantity(item.stock_minimum)} {item.base_unit_name}
              </span>
            </div>
          </div>

          {/* Type selector */}
          <div>
            <p className="mb-2 text-xs font-black uppercase tracking-[0.1em]">
              Tipo de ajuste
            </p>
            <div className="grid grid-cols-3 gap-2">
              {ADJUST_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  disabled={isSaving}
                  onClick={() => setAdjustType(opt.value)}
                  className={[
                    "border-4 border-[var(--kp-ink)] py-2 text-xs font-black uppercase tracking-[0.08em] transition-[transform,box-shadow]",
                    adjustType === opt.value
                      ? "translate-x-[2px] translate-y-[2px] bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)] shadow-none"
                      : "bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none",
                    "disabled:opacity-50",
                  ].join(" ")}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs font-bold text-[var(--kp-muted)]">
              {selectedOption.copy}
            </p>
          </div>

          {/* Quantity */}
          <div>
            <label htmlFor="adj-qty" className="block text-xs font-black uppercase tracking-[0.1em]">
              Cantidad{" "}
              <span className="text-[var(--kp-muted)] normal-case font-bold">
                ({item.base_unit_name})
              </span>
            </label>
            <p className="mb-1 text-xs text-[var(--kp-muted)]">
              Captura en {item.base_unit_name}. Ingresa un número positivo.
            </p>
            <div className="flex gap-2">
              <input
                id="adj-qty"
                type="number"
                step="any"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                disabled={isSaving}
                placeholder="Ej: 5"
                className="flex-1 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
              />
              <span className="flex items-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-sm font-black">
                {item.base_unit_name}
              </span>
            </div>
          </div>

          {/* Preview */}
          {qtyValid && (
            <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-sm font-bold">
              {selectedOption.previewLabel}{" "}
              <strong>
                {formatInventoryQuantity(parsedQty)} {item.base_unit_name}
              </strong>
              .
            </div>
          )}

          {/* Reason */}
          <div>
            <label htmlFor="adj-reason" className="block text-xs font-black uppercase tracking-[0.1em]">
              Motivo{" "}
              <span className="text-[var(--kp-danger)] font-black">*</span>
            </label>
            <input
              id="adj-reason"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isSaving}
              maxLength={200}
              placeholder="Ej. conteo físico, compra menor, derrame, corrección"
              className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
            />
          </div>

          {errorMessage && (
            <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
              No se pudo guardar el ajuste. Revisa cantidad, permiso o motivo.
            </p>
          )}

          <BrutalButton
            type="submit"
            variant="primary"
            fullWidth
            disabled={!canSubmit}
          >
            {isSaving ? "Guardando..." : "Guardar ajuste"}
          </BrutalButton>
        </div>
      </form>
    </div>
  );
}

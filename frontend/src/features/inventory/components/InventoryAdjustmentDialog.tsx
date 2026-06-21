import { useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { InventoryItem, InventoryMovementCreateRequest } from "../types/inventoryTypes";

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
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");

  const parsedQty = Number(quantity);
  const canSubmit =
    quantity.trim() !== "" &&
    !Number.isNaN(parsedQty) &&
    parsedQty !== 0 &&
    reason.trim() !== "" &&
    !isSaving;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      employee_id: employeeId,
      inventory_item_id: item.id,
      movement_type: "Ajuste manual",
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
        className="w-full max-w-md border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
        onSubmit={handleSubmit}
      >
        <header className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Inventario
            </p>
            <h2 id="adj-dialog-title" className="mt-1 text-2xl font-black uppercase">
              Ajustar inventario
            </h2>
            <p className="mt-1 font-bold">{item.name}</p>
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={onClose}
            disabled={isSaving}
            className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50"
          >
            <X className="h-6 w-6" />
          </button>
        </header>

        <p className="mt-2 text-sm font-bold text-[var(--kp-text-muted)]">
          Stock actual: {item.current_stock} {item.base_unit_name}
        </p>

        <div className="mt-4 grid gap-3">
          <div>
            <label htmlFor="adj-qty" className="block text-xs font-black uppercase tracking-[0.1em]">
              Cantidad
            </label>
            <p className="text-xs text-[var(--kp-text-muted)]">
              Negativo para reducir, positivo para aumentar
            </p>
            <input
              id="adj-qty"
              type="number"
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              disabled={isSaving}
              placeholder="Ej: -2 o 5"
              className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
            />
          </div>
          <div>
            <label htmlFor="adj-reason" className="block text-xs font-black uppercase tracking-[0.1em]">
              Motivo
            </label>
            <input
              id="adj-reason"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isSaving}
              maxLength={200}
              placeholder="Ej: Merma, conteo físico"
              className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
            />
          </div>
        </div>

        {errorMessage && (
          <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
            No se pudo ajustar. {errorMessage}
          </p>
        )}

        <BrutalButton
          type="submit"
          variant="primary"
          fullWidth
          disabled={!canSubmit}
          className="mt-4"
        >
          Guardar ajuste
        </BrutalButton>
      </form>
    </div>
  );
}

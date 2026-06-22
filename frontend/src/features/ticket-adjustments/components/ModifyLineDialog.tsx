import { useEffect } from "react";
import { Minus, Plus, X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { VariantGroupSelector } from "../../variants/components/VariantGroupSelector";
import type { VariantGroup } from "../../variants/types/variantTypes";
import { AdjustmentReasonField } from "./AdjustmentReasonField";

type ModifyLineDialogProps = {
  productName: string;
  lineStatus: string;
  note: string;
  quantity: number;
  groups: VariantGroup[];
  variantQuantities: Record<number, number>;
  isSaving: boolean;
  errorMessage: string | null;
  successMessage: string | null;
  onNoteChange: (note: string) => void;
  onQuantityChange: (qty: number) => void;
  onVariantChange: (optionId: number, qty: number) => void;
  onClose: () => void;
  onSubmit: () => void;
  isDirty: boolean;
};

export function ModifyLineDialog({
  productName,
  lineStatus,
  note,
  quantity,
  groups,
  variantQuantities,
  isSaving,
  errorMessage,
  successMessage,
  onNoteChange,
  onQuantityChange,
  onVariantChange,
  onClose,
  onSubmit,
  isDirty,
}: ModifyLineDialogProps) {
  const isCaptured = lineStatus === "Capturado";

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving && !successMessage) onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaving, successMessage, onClose]);

  useEffect(() => {
    if (!successMessage) return;
    const timer = setTimeout(() => onClose(), 2000);
    return () => clearTimeout(timer);
  }, [successMessage, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-2 sm:p-4"
      onClick={() => { if (!isSaving && !successMessage) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modify-line-title"
    >
      <form
        className="flex max-h-[calc(100dvh-1rem)] w-full max-w-xl flex-col overflow-hidden border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)] sm:max-h-[calc(100dvh-2rem)]"
        onSubmit={(event) => { event.preventDefault(); onSubmit(); }}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="z-10 flex shrink-0 items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3">
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Modificación</p>
            <h2 id="modify-line-title" className="text-xl font-black uppercase">Modificar</h2>
            <p className="truncate text-sm font-bold" title={productName}>{productName}</p>
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={onClose}
            disabled={isSaving || !!successMessage}
            className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="min-h-0 overflow-y-auto overscroll-contain p-3">
          {successMessage ? (
            <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 font-black uppercase text-[var(--kp-success-text)]">
              {successMessage}
            </p>
          ) : (
            <>
              <p className={`text-sm font-bold ${isCaptured ? "text-[var(--kp-muted)]" : "text-[var(--kp-warning-text)]"}`}>
                {isCaptured
                  ? "Aún no se envía. Puedes cambiar cantidad y preparación."
                  : "Ya fue enviado. Solo puedes mandar una nota de modificación."}
              </p>

              {isCaptured ? (
                <div className="mt-3 flex items-center justify-between gap-3 border-2 border-[var(--kp-ink)] px-2 py-1.5">
                  <p className="text-xs font-black uppercase text-[var(--kp-muted)]">Cantidad</p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      aria-label="Reducir cantidad"
                      disabled={isSaving || quantity <= 1}
                      onClick={() => onQuantityChange(quantity - 1)}
                      className="flex h-11 w-11 items-center justify-center border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] active:translate-x-[2px] active:translate-y-[2px] disabled:opacity-40"
                    >
                      <Minus className="h-5 w-5" />
                    </button>
                    <span className="min-w-8 text-center text-xl font-black">{quantity}</span>
                    <button
                      type="button"
                      aria-label="Aumentar cantidad"
                      disabled={isSaving}
                      onClick={() => onQuantityChange(quantity + 1)}
                      className="flex h-11 w-11 items-center justify-center border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] active:translate-x-[2px] active:translate-y-[2px] disabled:opacity-40"
                    >
                      <Plus className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ) : null}

              {isCaptured && groups.length > 0 ? (
                <div className="mt-3 grid gap-2">
                  <p className="text-xs font-black uppercase text-[var(--kp-muted)]">Preparación</p>
                  {groups.map((group) => (
                    <VariantGroupSelector
                      key={group.id}
                      group={group}
                      quantities={variantQuantities}
                      disabled={isSaving}
                      onChange={onVariantChange}
                    />
                  ))}
                </div>
              ) : null}

              <div className="mt-3">
                <AdjustmentReasonField
                  label={isCaptured ? "Nota adicional (opcional)" : "Nota (obligatoria)"}
                  value={note}
                  onChange={onNoteChange}
                  disabled={isSaving}
                  optional={isCaptured}
                  compact
                />
              </div>

              {errorMessage ? (
                <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                  {errorMessage}
                </p>
              ) : null}
            </>
          )}
        </div>

        {!successMessage ? (
          <footer className="shrink-0 border-t-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3">
            <BrutalButton type="submit" variant="secondary" fullWidth disabled={isSaving || !isDirty}>
              {isSaving ? "Guardando..." : "Guardar modificación"}
            </BrutalButton>
          </footer>
        ) : null}
      </form>
    </div>
  );
}

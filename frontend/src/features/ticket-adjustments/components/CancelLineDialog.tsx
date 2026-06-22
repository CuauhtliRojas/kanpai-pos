import { useEffect } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { AdjustmentReasonField } from "./AdjustmentReasonField";

type CancelLineDialogProps = {
  productName: string;
  reason: string;
  isSaving: boolean;
  errorMessage: string | null;
  onReasonChange: (reason: string) => void;
  onClose: () => void;
  onSubmit: () => void;
};

export function CancelLineDialog({
  productName,
  reason,
  isSaving,
  errorMessage,
  onReasonChange,
  onClose,
  onSubmit,
}: CancelLineDialogProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving) onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaving, onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" onClick={() => { if (!isSaving) onClose(); }} role="dialog" aria-modal="true" aria-labelledby="cancel-line-title">
      <form
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
        onSubmit={(event) => { event.preventDefault(); onSubmit(); }}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-danger-text)]">Cancelar producto</p>
            <h2 id="cancel-line-title" className="mt-1 text-2xl font-black uppercase">Cancelar</h2>
            <p className="mt-2 font-bold">{productName}</p>
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
        <div className="mt-4">
          <AdjustmentReasonField label="Motivo" value={reason} onChange={onReasonChange} disabled={isSaving} />
        </div>
        {errorMessage ? (
          <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p>
        ) : null}
        <BrutalButton type="submit" variant="danger" fullWidth disabled={isSaving || !reason.trim()} className="mt-4">
          Confirmar cancelación
        </BrutalButton>
      </form>
    </div>
  );
}

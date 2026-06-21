import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { AdjustmentReasonField } from "./AdjustmentReasonField";

type ModifyLineDialogProps = {
  productName: string;
  note: string;
  isSaving: boolean;
  errorMessage: string | null;
  onNoteChange: (note: string) => void;
  onClose: () => void;
  onSubmit: () => void;
};

export function ModifyLineDialog({
  productName,
  note,
  isSaving,
  errorMessage,
  onNoteChange,
  onClose,
  onSubmit,
}: ModifyLineDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="modify-line-title">
      <form
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
        onSubmit={(event) => { event.preventDefault(); onSubmit(); }}
      >
        <header className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Modificación</p>
            <h2 id="modify-line-title" className="mt-1 text-2xl font-black uppercase">Modificar</h2>
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
          <AdjustmentReasonField label="Nota" value={note} onChange={onNoteChange} disabled={isSaving} />
        </div>
        {errorMessage ? (
          <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p>
        ) : null}
        <BrutalButton type="submit" variant="secondary" fullWidth disabled={isSaving || !note.trim()} className="mt-4">
          Guardar modificación
        </BrutalButton>
      </form>
    </div>
  );
}

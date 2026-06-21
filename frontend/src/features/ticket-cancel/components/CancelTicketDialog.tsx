import { useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";

type Props = {
  folio: string;
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onSubmit: (reason: string) => void;
};

export function CancelTicketDialog({ folio, isSaving, errorMessage, onClose, onSubmit }: Props) {
  const [reason, setReason] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!reason.trim() || isSaving) return;
    onSubmit(reason.trim());
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="cancel-ticket-title">
      <form onSubmit={submit} className="w-full max-w-md border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="flex items-start justify-between gap-3">
          <div><p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-danger)]">Acción irreversible</p><h2 id="cancel-ticket-title" className="mt-1 text-2xl font-black uppercase">Cancelar cuenta</h2><p className="mt-1 font-bold">{folio}</p></div>
          <button type="button" aria-label="Cerrar" onClick={onClose} disabled={isSaving} className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)]"><X className="h-6 w-6" /></button>
        </header>
        <p className="mt-3 font-bold">Se cancelarán los productos y pagos activos. La mesa se liberará cuando el servicio confirme la operación.</p>
        <label className="mt-4 grid gap-1 font-black">Motivo<input value={reason} onChange={(event) => setReason(event.target.value)} maxLength={200} disabled={isSaving} className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2" /></label>
        {errorMessage ? <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p> : null}
        <BrutalButton type="submit" variant="danger" fullWidth disabled={!reason.trim() || isSaving} className="mt-4">{isSaving ? "Cancelando..." : "Confirmar cancelación"}</BrutalButton>
      </form>
    </div>
  );
}

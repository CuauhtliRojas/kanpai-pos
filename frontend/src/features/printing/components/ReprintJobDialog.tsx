import { useEffect, useRef, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { PrintJob } from "../types/printingTypes";

function normalizeJobType(jobType: string): string {
  const map: Record<string, string> = {
    ticket: "Ticket",
    comanda: "Comanda",
    corte: "Corte",
  };
  return map[jobType.toLowerCase()] ?? jobType;
}

type Props = {
  job: PrintJob;
  isSubmitting: boolean;
  errorMessage: string | null;
  onSubmit: (reason: string) => Promise<void>;
  onClose: () => void;
};

export function ReprintJobDialog({ job, isSubmitting, errorMessage, onSubmit, onClose }: Props) {
  const [reason, setReason] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !isSubmitting) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isSubmitting, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      role="presentation"
      onClick={(e) => {
        if (!isSubmitting && e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="reprint-dialog-title"
        className="w-full max-w-md border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 shadow-[var(--kp-shadow-hard)]"
      >
        <h2 id="reprint-dialog-title" className="text-2xl font-black uppercase">
          Imprimir otra vez
        </h2>
        <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
          {job.folio} — {normalizeJobType(job.job_type)}
        </p>

        <form
          className="mt-5 grid gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            const clean = reason.trim();
            if (!clean) return;
            void onSubmit(clean).catch(() => undefined);
          }}
        >
          <label className="grid gap-2 text-sm font-black uppercase tracking-[0.08em]">
            Motivo
            <input
              ref={inputRef}
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={200}
              placeholder="Ej. no salio completo, papel atorado, cliente pidio copia"
              disabled={isSubmitting}
              aria-required="true"
              className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-3 text-base font-bold normal-case tracking-normal text-[var(--kp-text)] placeholder:text-[var(--kp-muted)] outline-none focus:border-[var(--kp-info)] disabled:opacity-50"
            />
          </label>

          {errorMessage ? (
            <p
              role="alert"
              className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]"
            >
              {errorMessage}
            </p>
          ) : null}

          <div className="flex gap-3">
            <BrutalButton
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Volver
            </BrutalButton>
            <BrutalButton
              type="submit"
              variant="warning"
              disabled={isSubmitting || !reason.trim()}
              className="flex-1"
            >
              {isSubmitting ? "Enviando..." : "Enviar a impresion"}
            </BrutalButton>
          </div>
        </form>
      </div>
    </div>
  );
}

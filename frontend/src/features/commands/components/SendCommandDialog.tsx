import { useEffect } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";

type SendCommandDialogProps = {
  pendingLineCount: number;
  isSending: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onConfirm: () => void;
};

export function SendCommandDialog({
  pendingLineCount,
  isSending,
  errorMessage,
  onClose,
  onConfirm,
}: SendCommandDialogProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSending) onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSending, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/75 p-4"
      onClick={() => {
        if (!isSending) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="send-command-title"
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Producción</p>
        <h2 id="send-command-title" className="mt-1 text-3xl font-black uppercase">Enviar comanda</h2>
        <p className="mt-4 text-lg font-black">
          Se enviarán {pendingLineCount} productos pendientes a producción.
        </p>
        <p className="mt-2 font-bold text-[var(--kp-muted)]">Revisa la mesa antes de continuar.</p>

        {errorMessage ? (
          <p className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <BrutalButton type="button" size="lg" onClick={onClose} disabled={isSending}>
            Volver
          </BrutalButton>
          <BrutalButton
            type="button"
            variant="warning"
            size="lg"
            onClick={onConfirm}
            disabled={isSending || pendingLineCount === 0}
          >
            {isSending ? "Enviando..." : "Enviar ahora"}
          </BrutalButton>
        </div>
      </section>
    </div>
  );
}

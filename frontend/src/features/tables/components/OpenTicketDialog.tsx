import { useEffect } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { DiningTable } from "../types/tableTypes";

type OpenTicketDialogProps = {
  table: DiningTable;
  isOpening: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onConfirm: () => void;
};

export function OpenTicketDialog({
  table,
  isOpening,
  errorMessage,
  onClose,
  onConfirm,
}: OpenTicketDialogProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isOpening) onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpening, onClose]);

  const tableName = table.display_name || table.table_code || `Mesa ${table.id}`;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
      onClick={() => {
        if (!isOpening) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="open-ticket-title"
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Venta</p>
        <h2 id="open-ticket-title" className="mt-1 text-3xl font-black uppercase">Abrir cuenta</h2>
        <p className="mt-4 text-lg font-bold">Se abrirá una cuenta para {tableName}.</p>

        {errorMessage ? (
          <p className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <BrutalButton type="button" size="lg" onClick={onClose} disabled={isOpening}>
            Volver
          </BrutalButton>
          <BrutalButton type="button" variant="success" size="lg" onClick={onConfirm} disabled={isOpening}>
            {isOpening ? "Abriendo cuenta..." : "Abrir cuenta"}
          </BrutalButton>
        </div>
      </section>
    </div>
  );
}

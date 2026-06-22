import { useEffect } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketLine } from "../../tickets/types/ticketTypes";

type TicketLineActionsDialogProps = {
  line: TicketLine;
  canModify: boolean;
  canCancel: boolean;
  requiresAuthorization: boolean;
  onClose: () => void;
  onModify: () => void;
  onCancel: () => void;
};

function getLineStatusLabel(status: string): string {
  if (status === "Capturado") return "Pendiente de enviar";
  if (status === "Cancelado") return "Cancelado";
  return "Enviado";
}

export function TicketLineActionsDialog({
  line,
  canModify,
  canCancel,
  requiresAuthorization,
  onClose,
  onModify,
  onCancel,
}: TicketLineActionsDialogProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/75 p-4" onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-line-actions-title"
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Producto de la cuenta</p>
        <h2 id="ticket-line-actions-title" className="mt-1 text-2xl font-black uppercase">
          {line.product_name_snapshot}
        </h2>

        <dl className="mt-4 grid grid-cols-2 gap-3 border-y-4 border-[var(--kp-ink)] py-4">
          <div><dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Cantidad</dt><dd className="mt-1 font-black">{line.quantity}</dd></div>
          <div><dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Estado</dt><dd className="mt-1 font-black">{getLineStatusLabel(line.status)}</dd></div>
          <div><dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Precio unitario</dt><dd className="mt-1 font-black">{formatCentsToPesos(line.unit_price_cents)}</dd></div>
          <div><dt className="text-xs font-black uppercase text-[var(--kp-muted)]">Total</dt><dd className="mt-1 text-xl font-black">{formatCentsToPesos(line.line_total_cents)}</dd></div>
        </dl>

        {line.note ? (
          <p className="mt-4 border-l-4 border-[var(--kp-selected)] pl-3 font-bold">Nota: {line.note}</p>
        ) : null}
        {requiresAuthorization ? (
          <p className="mt-4 font-bold text-[var(--kp-warning-text)]">Pide autorización al encargado para cancelar.</p>
        ) : null}

        <div className="mt-5 grid gap-3">
          {canModify ? (
            <BrutalButton type="button" variant="warning" size="lg" fullWidth onClick={onModify}>
              Modificar
            </BrutalButton>
          ) : null}
          {canCancel ? (
            <BrutalButton type="button" variant="danger" size="lg" fullWidth onClick={onCancel}>
              Cancelar producto
            </BrutalButton>
          ) : null}
          <BrutalButton type="button" size="lg" fullWidth onClick={onClose}>Volver</BrutalButton>
        </div>
      </section>
    </div>
  );
}

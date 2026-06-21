import { useEffect, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useSendTicketRoundMutation } from "../hooks/useSendTicketRoundMutation";

type SendCommandPanelProps = {
  ticketId: number | null;
  employeeId: number | null;
  pendingLineCount: number;
  isLoadingLines: boolean;
};

export function SendCommandPanel({
  ticketId,
  employeeId,
  pendingLineCount,
  isLoadingLines,
}: SendCommandPanelProps) {
  const [isConfirming, setIsConfirming] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const sendMutation = useSendTicketRoundMutation();
  const canSend =
    ticketId !== null &&
    employeeId !== null &&
    pendingLineCount > 0 &&
    !isLoadingLines &&
    !sendMutation.isPending;

  useEffect(() => {
    setIsConfirming(false);
    setMessage(null);
  }, [ticketId]);

  async function handleConfirm() {
    if (ticketId === null || employeeId === null || pendingLineCount === 0) return;

    setMessage(null);
    try {
      await sendMutation.mutateAsync({
        ticketId,
        payload: { employee_id: employeeId },
      });
      setIsConfirming(false);
      setMessage("Comanda enviada.");
    } catch {
      setMessage("No se pudo enviar la comanda.");
    }
  }

  const guidance =
    ticketId === null
      ? "Primero abre una cuenta."
      : !isLoadingLines &&
          pendingLineCount === 0 &&
          message !== "Comanda enviada."
        ? "Agrega productos antes de enviar."
        : null;
  const visibleMessage =
    message === "Comanda enviada." && pendingLineCount > 0 ? null : message;

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">
        Productos pendientes
      </p>
      <p className="mt-1 text-2xl font-black">{pendingLineCount}</p>

      {guidance ? <p className="mt-3 font-bold text-[var(--kp-muted)]">{guidance}</p> : null}
      {visibleMessage ? <p className="mt-3 font-black">{visibleMessage}</p> : null}

      {isConfirming ? (
        <div className="mt-4 grid gap-2">
          <p className="font-black">¿Confirmar envío?</p>
          <BrutalButton
            type="button"
            variant="warning"
            size="lg"
            fullWidth
            disabled={!canSend}
            onClick={() => void handleConfirm()}
          >
            {sendMutation.isPending ? "Enviando..." : "Confirmar envío"}
          </BrutalButton>
          <BrutalButton
            type="button"
            variant="ghost"
            disabled={sendMutation.isPending}
            onClick={() => setIsConfirming(false)}
          >
            Volver
          </BrutalButton>
        </div>
      ) : (
        <BrutalButton
          type="button"
          variant="warning"
          size="lg"
          fullWidth
          disabled={!canSend}
          onClick={() => {
            setMessage(null);
            setIsConfirming(true);
          }}
          className="mt-4"
        >
          Enviar comanda
        </BrutalButton>
      )}
    </section>
  );
}

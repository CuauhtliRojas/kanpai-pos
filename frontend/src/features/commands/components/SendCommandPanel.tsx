import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useSendTicketRoundMutation } from "../hooks/useSendTicketRoundMutation";
import { SendCommandDialog } from "./SendCommandDialog";

type SendCommandPanelProps = {
  ticketId: number | null;
  employeeId: number | null;
  pendingLineCount: number;
  isLoadingLines: boolean;
};

function getSendErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail =
      typeof error.details === "object" &&
      error.details !== null &&
      "detail" in error.details &&
      typeof error.details.detail === "string"
        ? error.details.detail
        : null;

    if (detail?.includes("No hay líneas capturadas")) {
      return "No hay productos pendientes por enviar.";
    }
    if (detail?.includes("no admite el envío")) {
      return "La cuenta cambió. Revisa el pedido e intenta de nuevo.";
    }
    if (detail?.includes("estación") || detail?.includes("impresora")) {
      return detail;
    }
    if (error.status === 409) {
      return "La cuenta cambió. Revisa el pedido e intenta de nuevo.";
    }
  }
  return "No se pudo enviar la comanda. Intenta de nuevo.";
}

export function SendCommandPanel({
  ticketId,
  employeeId,
  pendingLineCount,
  isLoadingLines,
}: SendCommandPanelProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const submitLockRef = useRef(false);
  const sendMutation = useSendTicketRoundMutation();
  const canSend =
    ticketId !== null &&
    employeeId !== null &&
    pendingLineCount > 0 &&
    !isLoadingLines &&
    !sendMutation.isPending;

  useEffect(() => {
    setIsDialogOpen(false);
    setMessage(null);
    setErrorMessage(null);
  }, [ticketId]);

  async function handleConfirm() {
    if (!canSend || ticketId === null || employeeId === null || submitLockRef.current) return;

    submitLockRef.current = true;
    setErrorMessage(null);
    try {
      await sendMutation.mutateAsync({
        ticketId,
        payload: { employee_id: employeeId },
      });
      setIsDialogOpen(false);
      setMessage("Comanda enviada.");
    } catch (error) {
      setErrorMessage(getSendErrorMessage(error));
    } finally {
      submitLockRef.current = false;
    }
  }

  const guidance = isLoadingLines
    ? "Revisando pedido..."
    : ticketId === null
      ? "Primero abre una cuenta."
      : pendingLineCount === 0 && message !== "Comanda enviada."
        ? "No hay productos pendientes por enviar."
        : null;

  return (
    <>
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">
          Productos pendientes
        </p>
        <p className="mt-1 text-2xl font-black">{pendingLineCount}</p>

        {guidance ? <p className="mt-3 font-bold text-[var(--kp-muted)]">{guidance}</p> : null}
        {message ? <p className="mt-3 font-black">{message}</p> : null}

        <BrutalButton
          type="button"
          variant="warning"
          size="lg"
          fullWidth
          disabled={!canSend}
          onClick={() => {
            setMessage(null);
            setErrorMessage(null);
            setIsDialogOpen(true);
          }}
          className="mt-4"
        >
          Enviar comanda
        </BrutalButton>
      </section>

      {isDialogOpen ? (
        <SendCommandDialog
          pendingLineCount={pendingLineCount}
          isSending={sendMutation.isPending}
          errorMessage={errorMessage}
          onClose={() => {
            if (sendMutation.isPending) return;
            setErrorMessage(null);
            setIsDialogOpen(false);
          }}
          onConfirm={() => void handleConfirm()}
        />
      ) : null}
    </>
  );
}

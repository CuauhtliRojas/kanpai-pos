import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { DiscountPanel } from "../../discounts/components/DiscountPanel";
import { PaymentForm } from "../../payments/components/PaymentForm";
import { PaymentList } from "../../payments/components/PaymentList";
import { usePaymentMethodsQuery } from "../../payments/hooks/usePaymentMethodsQuery";
import { usePaymentsQuery } from "../../payments/hooks/usePaymentsQuery";
import type { Ticket } from "../../tables/types/tableTypes";
import { CancelTicketAction } from "../../ticket-cancel/components/CancelTicketAction";
import { TicketSplitPanel } from "../../ticket-split/components/TicketSplitPanel";
import { useTicketSplitsQuery } from "../../ticket-split/hooks/useTicketSplitsQuery";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { useStartCheckoutMutation } from "../hooks/useStartCheckoutMutation";
import { CheckoutSummary } from "./CheckoutSummary";

type AccountCheckoutDialogProps = {
  ticket: Ticket;
  lineCount: number;
  lines: TicketLine[];
  pendingLineCount: number;
  employeeId: number | null;
  canAuthorizeDiscount: boolean;
  canCancelTicket: boolean;
  onClose: () => void;
  onClosed: () => void;
  onCancelled: () => void;
};

function getCheckoutErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail =
      typeof error.details === "object" &&
      error.details !== null &&
      "detail" in error.details &&
      typeof error.details.detail === "string"
        ? error.details.detail
        : null;
    if (detail?.includes("líneas capturadas pendientes")) {
      return "Envía los productos pendientes antes de cobrar.";
    }
    if (detail?.includes("no puede iniciar cobro")) {
      return "Esta cuenta ya no puede cambiar a cobro.";
    }
  }
  return "Revisa la cuenta e intenta de nuevo.";
}

export function AccountCheckoutDialog({
  ticket,
  lineCount,
  lines,
  pendingLineCount,
  employeeId,
  canAuthorizeDiscount,
  canCancelTicket,
  onClose,
  onClosed,
  onCancelled,
}: AccountCheckoutDialogProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const submitLockRef = useRef(false);
  const startMutation = useStartCheckoutMutation();
  const isInPayment = ticket.status === "En cobro";
  const paymentsQuery = usePaymentsQuery(isInPayment ? ticket.id : null);
  const methodsQuery = usePaymentMethodsQuery(isInPayment);
  const splitsQuery = useTicketSplitsQuery(ticket.id);
  const activeSplits = (splitsQuery.data ?? []).filter(
    (split) => split.status !== "Cancelada",
  );
  const blockingMessage =
    pendingLineCount > 0
      ? "Envía la comanda pendiente antes de cobrar."
      : ticket.total_cents <= 0
        ? "La cuenta debe tener un total mayor a cero."
        : lineCount === 0
          ? "Agrega productos antes de cobrar."
          : null;
  const canStart =
    ticket.status === "Abierto" &&
    blockingMessage === null &&
    employeeId !== null &&
    !startMutation.isPending;

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !startMutation.isPending) onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, startMutation.isPending]);

  async function handleStart() {
    if (!canStart || employeeId === null || submitLockRef.current) return;
    submitLockRef.current = true;
    setErrorMessage(null);
    try {
      await startMutation.mutateAsync({
        ticketId: ticket.id,
        payload: { employee_id: employeeId },
      });
    } catch (error) {
      setErrorMessage(getCheckoutErrorMessage(error));
    } finally {
      submitLockRef.current = false;
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 grid place-items-center bg-black/75 p-2"
      onClick={() => {
        if (!startMutation.isPending) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-checkout-title"
        className="flex max-h-[calc(100vh-8rem)] w-[min(90vw,38rem)] flex-col border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex flex-wrap items-start justify-between gap-2 border-b-4 border-[var(--kp-ink)] p-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Cuenta</p>
            <h2 id="account-checkout-title" className="mt-1 text-2xl font-black uppercase">
              {isInPayment ? "Cobro" : "Cuenta"}
            </h2>
            <p className="mt-1 font-bold text-[var(--kp-muted)]">{ticket.folio}</p>
          </div>
          <BrutalButton type="button" size="md" onClick={onClose} disabled={startMutation.isPending}>
            Volver
          </BrutalButton>
        </header>

        <div className="min-h-0 overflow-y-auto p-3">
          <CheckoutSummary ticket={ticket} lineCount={lineCount} />

          {!isInPayment ? (
            <div className="mt-3 grid gap-2">
              <p className="font-bold">Se pausará la captura para cobrar esta cuenta.</p>
              {blockingMessage ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] p-3 font-bold text-[var(--kp-text)]">
                  {blockingMessage}
                </p>
              ) : null}
              {errorMessage ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                  {errorMessage}
                </p>
              ) : null}
              <DiscountPanel ticket={ticket} employeeId={employeeId} canAuthorize={canAuthorizeDiscount} />
              <BrutalButton type="button" variant="success" size="lg" fullWidth disabled={!canStart} onClick={() => void handleStart()}>
                {startMutation.isPending ? "Iniciando..." : "Iniciar cobro"}
              </BrutalButton>
            </div>
          ) : (
            <div className="mt-3 grid gap-3">
              <DiscountPanel ticket={ticket} employeeId={employeeId} canAuthorize={canAuthorizeDiscount} />
              <section className="border-t-2 border-[var(--kp-ink)] pt-3">
                <h3 className="text-lg font-black uppercase">Pagos registrados</h3>
                {paymentsQuery.isPending || methodsQuery.isPending ? (
                  <p className="mt-3 font-bold">Consultando pagos...</p>
                ) : paymentsQuery.isError || methodsQuery.isError ? (
                  <p className="mt-3 font-bold">No se pudieron cargar los pagos.</p>
                ) : paymentsQuery.data && methodsQuery.data ? (
                  <div className="mt-2 grid gap-3">
                    <PaymentList summary={paymentsQuery.data} methods={methodsQuery.data} />
                    {activeSplits.length === 0 ? (
                      <div>
                        <h3 className="mb-2 text-lg font-black uppercase">Registrar pago</h3>
                        <PaymentForm
                          ticket={ticket}
                          employeeId={employeeId}
                          remainingCents={paymentsQuery.data.remaining_cents}
                          methods={methodsQuery.data}
                          onClosed={onClosed}
                        />
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </section>
            </div>
          )}

          <div className="mt-3 grid gap-2 border-t-2 border-[var(--kp-ink)] pt-3">
            <CancelTicketAction ticket={ticket} employeeId={employeeId} canCancel={canCancelTicket} onCancelled={onCancelled} />
            {!splitsQuery.isPending && !splitsQuery.isError ? (
              <TicketSplitPanel
                ticket={ticket}
                lines={lines}
                splits={splitsQuery.data ?? []}
                employeeId={employeeId}
                methods={methodsQuery.data ?? []}
                onClosed={onClosed}
              />
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

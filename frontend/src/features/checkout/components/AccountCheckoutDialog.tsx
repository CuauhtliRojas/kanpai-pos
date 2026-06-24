import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos } from "../../../shared/lib/money";
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
import { CheckoutSection } from "./CheckoutSection";
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
  const paymentSummary = paymentsQuery.data;
  const blockingMessage =
    pendingLineCount > 0
      ? "Envía la comanda pendiente antes de cobrar."
      : ticket.total_cents < 0
        ? "La cuenta puede cerrarse en $0.00 si tiene cortesía autorizada."
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
      className="fixed inset-0 z-40 grid place-items-center bg-black/75 p-2 sm:p-4"
      onClick={() => {
        if (!startMutation.isPending) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-checkout-title"
        className="flex max-h-[calc(100dvh-1rem)] w-full max-w-[38rem] flex-col overflow-hidden border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)] sm:max-h-[calc(100dvh-2rem)]"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex shrink-0 items-center justify-between gap-2 border-b-4 border-[var(--kp-ink)] p-2 sm:p-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Cuenta</p>
            <h2 id="account-checkout-title" className="text-xl font-black uppercase sm:text-2xl">
              {isInPayment ? "Cobro" : "Cuenta"} · {ticket.folio}
            </h2>
          </div>
          <BrutalButton type="button" size="sm" onClick={onClose} disabled={startMutation.isPending}>
            Volver
          </BrutalButton>
        </header>

        <div className="min-h-0 overflow-y-auto overscroll-contain p-2 sm:p-3">
          <div className="grid gap-2">
            <CheckoutSection
              title="Resumen"
              defaultOpen
              summary={`Saldo ${formatCentsToPesos(paymentSummary?.remaining_cents ?? ticket.total_cents)}`}
            >
              <CheckoutSummary ticket={ticket} lineCount={lineCount} remainingCents={paymentSummary?.remaining_cents} embedded />
            </CheckoutSection>

            {pendingLineCount > 0 ? (
              <CheckoutSection title="Productos pendientes" defaultOpen tone="warning" summary={`${pendingLineCount} por enviar`}>
                <p className="font-black">Envía estos productos antes de cobrar.</p>
                <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">Productos pendientes: {pendingLineCount}</p>
              </CheckoutSection>
            ) : null}

            <CheckoutSection title="Comandas / estado de cuenta" summary={ticket.status}>
              <div className="grid gap-1 font-bold">
                <div className="flex justify-between gap-3"><span>Estado</span><span>{ticket.status}</span></div>
                <div className="flex justify-between gap-3"><span>Productos</span><span>{lineCount}</span></div>
                <div className="flex justify-between gap-3"><span>Pendientes de envío</span><span>{pendingLineCount}</span></div>
              </div>
            </CheckoutSection>

            <section className="grid gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-2">
              <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">Acciones de cuenta</p>
              <div className={`grid gap-2 ${!isInPayment ? "grid-cols-2" : "grid-cols-1"}`}>
                {!isInPayment ? (
                  <DiscountPanel ticket={ticket} employeeId={employeeId} canAuthorize={canAuthorizeDiscount} actionOnly />
                ) : null}
                {!splitsQuery.isPending && !splitsQuery.isError ? (
                  <TicketSplitPanel
                    ticket={ticket}
                    lines={lines}
                    splits={splitsQuery.data ?? []}
                    employeeId={employeeId}
                    methods={methodsQuery.data ?? []}
                    onClosed={onClosed}
                    actionOnly
                  />
                ) : (
                  <BrutalButton type="button" fullWidth disabled>Dividir cuenta</BrutalButton>
                )}
              </div>
              {!isInPayment ? (
                <>
                  {blockingMessage ? (
                    <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] p-2 font-bold">{blockingMessage}</p>
                  ) : null}
                  {errorMessage ? (
                    <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-2 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p>
                  ) : null}
                  <BrutalButton type="button" variant="success" size="lg" fullWidth disabled={!canStart} onClick={() => void handleStart()}>
                    {startMutation.isPending ? "Iniciando..." : "Iniciar cobro"}
                  </BrutalButton>
                </>
              ) : null}
            </section>

            {isInPayment ? (
              <CheckoutSection
                title="Pagos registrados"
                defaultOpen
                summary={paymentSummary ? `${paymentSummary.payments.length} pagos` : "Consultando"}
              >
                {paymentsQuery.isPending || methodsQuery.isPending ? (
                  <p className="font-bold">Consultando pagos...</p>
                ) : paymentsQuery.isError || methodsQuery.isError ? (
                  <p className="font-bold">No se pudieron cargar los pagos.</p>
                ) : paymentsQuery.data && methodsQuery.data ? (
                  <div className="grid gap-3">
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
                    ) : (
                      <p className="text-sm font-bold text-[var(--kp-muted)]">Registra los pagos dentro de cada parte de la división.</p>
                    )}
                  </div>
                ) : null}
              </CheckoutSection>
            ) : null}

            {!splitsQuery.isPending && !splitsQuery.isError ? (
              <CheckoutSection
                title="División de cuenta"
                defaultOpen={activeSplits.length > 0}
                summary={activeSplits.length > 0 ? `${activeSplits.length} partes activas` : "Sin división activa"}
              >
                <TicketSplitPanel
                  ticket={ticket}
                  lines={lines}
                splits={splitsQuery.data ?? []}
                employeeId={employeeId}
                  methods={methodsQuery.data ?? []}
                  onClosed={onClosed}
                  hideDivideAction
                />
              </CheckoutSection>
            ) : null}

            {canCancelTicket ? (
              <CheckoutSection title="Zona de cancelación" tone="danger" summary="Acción irreversible">
                <p className="mb-3 text-sm font-bold">Cancela toda la cuenta únicamente cuando sea necesario.</p>
                <CancelTicketAction ticket={ticket} employeeId={employeeId} canCancel={canCancelTicket} onCancelled={onCancelled} />
              </CheckoutSection>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

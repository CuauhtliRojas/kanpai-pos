import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { DiscountPanel } from "../../discounts/components/DiscountPanel";
import type { Ticket } from "../../tables/types/tableTypes";
import { PaymentForm } from "../../payments/components/PaymentForm";
import { PaymentList } from "../../payments/components/PaymentList";
import { usePaymentMethodsQuery } from "../../payments/hooks/usePaymentMethodsQuery";
import { usePaymentsQuery } from "../../payments/hooks/usePaymentsQuery";
import { useStartCheckoutMutation } from "../hooks/useStartCheckoutMutation";
import { CheckoutSummary } from "./CheckoutSummary";
import { CancelTicketAction } from "../../ticket-cancel/components/CancelTicketAction";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { TicketSplitPanel } from "../../ticket-split/components/TicketSplitPanel";
import { useTicketSplitsQuery } from "../../ticket-split/hooks/useTicketSplitsQuery";

type CheckoutPanelProps = {
  hasSelectedTable: boolean;
  ticket: Ticket | null;
  lineCount: number;
  lines: TicketLine[];
  pendingLineCount: number;
  employeeId: number | null;
  notice: string | null;
  onClosed: () => void;
  canAuthorizeDiscount: boolean;
  canCancelTicket: boolean;
  onCancelled: () => void;
};

export function CheckoutPanel({
  hasSelectedTable,
  ticket,
  lineCount,
  lines,
  pendingLineCount,
  employeeId,
  notice,
  onClosed,
  canAuthorizeDiscount,
  canCancelTicket,
  onCancelled,
}: CheckoutPanelProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const startMutation = useStartCheckoutMutation();
  const isInPayment = ticket?.status === "En cobro";
  const paymentsQuery = usePaymentsQuery(isInPayment ? ticket.id : null);
  const methodsQuery = usePaymentMethodsQuery(isInPayment);
  const splitsQuery = useTicketSplitsQuery(ticket?.id ?? null);
  const activeSplits = (splitsQuery.data ?? []).filter((split) => split.status !== "Cancelada");

  const guidance = notice
    ? null
    : !hasSelectedTable
      ? "Primero elige una mesa."
      : !ticket
      ? "Abre una cuenta para esta mesa."
      : lineCount === 0
        ? "Agrega productos antes de cobrar."
        : pendingLineCount > 0
          ? "Productos pendientes de enviar."
          : null;
  const canStart =
    ticket !== null &&
    ticket.status === "Abierto" &&
    lineCount > 0 &&
    pendingLineCount === 0 &&
    employeeId !== null &&
    !startMutation.isPending;

  async function handleStart() {
    if (!canStart || !ticket || employeeId === null) return;
    setErrorMessage(null);
    try {
      await startMutation.mutateAsync({
        ticketId: ticket.id,
        payload: { employee_id: employeeId },
      });
    } catch {
      setErrorMessage("No se pudo iniciar el cobro.");
    }
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
        Cuenta
      </p>
      <h2 className="mt-1 text-xl font-black uppercase">
        {notice ? "Cuenta cerrada" : isInPayment ? "Pago" : ticket ? "Cuenta activa" : "Cuenta"}
      </h2>

      {ticket ? <CheckoutSummary ticket={ticket} lineCount={lineCount} /> : null}
      {ticket ? (
        <DiscountPanel
          ticket={ticket}
          employeeId={employeeId}
          canAuthorize={canAuthorizeDiscount}
        />
      ) : null}
      {ticket ? <CancelTicketAction ticket={ticket} employeeId={employeeId} canCancel={canCancelTicket} onCancelled={onCancelled} /> : null}
      {ticket && !splitsQuery.isPending && !splitsQuery.isError ? <TicketSplitPanel ticket={ticket} lines={lines} splits={splitsQuery.data ?? []} employeeId={employeeId} methods={methodsQuery.data ?? []} onClosed={onClosed} /> : null}
      {notice ? <p className="mt-3 font-black text-emerald-400">{notice}</p> : null}
      {guidance ? <p className="mt-3 font-bold text-[var(--kp-muted)]">{guidance}</p> : null}
      {errorMessage ? <p className="mt-3 font-black">{errorMessage}</p> : null}

      {isInPayment && ticket ? (
        paymentsQuery.isPending || methodsQuery.isPending ? (
          <p className="mt-3 font-bold">Consultando pagos...</p>
        ) : paymentsQuery.isError || methodsQuery.isError ? (
          <p className="mt-3 font-bold">No se pudieron cargar los pagos.</p>
        ) : paymentsQuery.data && methodsQuery.data ? (
          <div className="mt-4 grid gap-4">
            <PaymentList
              summary={paymentsQuery.data}
              methods={methodsQuery.data}
            />
            {activeSplits.length === 0 ? <PaymentForm ticket={ticket} employeeId={employeeId} remainingCents={paymentsQuery.data.remaining_cents} methods={methodsQuery.data} onClosed={onClosed} /> : null}
          </div>
        ) : null
      ) : (
        <BrutalButton
          type="button"
          variant="primary"
          size="lg"
          fullWidth
          disabled={!canStart}
          onClick={() => void handleStart()}
          className="mt-4"
        >
          {startMutation.isPending ? "Abriendo cobro..." : "Cobrar"}
        </BrutalButton>
      )}
    </section>
  );
}

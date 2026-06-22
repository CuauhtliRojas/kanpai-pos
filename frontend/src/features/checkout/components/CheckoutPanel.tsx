import { useEffect, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { Ticket } from "../../tables/types/tableTypes";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { AccountCheckoutDialog } from "./AccountCheckoutDialog";
import { CheckoutSummary } from "./CheckoutSummary";

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
  const [dialogOpen, setDialogOpen] = useState(false);
  const isInPayment = ticket?.status === "En cobro";
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

  useEffect(() => {
    setDialogOpen(false);
  }, [ticket?.id]);

  return (
    <>
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Cuenta</p>
        <h2 className="mt-1 text-xl font-black uppercase">
          {notice ? "Cuenta cerrada" : isInPayment ? "Cobro" : ticket ? "Cuenta activa" : "Cuenta"}
        </h2>
        {ticket ? <CheckoutSummary ticket={ticket} lineCount={lineCount} /> : null}
        {notice ? <p className="mt-3 font-black text-[var(--kp-success-text)]">{notice}</p> : null}
        {guidance ? <p className="mt-3 font-bold text-[var(--kp-muted)]">{guidance}</p> : null}
        <BrutalButton
          type="button"
          variant="primary"
          size="lg"
          fullWidth
          disabled={ticket === null || lineCount === 0 || employeeId === null}
          onClick={() => setDialogOpen(true)}
          className="mt-4"
        >
          {isInPayment ? "Administrar cobro" : "Cobrar"}
        </BrutalButton>
      </section>

      {dialogOpen && ticket ? (
        <AccountCheckoutDialog
          ticket={ticket}
          lineCount={lineCount}
          lines={lines}
          pendingLineCount={pendingLineCount}
          employeeId={employeeId}
          canAuthorizeDiscount={canAuthorizeDiscount}
          canCancelTicket={canCancelTicket}
          onClose={() => setDialogOpen(false)}
          onClosed={onClosed}
          onCancelled={onCancelled}
        />
      ) : null}
    </>
  );
}

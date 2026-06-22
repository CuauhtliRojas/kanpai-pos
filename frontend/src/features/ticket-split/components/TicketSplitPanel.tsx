import { useMemo, useState } from "react";
import { ApiError } from "../../../api/http";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { PaymentMethod } from "../../payments/types/paymentTypes";
import type { Ticket } from "../../tables/types/tableTypes";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { useCancelTicketSplitsMutation, useCreateEqualSplitsMutation, useCreateLinesSplitMutation } from "../hooks/useTicketSplitMutations";
import type { TicketSplit } from "../types/ticketSplitTypes";
import { SplitPaymentForm } from "./SplitPaymentForm";
import { SplitTicketDialog } from "./SplitTicketDialog";

type Props = {
  ticket: Ticket;
  lines: TicketLine[];
  splits: TicketSplit[];
  employeeId: number | null;
  methods: PaymentMethod[];
  onClosed: () => void;
  actionOnly?: boolean;
  hideDivideAction?: boolean;
};

function getRebuildError(error: unknown): string {
  if (error instanceof ApiError) {
    const detail =
      typeof error.details === "object" &&
      error.details !== null &&
      "detail" in error.details &&
      typeof error.details.detail === "string"
        ? error.details.detail
        : null;
    if (detail?.toLowerCase().includes("pago")) {
      return "Esta división ya tiene pagos. Termina el cobro o pide ayuda.";
    }
  }
  return "No se pudo rehacer la división. Revisa su estado e intenta de nuevo.";
}

export function TicketSplitPanel({
  ticket,
  lines,
  splits,
  employeeId,
  methods,
  onClosed,
  actionOnly = false,
  hideDivideAction = false,
}: Props) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const equalMutation = useCreateEqualSplitsMutation();
  const linesMutation = useCreateLinesSplitMutation();
  const cancelMutation = useCancelTicketSplitsMutation();

  const activeSplits = splits.filter((split) => split.status !== "Cancelada");
  const canAddSplit = activeSplits.length === 0 || activeSplits.every((split) => split.split_type === "Por lineas");
  const usedIds = useMemo(
    () => new Set(activeSplits.flatMap((split) => split.lines.map((line) => line.ticket_line_id))),
    [activeSplits],
  );

  const splitError = equalMutation.isError || linesMutation.isError
    ? "No se pudo dividir la cuenta. Revisa la selección e intenta de nuevo."
    : null;

  const ticketActive = ticket.status !== "Cobrado" && ticket.status !== "Cancelado";

  function handleRehacer() {
    setCancelError(null);
    setConfirmCancel(true);
  }

  function handleCancelSplits() {
    if (employeeId === null) return;
    void cancelMutation
      .mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId } })
      .then(() => {
        setConfirmCancel(false);
        setCancelError(null);
      })
      .catch((error: unknown) => {
        setCancelError(getRebuildError(error));
      });
  }

  const splitDialog = dialogOpen && employeeId !== null ? (
    <SplitTicketDialog
      lines={lines}
      usedIds={usedIds}
      allowEqual={activeSplits.length === 0}
      isSaving={equalMutation.isPending || linesMutation.isPending}
      errorMessage={splitError}
      onClose={() => {
        equalMutation.reset();
        linesMutation.reset();
        setDialogOpen(false);
      }}
      onEqual={(parts) =>
        void equalMutation
          .mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId, parts } })
          .then(() => setDialogOpen(false))
          .catch(() => undefined)
      }
      onLines={(name, ticketLineIds) =>
        void linesMutation
          .mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId, name, ticket_line_ids: ticketLineIds } })
          .then(() => setDialogOpen(false))
          .catch(() => undefined)
      }
    />
  ) : null;

  if (actionOnly) {
    return (
      <div className="min-w-0">
        <BrutalButton
          type="button"
          size="md"
          fullWidth
          disabled={employeeId === null || !canAddSplit || !ticketActive}
          onClick={() => setDialogOpen(true)}
        >
          Dividir cuenta
        </BrutalButton>
        {splitDialog}
      </div>
    );
  }

  return (
    <section>
      <div className="flex items-center justify-between gap-2">
        <p className="font-black uppercase">Cuenta dividida</p>
        <div className="flex gap-2">
          {employeeId !== null && activeSplits.length > 0 && ticketActive ? (
            <BrutalButton type="button" size="sm" variant="warning" onClick={handleRehacer}>
              Rehacer división
            </BrutalButton>
          ) : null}
          {!hideDivideAction && employeeId !== null && canAddSplit && ticketActive ? (
            <BrutalButton type="button" size="sm" onClick={() => setDialogOpen(true)}>
              {activeSplits.length ? "Agregar persona" : "Dividir"}
            </BrutalButton>
          ) : null}
        </div>
      </div>

      {activeSplits.length === 0 ? (
        <p className="mt-2 text-sm font-bold text-[var(--kp-muted)]">
          Puedes separar por personas o por productos.
        </p>
      ) : (
        <div className="mt-3 grid gap-3">
          {activeSplits.map((split) => (
            <article key={split.id} className="border-2 border-[var(--kp-ink)] p-3">
              <div className="flex justify-between gap-3">
                <div>
                  <p className="font-black">{split.name}</p>
                  <p className="text-sm font-bold text-[var(--kp-muted)]">{split.status}</p>
                </div>
                <p className="font-black">{formatCentsToPesos(split.amount_cents)}</p>
              </div>
              {split.status === "Abierta" && ticket.status === "En cobro" && employeeId !== null ? (
                <SplitPaymentForm
                  split={split}
                  ticketId={ticket.id}
                  cashShiftId={ticket.cash_shift_id}
                  employeeId={employeeId}
                  methods={methods}
                  onClosed={onClosed}
                />
              ) : null}
            </article>
          ))}
        </div>
      )}

      {confirmCancel ? (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="rebuild-split-title">
          <div className="w-full max-w-md border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">División de cuenta</p>
            <h2 id="rebuild-split-title" className="mt-1 text-2xl font-black uppercase">Rehacer división</h2>
            <p className="mt-3 font-bold">Se cancelarán las partes actuales y podrás dividir de nuevo.</p>
            {cancelError ? (
              <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                {cancelError}
              </p>
            ) : null}
            <div className="mt-4 grid grid-cols-2 gap-2">
              <BrutalButton type="button" disabled={cancelMutation.isPending} onClick={() => { setConfirmCancel(false); setCancelError(null); }}>
                Volver
              </BrutalButton>
              <BrutalButton type="button" variant="danger" disabled={cancelMutation.isPending} onClick={handleCancelSplits}>
                {cancelMutation.isPending ? "Rehaciendo..." : "Rehacer"}
              </BrutalButton>
            </div>
          </div>
        </div>
      ) : null}

      {splitDialog}
    </section>
  );
}

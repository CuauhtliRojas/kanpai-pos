import { useMemo, useState } from "react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { PaymentMethod } from "../../payments/types/paymentTypes";
import type { Ticket } from "../../tables/types/tableTypes";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { useCreateEqualSplitsMutation, useCreateLinesSplitMutation } from "../hooks/useTicketSplitMutations";
import type { TicketSplit } from "../types/ticketSplitTypes";
import { SplitPaymentForm } from "./SplitPaymentForm";
import { SplitTicketDialog } from "./SplitTicketDialog";

type Props = { ticket: Ticket; lines: TicketLine[]; splits: TicketSplit[]; employeeId: number | null; methods: PaymentMethod[]; onClosed: () => void };
export function TicketSplitPanel({ ticket, lines, splits, employeeId, methods, onClosed }: Props) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const equalMutation = useCreateEqualSplitsMutation();
  const linesMutation = useCreateLinesSplitMutation();
  const activeSplits = splits.filter((split) => split.status !== "Cancelada");
  const canAddSplit = activeSplits.length === 0 || activeSplits.every((split) => split.split_type === "Por lineas");
  const usedIds = useMemo(() => new Set(activeSplits.flatMap((split) => split.lines.map((line) => line.ticket_line_id))), [activeSplits]);
  const error = equalMutation.isError || linesMutation.isError ? "No se pudo dividir la cuenta. Revisa la selección e intenta de nuevo." : null;
  return <section className="border-t-2 border-zinc-700 pt-3"><div className="flex items-center justify-between gap-2"><p className="font-black uppercase">Cuenta dividida</p>{employeeId !== null && canAddSplit && ticket.status !== "Cobrado" && ticket.status !== "Cancelado" ? <BrutalButton type="button" size="sm" onClick={() => setDialogOpen(true)}>{activeSplits.length ? "Agregar parte" : "Dividir"}</BrutalButton> : null}</div>{activeSplits.length === 0 ? <p className="mt-2 text-sm font-bold text-[var(--kp-muted)]">Puedes separar por partes iguales o por productos.</p> : <div className="mt-3 grid gap-3">{activeSplits.map((split) => <article key={split.id} className="border-2 border-[var(--kp-ink)] p-3"><div className="flex justify-between gap-3"><div><p className="font-black">{split.name}</p><p className="text-sm font-bold text-[var(--kp-muted)]">{split.status}</p></div><p className="font-black">{formatCentsToPesos(split.amount_cents)}</p></div>{split.status === "Abierta" && ticket.status === "En cobro" && employeeId !== null ? <SplitPaymentForm split={split} ticketId={ticket.id} cashShiftId={ticket.cash_shift_id} employeeId={employeeId} methods={methods} onClosed={onClosed} /> : null}</article>)}</div>}{dialogOpen && employeeId !== null ? <SplitTicketDialog lines={lines} usedIds={usedIds} allowEqual={activeSplits.length === 0} isSaving={equalMutation.isPending || linesMutation.isPending} errorMessage={error} onClose={() => { equalMutation.reset(); linesMutation.reset(); setDialogOpen(false); }} onEqual={(parts) => void equalMutation.mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId, parts } }).then(() => setDialogOpen(false)).catch(() => undefined)} onLines={(name, ticketLineIds) => void linesMutation.mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId, name, ticket_line_ids: ticketLineIds } }).then(() => setDialogOpen(false)).catch(() => undefined)} /> : null}</section>;
}

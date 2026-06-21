import { useMemo, useState, type FormEvent } from "react";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import type { PaymentMethod } from "../../payments/types/paymentTypes";
import { usePayTicketSplitMutation } from "../hooks/useTicketSplitMutations";
import type { TicketSplit } from "../types/ticketSplitTypes";

type Props = { split: TicketSplit; ticketId: number; cashShiftId: number; employeeId: number; methods: PaymentMethod[]; onClosed: () => void };
export function SplitPaymentForm({ split, ticketId, cashShiftId, employeeId, methods, onClosed }: Props) {
  const activeMethods = useMemo(() => methods.filter((method) => method.active), [methods]);
  const [methodId, setMethodId] = useState<number | null>(activeMethods[0]?.id ?? null);
  const [received, setReceived] = useState((split.amount_cents / 100).toFixed(2));
  const [reference, setReference] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const mutation = usePayTicketSplitMutation();
  const selectedMethod = activeMethods.find((method) => method.id === methodId);
  const isCash = selectedMethod?.method_key === "Efectivo";
  async function submit(event: FormEvent) {
    event.preventDefault(); setMessage(null);
    const receivedCents = isCash ? parsePesosToCents(received) : null;
    if (methodId === null || (isCash && (receivedCents === null || receivedCents < split.amount_cents))) { setMessage("Ingresa un monto recibido válido."); return; }
    if (selectedMethod?.requires_reference && !reference.trim()) { setMessage("Ingresa la referencia."); return; }
    try {
      const result = await mutation.mutateAsync({ ticketId, cashShiftId, splitId: split.id, payload: { employee_id: employeeId, payment_method_id: methodId, amount_cents: split.amount_cents, received_cents: receivedCents, reference: selectedMethod?.requires_reference ? reference.trim() : null } });
      if (result.ticket_closed) onClosed(); else setMessage(result.change_cents > 0 ? `Cambio: ${formatCentsToPesos(result.change_cents)}` : "Parte pagada.");
    } catch { setMessage("No se pudo registrar el pago."); }
  }
  if (activeMethods.length === 0) return <p className="font-bold">No hay formas de pago disponibles.</p>;
  return <form onSubmit={submit} className="mt-2 grid gap-2 border-t-2 border-zinc-700 pt-2"><label className="grid gap-1 text-sm font-black">Forma de pago<select value={methodId ?? ""} onChange={(event) => setMethodId(Number(event.target.value))} className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2">{activeMethods.map((method) => <option key={method.id} value={method.id}>{method.name}</option>)}</select></label>{isCash ? <label className="grid gap-1 text-sm font-black">Monto recibido<input value={received} onChange={(event) => setReceived(event.target.value)} inputMode="decimal" className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2" /></label> : null}{selectedMethod?.requires_reference ? <label className="grid gap-1 text-sm font-black">Referencia<input value={reference} onChange={(event) => setReference(event.target.value)} className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2" /></label> : null}{message ? <p className="font-bold">{message}</p> : null}<button type="submit" disabled={mutation.isPending} className="border-4 border-[var(--kp-ink)] bg-[var(--kp-selected)] p-2 font-black uppercase text-[var(--kp-selected-contrast)] disabled:opacity-50">{mutation.isPending ? "Registrando..." : `Pagar ${formatCentsToPesos(split.amount_cents)}`}</button></form>;
}

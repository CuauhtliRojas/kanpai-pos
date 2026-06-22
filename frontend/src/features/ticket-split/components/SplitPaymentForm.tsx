import { useEffect, useMemo, useState, type FormEvent } from "react";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import {
  isCardMethod,
  isCashMethod,
  isTransferMethod,
  requiresPaymentReference,
} from "../../payments/utils/paymentMethodPolicy";
import type { PaymentMethod } from "../../payments/types/paymentTypes";
import { usePayTicketSplitMutation } from "../hooks/useTicketSplitMutations";
import type { TicketSplit } from "../types/ticketSplitTypes";

type Props = {
  split: TicketSplit;
  ticketId: number;
  cashShiftId: number;
  employeeId: number;
  methods: PaymentMethod[];
  onClosed: () => void;
};

export function SplitPaymentForm({ split, ticketId, cashShiftId, employeeId, methods, onClosed }: Props) {
  const activeMethods = useMemo(() => methods.filter((method) => method.active), [methods]);
  const [methodId, setMethodId] = useState<number | null>(activeMethods[0]?.id ?? null);
  const [received, setReceived] = useState((split.amount_cents / 100).toFixed(2));
  const [reference, setReference] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const mutation = usePayTicketSplitMutation();
  const selectedMethod = activeMethods.find((method) => method.id === methodId) ?? null;
  const isCash = isCashMethod(selectedMethod);
  const isCard = isCardMethod(selectedMethod);
  const isTransfer = isTransferMethod(selectedMethod);
  const requiresReference = requiresPaymentReference(selectedMethod);
  const receivedCents = isCash ? parsePesosToCents(received) : null;
  const cashShortfall = isCash && (receivedCents === null || receivedCents < split.amount_cents);
  const changeCents = isCash && receivedCents !== null
    ? Math.max(0, receivedCents - split.amount_cents)
    : null;

  useEffect(() => {
    setReceived((split.amount_cents / 100).toFixed(2));
  }, [split.amount_cents]);

  useEffect(() => {
    if (methodId === null && activeMethods[0]) setMethodId(activeMethods[0].id);
  }, [activeMethods, methodId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    if (methodId === null) {
      setMessage("Selecciona una forma de pago.");
      return;
    }
    if (cashShortfall) {
      setMessage("El efectivo recibido no cubre el monto a pagar.");
      return;
    }
    if (requiresReference && !reference.trim()) {
      setMessage("Ingresa el folio o comprobante de la transferencia.");
      return;
    }
    try {
      const result = await mutation.mutateAsync({
        ticketId,
        cashShiftId,
        splitId: split.id,
        payload: {
          employee_id: employeeId,
          payment_method_id: methodId,
          amount_cents: split.amount_cents,
          received_cents: receivedCents,
          reference: requiresReference ? reference.trim() : null,
        },
      });
      if (result.ticket_closed) onClosed();
      else setMessage("Parte pagada.");
    } catch {
      setMessage("No se pudo registrar el pago.");
    }
  }

  if (activeMethods.length === 0) return <p className="font-bold">No hay formas de pago disponibles.</p>;

  return (
    <form onSubmit={submit} className="mt-2 grid gap-2 border-t-2 border-zinc-700 pt-2">
      <p className="font-black">Monto a pagar: {formatCentsToPesos(split.amount_cents)}</p>
      <label className="grid gap-1 text-sm font-black">
        Forma de pago
        <select
          value={methodId ?? ""}
          onChange={(event) => { setMethodId(Number(event.target.value)); setReference(""); setMessage(null); }}
          className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2"
        >
          {activeMethods.map((method) => <option key={method.id} value={method.id}>{method.name}</option>)}
        </select>
      </label>
      {isCash ? (
        <div className="grid gap-1 border-2 border-[var(--kp-ink)] p-2">
          <label className="grid gap-1 text-sm font-black">
            Monto recibido
            <input value={received} onChange={(event) => { setReceived(event.target.value); setMessage(null); }} inputMode="decimal" className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2" />
          </label>
          {cashShortfall ? <p className="text-sm font-black text-[var(--kp-danger-text)]">El efectivo recibido no cubre el monto a pagar.</p> : null}
          {changeCents !== null ? <p className="font-black">Cambio: {formatCentsToPesos(changeCents)}</p> : null}
        </div>
      ) : null}
      {isCard ? <p className="border-2 border-[var(--kp-ink)] p-2 text-sm font-bold">Cobra en la terminal y confirma el pago.</p> : null}
      {requiresReference ? (
        <label className="grid gap-1 text-sm font-black">
          {isTransfer ? "Folio o comprobante" : "Referencia"}
          <input value={reference} onChange={(event) => setReference(event.target.value)} className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2" />
        </label>
      ) : null}
      {message ? <p className="font-bold">{message}</p> : null}
      <button type="submit" disabled={mutation.isPending || cashShortfall} className="border-4 border-[var(--kp-ink)] bg-[var(--kp-selected)] p-2 font-black uppercase text-[var(--kp-selected-contrast)] disabled:opacity-50">
        {mutation.isPending ? "Registrando..." : `Pagar ${formatCentsToPesos(split.amount_cents)}`}
      </button>
    </form>
  );
}

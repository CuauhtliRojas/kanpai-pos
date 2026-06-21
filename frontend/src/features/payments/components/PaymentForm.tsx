import { useEffect, useMemo, useState, type FormEvent } from "react";
import { parsePesosToCents } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";
import { useCreatePaymentMutation } from "../hooks/useCreatePaymentMutation";
import type { PaymentMethod } from "../types/paymentTypes";

type PaymentFormProps = {
  ticket: Ticket;
  employeeId: number | null;
  remainingCents: number;
  methods: PaymentMethod[];
  onClosed: () => void;
};

export function PaymentForm({
  ticket,
  employeeId,
  remainingCents,
  methods,
  onClosed,
}: PaymentFormProps) {
  const activeMethods = useMemo(() => methods.filter((method) => method.active), [methods]);
  const [methodId, setMethodId] = useState<number | null>(activeMethods[0]?.id ?? null);
  const [amount, setAmount] = useState((remainingCents / 100).toFixed(2));
  const [received, setReceived] = useState((remainingCents / 100).toFixed(2));
  const [reference, setReference] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const createMutation = useCreatePaymentMutation();
  const selectedMethod = activeMethods.find((method) => method.id === methodId) ?? null;
  const isCash = selectedMethod?.method_key === "Efectivo";

  useEffect(() => {
    const remaining = (remainingCents / 100).toFixed(2);
    setAmount(remaining);
    setReceived(remaining);
  }, [remainingCents]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);

    const amountCents = parsePesosToCents(amount);
    const receivedCents = isCash ? parsePesosToCents(received) : null;
    if (
      employeeId === null ||
      methodId === null ||
      amountCents === null ||
      amountCents <= 0 ||
      amountCents > remainingCents
    ) {
      setMessage("Ingresa un monto válido.");
      return;
    }
    if (isCash && (receivedCents === null || receivedCents < amountCents)) {
      setMessage("El monto recibido debe cubrir el pago.");
      return;
    }
    if (selectedMethod?.requires_reference && !reference.trim()) {
      setMessage("Ingresa la referencia.");
      return;
    }

    try {
      const result = await createMutation.mutateAsync({
        ticketId: ticket.id,
        cashShiftId: ticket.cash_shift_id,
        payload: {
          employee_id: employeeId,
          payment_method_id: methodId,
          amount_cents: amountCents,
          received_cents: isCash ? receivedCents : null,
          reference: selectedMethod?.requires_reference ? reference.trim() : null,
        },
      });
      if (result.closed) {
        onClosed();
        return;
      }
      setReference("");
      setMessage("Pago registrado.");
    } catch {
      setMessage("No se pudo registrar el pago.");
    }
  }

  if (activeMethods.length === 0) {
    return <p className="font-bold">No hay métodos de pago disponibles.</p>;
  }

  return (
    <form className="grid gap-3 border-t-2 border-zinc-700 pt-4" onSubmit={handleSubmit}>
      <label className="grid gap-1 font-black">
        Método
        <select
          value={methodId ?? ""}
          onChange={(event) => {
            setMethodId(Number(event.target.value));
            setMessage(null);
          }}
          className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2"
        >
          {activeMethods.map((method) => (
            <option key={method.id} value={method.id}>
              {method.name}
            </option>
          ))}
        </select>
      </label>

      <label className="grid gap-1 font-black">
        Monto
        <input
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          inputMode="decimal"
          className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2"
        />
      </label>

      {isCash ? (
        <>
          <label className="grid gap-1 font-black">
            Monto recibido
            <input
              value={received}
              onChange={(event) => setReceived(event.target.value)}
              inputMode="decimal"
              className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2"
            />
          </label>
        </>
      ) : null}

      {selectedMethod?.requires_reference ? (
        <label className="grid gap-1 font-black">
          Referencia
          <input
            value={reference}
            onChange={(event) => setReference(event.target.value)}
            className="border-2 border-[var(--kp-ink)] bg-zinc-900 p-2"
          />
        </label>
      ) : null}

      <p className="text-sm font-bold text-[var(--kp-muted)]">
        Para pago mixto, registra cada monto por separado.
      </p>
      {message ? <p className="font-black">{message}</p> : null}
      <button
        type="submit"
        disabled={createMutation.isPending}
        className="border-4 border-[var(--kp-ink)] bg-[var(--kp-selected)] px-4 py-3 font-black uppercase text-[var(--kp-selected-contrast)] shadow-[var(--kp-shadow-hard-sm)] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {createMutation.isPending ? "Registrando..." : "Registrar pago"}
      </button>
    </form>
  );
}

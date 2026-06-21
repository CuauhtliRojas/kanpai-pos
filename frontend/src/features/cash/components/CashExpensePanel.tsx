import { useState, type FormEvent } from "react";
import { ReceiptText } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { parsePesosToCents } from "../../../shared/lib/money";

type CashExpensePanelProps = {
  canCreate: boolean;
  isSaving: boolean;
  errorMessage: string | null;
  onCreate: (amountCents: number, description: string) => Promise<void>;
};

export function CashExpensePanel({
  canCreate,
  isSaving,
  errorMessage,
  onCreate,
}: CashExpensePanelProps) {
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cents = parsePesosToCents(amount);
    const cleanDescription = description.trim();
    if (cents === null || cents <= 0) {
      setValidationMessage("Escribe un monto mayor a cero.");
      return;
    }
    if (!cleanDescription) {
      setValidationMessage("Escribe el motivo del gasto.");
      return;
    }

    setValidationMessage(null);
    setSavedMessage(null);
    try {
      await onCreate(cents, cleanDescription);
      setAmount("");
      setDescription("");
      setSavedMessage("Gasto registrado. Listo.");
    } catch {
      // El mensaje de la operación se muestra dentro del panel.
    }
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <h2 className="text-2xl font-black uppercase">Registrar gasto</h2>
      {canCreate ? (
        <form className="mt-4 grid gap-4" onSubmit={handleSubmit}>
          <label className="grid gap-2 font-black uppercase">
            Motivo
            <input
              type="text"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-white px-3 text-lg font-bold text-[var(--kp-text-on-light)] outline-none"
            />
          </label>
          <label className="grid gap-2 font-black uppercase">
            Monto
            <div className="flex border-4 border-[var(--kp-ink)] bg-white text-[var(--kp-text-on-light)]">
              <span className="px-3 py-3 text-xl font-black">$</span>
              <input
                type="text"
                inputMode="decimal"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="0.00"
                className="min-w-0 flex-1 bg-transparent px-1 text-xl font-black outline-none"
              />
            </div>
          </label>
          {validationMessage || errorMessage ? (
            <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
              {validationMessage ?? errorMessage}
            </p>
          ) : null}
          {savedMessage ? (
            <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 font-bold text-[var(--kp-success-text)]">
              {savedMessage}
            </p>
          ) : null}
          <BrutalButton type="submit" variant="warning" size="lg" disabled={isSaving}>
            <ReceiptText className="h-7 w-7" />
            {isSaving ? "Guardando..." : "Registrar gasto"}
          </BrutalButton>
        </form>
      ) : (
        <div className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-4 text-[var(--kp-warning-contrast)]">
          <p className="font-black uppercase">No tienes permiso para usar esta opción.</p>
          <p className="mt-2 font-bold">Pide ayuda al encargado.</p>
        </div>
      )}
    </section>
  );
}

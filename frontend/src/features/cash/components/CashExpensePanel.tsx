import { useEffect, useState, type FormEvent } from "react";
import { ListChecks, ReceiptText } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import { CashAmountPad, normalizeCashAmount } from "./CashAmountPad";

const expenseCategories = [
  ["SUPPLIES", "Insumo"],
  ["SERVICE", "Servicio"],
  ["OPERATIONS", "Operación"],
  ["MAINTENANCE", "Mantenimiento"],
  ["OTHER", "Otro"],
] as const;

type CashExpensePanelProps = {
  canCreate: boolean;
  isSaving: boolean;
  errorMessage: string | null;
  totalExpensesCents: number;
  expenseCount: number;
  onViewExpenses: () => void;
  onCreate: (
    amountCents: number,
    description: string,
    category: string,
    note: string | null,
  ) => Promise<void>;
};

export function CashExpensePanel({
  canCreate,
  isSaving,
  errorMessage,
  totalExpensesCents,
  expenseCount,
  onViewExpenses,
  onCreate,
}: CashExpensePanelProps) {
  const [showCreate, setShowCreate] = useState(false);
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("OTHER");
  const [note, setNote] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!showCreate) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving) setShowCreate(false);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSaving, showCreate]);

  function resetForm() {
    setAmount("");
    setDescription("");
    setCategory("OTHER");
    setNote("");
    setValidationMessage(null);
  }

  function openDialog() {
    resetForm();
    setSavedMessage(null);
    setShowCreate(true);
  }

  function closeDialog() {
    if (isSaving) return;
    setShowCreate(false);
    resetForm();
  }

  function handleAmountChange(value: string) {
    const normalizedValue = normalizeCashAmount(value);
    if (normalizedValue === null) return;
    setAmount(normalizedValue);
    setValidationMessage(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amountCents = parsePesosToCents(amount);
    const cleanDescription = description.trim();
    const cleanNote = note.trim();

    if (!cleanDescription) {
      setValidationMessage("Escribe el motivo del gasto.");
      return;
    }
    if (amountCents === null || amountCents <= 0) {
      setValidationMessage("Escribe un monto mayor a cero.");
      return;
    }

    setValidationMessage(null);
    try {
      await onCreate(amountCents, cleanDescription, category, cleanNote || null);
      setShowCreate(false);
      resetForm();
      setSavedMessage("Gasto registrado. Listo.");
    } catch {
      // El mensaje de la operación se muestra dentro del diálogo.
    }
  }

  return (
    <>
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">Movimientos del turno</p>
            <h2 className="text-2xl font-black uppercase">Gastos del turno</h2>
            <p className="mt-1 font-bold text-[var(--kp-muted)]">Registra salidas de efectivo del turno.</p>
          </div>

          <div className="text-right">
            <p className="text-2xl font-black">{formatCentsToPesos(totalExpensesCents)}</p>
            <p className="text-sm font-bold text-[var(--kp-muted)]">{expenseCount} registrados</p>
          </div>
        </div>

        {savedMessage ? (
          <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-2 font-bold text-[var(--kp-success-text)]">
            {savedMessage}
          </p>
        ) : null}

        <div className="mt-3 flex flex-wrap gap-3">
          {canCreate ? (
            <BrutalButton type="button" variant="primary" size="md" onClick={openDialog}>
              <ReceiptText className="h-6 w-6" />
              Registrar gasto
            </BrutalButton>
          ) : null}
          <BrutalButton type="button" size="md" onClick={onViewExpenses}>
            <ListChecks className="h-6 w-6" />
            Ver gastos
          </BrutalButton>
        </div>

        {!canCreate ? (
          <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-3 font-bold text-[var(--kp-warning-contrast)]">
            Sin permiso para registrar gastos. Pide ayuda al encargado.
          </p>
        ) : null}
      </section>

      {showCreate && canCreate ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/70 p-3"
          onClick={closeDialog}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-expense-title"
            className="w-full max-w-4xl border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div>
              <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">Gastos del turno</p>
              <h2 id="create-expense-title" className="text-2xl font-black uppercase">Registrar gasto</h2>
            </div>

            <form className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1.2fr)_minmax(16rem,0.8fr)]" onSubmit={handleSubmit}>
              <div className="grid content-start gap-3">
                <label className="grid gap-1 font-black uppercase">
                  Motivo
                  <input
                    type="text"
                    autoFocus
                    disabled={isSaving}
                    value={description}
                    onChange={(event) => {
                      setDescription(event.target.value);
                      setValidationMessage(null);
                    }}
                    placeholder="Ej. Servilletas, taxi o compra local"
                    className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-lg font-bold text-[var(--kp-text)] outline-none placeholder:text-[var(--kp-muted)] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-[var(--kp-info)] disabled:opacity-50"
                  />
                </label>

                <label className="grid gap-1 font-black uppercase">
                  Tipo de gasto
                  <select
                    disabled={isSaving}
                    value={category}
                    onChange={(event) => setCategory(event.target.value)}
                    className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-lg font-black text-[var(--kp-text)] outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-[var(--kp-info)] disabled:opacity-50"
                  >
                    {expenseCategories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </label>

                <label className="grid gap-1 font-black uppercase">
                  Monto
                  <div className="flex min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)] focus-within:outline focus-within:outline-4 focus-within:outline-offset-2 focus-within:outline-[var(--kp-info)]">
                    <span className="px-3 py-2 text-xl font-black" aria-hidden="true">$</span>
                    <input
                      type="text"
                      inputMode="decimal"
                      disabled={isSaving}
                      value={amount}
                      onChange={(event) => handleAmountChange(event.target.value)}
                      placeholder="0.00"
                      aria-label="Monto del gasto en pesos"
                      className="min-w-0 flex-1 bg-transparent px-1 text-xl font-black outline-none placeholder:text-[var(--kp-muted)] disabled:opacity-50"
                    />
                  </div>
                </label>

                <label className="grid gap-1 font-black uppercase">
                  Nota <span className="text-xs text-[var(--kp-muted)]">Opcional</span>
                  <textarea
                    disabled={isSaving}
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="Detalle adicional para el cierre"
                    rows={2}
                    className="resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 font-bold text-[var(--kp-text)] outline-none placeholder:text-[var(--kp-muted)] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-[var(--kp-info)] disabled:opacity-50"
                  />
                </label>

                {validationMessage || errorMessage ? (
                  <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-2 font-bold text-[var(--kp-danger-text)]">
                    {validationMessage ?? errorMessage}
                  </p>
                ) : null}

                <div className="grid grid-cols-2 gap-2">
                  <BrutalButton type="button" size="md" disabled={isSaving} onClick={closeDialog}>Volver</BrutalButton>
                  <BrutalButton type="submit" variant="primary" size="md" disabled={isSaving}>
                    {isSaving ? "Guardando..." : "Guardar gasto"}
                  </BrutalButton>
                </div>
              </div>

              <CashAmountPad value={amount} onChange={handleAmountChange} disabled={isSaving} label="Teclado para monto del gasto" />
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}

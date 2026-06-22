import { useState, type FormEvent } from "react";
import { LockKeyhole, WalletCards } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { parsePesosToCents } from "../../../shared/lib/money";
import { CashAmountPad, normalizeCashAmount } from "./CashAmountPad";

const quickAmounts = [100, 200, 500, 1000];

type CashClosedPanelProps = {
  canOpen: boolean;
  isOpening: boolean;
  errorMessage: string | null;
  onOpen: (openingCashCents: number) => Promise<void>;
};

export function CashClosedPanel({
  canOpen,
  isOpening,
  errorMessage,
  onOpen,
}: CashClosedPanelProps) {
  const [openingCash, setOpeningCash] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const openingCashCents = parsePesosToCents(openingCash);
  const canSubmit = canOpen && !isOpening && openingCashCents !== null && openingCashCents > 0;

  function updateOpeningCash(value: string) {
    setOpeningCash(value);
    setValidationMessage(null);
  }

  function handleInputChange(value: string) {
    const normalizedValue = normalizeCashAmount(value);
    if (normalizedValue !== null) updateOpeningCash(normalizedValue);
  }

  function showValidationMessage() {
    if (openingCashCents === 0) {
      setValidationMessage("El fondo inicial debe ser mayor a $0.00.");
    } else if (openingCashCents === null) {
      setValidationMessage("Escribe un fondo inicial válido.");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || openingCashCents === null) {
      showValidationMessage();
      return;
    }

    setValidationMessage(null);
    try {
      await onOpen(openingCashCents);
    } catch {
      // El mensaje de la operación se muestra dentro del panel.
    }
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard)] md:p-4">
      <div className="mx-auto max-w-5xl">
        {canOpen ? (
          <form className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,0.72fr)]" onSubmit={handleSubmit}>
            <div className="grid content-start gap-3">
              <div className="flex items-start gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
                <LockKeyhole className="h-8 w-8 shrink-0 text-[var(--kp-selected)]" />
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">Estado</p>
                  <h2 className="text-xl font-black uppercase md:text-2xl">Caja cerrada</h2>
                  <p className="mt-1 font-bold">Declara el efectivo inicial para comenzar a tomar pedidos.</p>
                  <p className="text-sm font-semibold text-[var(--kp-muted)]">
                    Las ventas y mesas se activan cuando abras caja.
                  </p>
                </div>
              </div>

              <label className="grid gap-1 font-black uppercase tracking-[0.08em]">
                Fondo inicial
                <div className="flex min-h-[var(--kp-touch-md)] items-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] focus-within:outline focus-within:outline-4 focus-within:outline-offset-2 focus-within:outline-[var(--kp-info)]">
                  <span className="px-3 text-2xl" aria-hidden="true">$</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    disabled={isOpening}
                    value={openingCash}
                    onChange={(event) => handleInputChange(event.target.value)}
                    onBlur={showValidationMessage}
                    placeholder="0.00"
                    aria-label="Fondo inicial en pesos"
                    className="min-w-0 flex-1 bg-transparent px-1 py-2 text-2xl font-black text-[var(--kp-text)] outline-none placeholder:text-[var(--kp-muted)] disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </label>

              <div>
                <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">Montos rápidos</p>
                <div className="mt-1 grid grid-cols-4 gap-2">
                  {quickAmounts.map((amount) => (
                    <BrutalButton
                      key={amount}
                      type="button"
                      size="md"
                      disabled={isOpening}
                      onClick={() => updateOpeningCash(String(amount))}
                    >
                      ${amount}
                    </BrutalButton>
                  ))}
                </div>
              </div>

              {validationMessage || errorMessage ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-2 font-bold text-[var(--kp-danger-text)]">
                  {validationMessage ?? errorMessage}
                </p>
              ) : null}

              <BrutalButton type="submit" variant="success" size="md" fullWidth disabled={!canSubmit}>
                <WalletCards className="h-6 w-6" />
                {isOpening ? "Abriendo caja..." : "Abrir caja"}
              </BrutalButton>
            </div>

            <CashAmountPad
              value={openingCash}
              onChange={updateOpeningCash}
              disabled={isOpening}
              label="Teclado para fondo inicial"
            />
          </form>
        ) : (
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,0.72fr)]">
            <div className="flex items-start gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
              <LockKeyhole className="h-8 w-8 shrink-0 text-[var(--kp-selected)]" />
              <div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">Estado</p>
                <h2 className="text-xl font-black uppercase md:text-2xl">Caja cerrada</h2>
                <p className="mt-1 font-bold">Las ventas permanecen bloqueadas hasta abrir caja.</p>
              </div>
            </div>
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-3 text-[var(--kp-warning-contrast)]">
              <p className="font-black uppercase">No tienes permiso para usar esta opción.</p>
              <p className="mt-1 font-bold">Pide ayuda al encargado.</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

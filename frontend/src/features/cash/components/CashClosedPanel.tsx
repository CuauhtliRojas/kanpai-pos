import { useState, type FormEvent } from "react";
import { LockKeyhole, WalletCards } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { parsePesosToCents } from "../../../shared/lib/money";

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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cents = parsePesosToCents(openingCash);
    if (cents === null || cents < 0) {
      setValidationMessage("Escribe un fondo inicial válido.");
      return;
    }

    setValidationMessage(null);
    try {
      await onOpen(cents);
    } catch {
      // El mensaje de la operación se muestra dentro del panel.
    }
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)] md:p-6">
      <div className="flex items-center gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-4">
        <LockKeyhole className="h-10 w-10 text-[var(--kp-selected)]" />
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-muted)]">Estado</p>
          <h2 className="text-3xl font-black uppercase">Caja cerrada</h2>
        </div>
      </div>

      {canOpen ? (
        <form className="mt-5 grid max-w-xl gap-4" onSubmit={handleSubmit}>
          <label className="grid gap-2 font-black uppercase tracking-[0.08em]">
            Fondo inicial
            <div className="flex min-h-[var(--kp-touch-lg)] items-center border-4 border-[var(--kp-ink)] bg-white text-[var(--kp-text-on-light)] shadow-[var(--kp-shadow-hard-sm)]">
              <span className="px-4 text-2xl">$</span>
              <input
                type="text"
                inputMode="decimal"
                value={openingCash}
                onChange={(event) => setOpeningCash(event.target.value)}
                placeholder="0.00"
                aria-label="Fondo inicial en pesos"
                className="min-w-0 flex-1 bg-transparent px-1 py-4 text-2xl font-black outline-none"
              />
            </div>
          </label>
          {validationMessage || errorMessage ? (
            <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
              {validationMessage ?? errorMessage}
            </p>
          ) : null}
          <BrutalButton type="submit" variant="warning" size="lg" disabled={isOpening}>
            <WalletCards className="h-7 w-7" />
            {isOpening ? "Abriendo caja..." : "Abrir caja"}
          </BrutalButton>
        </form>
      ) : (
        <div className="mt-5 border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-4 text-[var(--kp-warning-contrast)]">
          <p className="text-lg font-black uppercase">No tienes permiso para usar esta opción.</p>
          <p className="mt-2 font-bold">Pide ayuda al encargado.</p>
        </div>
      )}
    </section>
  );
}

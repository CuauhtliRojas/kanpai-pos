import { useEffect, useState, type FormEvent } from "react";
import { CircleCheckBig, OctagonAlert } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import type { CashShift } from "../types/cashTypes";
import { CashAmountPad, normalizeCashAmount } from "./CashAmountPad";

type CashOpenPanelProps = {
  cashShift: CashShift;
  canClose: boolean;
  isClosing: boolean;
  errorMessage: string | null;
  onClose: (declaredCashCents: number) => Promise<void>;
};

function formatOpenedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("es-MX");
}

export function CashOpenPanel({
  cashShift,
  canClose,
  isClosing,
  errorMessage,
  onClose,
}: CashOpenPanelProps) {
  const [showClose, setShowClose] = useState(false);
  const [declaredCash, setDeclaredCash] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const declaredCashCents = parsePesosToCents(declaredCash);
  const canSubmitClose = !isClosing && declaredCashCents !== null && declaredCashCents >= 0;

  useEffect(() => {
    if (!showClose) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isClosing) setShowClose(false);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isClosing, showClose]);

  function updateDeclaredCash(value: string) {
    setDeclaredCash(value);
    setValidationMessage(null);
  }

  function handleInputChange(value: string) {
    const normalizedValue = normalizeCashAmount(value);
    if (normalizedValue !== null) updateDeclaredCash(normalizedValue);
  }

  function closeDialog() {
    if (isClosing) return;
    setShowClose(false);
    setDeclaredCash("");
    setValidationMessage(null);
  }

  function openDialog() {
    setDeclaredCash("");
    setValidationMessage(null);
    setShowClose(true);
  }

  async function handleClose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmitClose || declaredCashCents === null) {
      setValidationMessage("Escribe el efectivo contado.");
      return;
    }

    setValidationMessage(null);
    try {
      await onClose(declaredCashCents);
    } catch {
      // El mensaje de la operación se muestra dentro del diálogo.
    }
  }

  return (
    <>
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard)] md:p-4">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 text-[var(--kp-success-text)]">
          <div className="flex items-start gap-3">
            <CircleCheckBig className="h-9 w-9 shrink-0" />
            <div>
              <p className="text-xs font-black uppercase tracking-[0.18em]">Estado</p>
              <h2 className="text-2xl font-black uppercase md:text-3xl">Caja abierta</h2>
              <p className="mt-1 font-bold">Ya puedes tomar pedidos y registrar gastos.</p>
            </div>
          </div>

          <dl className="grid grid-cols-2 gap-x-5 gap-y-1 text-sm sm:grid-cols-3">
            <div>
              <dt className="font-black uppercase">Folio</dt>
              <dd className="font-bold">{cashShift.folio}</dd>
            </div>
            <div>
              <dt className="font-black uppercase">Apertura</dt>
              <dd className="font-bold">{formatOpenedAt(cashShift.opened_at)}</dd>
            </div>
            <div>
              <dt className="font-black uppercase">Fondo inicial</dt>
              <dd className="font-bold">{formatCentsToPesos(cashShift.opening_cash_cents)}</dd>
            </div>
          </dl>
        </div>

        <div className="mx-auto mt-3 flex max-w-6xl items-center justify-between gap-3 border-t-4 border-[var(--kp-ink)] pt-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-danger-text)]">Acción crítica</p>
            <p className="text-sm font-bold text-[var(--kp-muted)]">Cierra la caja únicamente al terminar el turno.</p>
          </div>
          {canClose ? (
            <BrutalButton type="button" variant="danger" size="md" onClick={openDialog}>
              <OctagonAlert className="h-6 w-6" />
              Cerrar caja
            </BrutalButton>
          ) : (
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-2 text-[var(--kp-warning-contrast)]">
              <p className="font-black">Pide ayuda al encargado para cerrar caja.</p>
            </div>
          )}
        </div>
      </section>

      {showClose && canClose ? (
        <div
          className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/70 p-4"
          onClick={closeDialog}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="close-cash-title"
            className="w-full max-w-3xl border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 text-[var(--kp-danger-text)]">
              <h2 id="close-cash-title" className="text-2xl font-black uppercase">Cerrar caja</h2>
              <p className="mt-1 font-bold">Cuenta el efectivo antes de cerrar. Esta acción termina el turno.</p>
            </div>

            <form className="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(16rem,0.8fr)]" onSubmit={handleClose}>
              <div className="grid content-start gap-3">
                <label className="grid gap-1 font-black uppercase">
                  Efectivo contado
                  <div className="flex min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)] focus-within:outline focus-within:outline-4 focus-within:outline-offset-2 focus-within:outline-[var(--kp-info)]">
                    <span className="px-3 py-2 text-2xl font-black" aria-hidden="true">$</span>
                    <input
                      type="text"
                      inputMode="decimal"
                      autoFocus
                      disabled={isClosing}
                      value={declaredCash}
                      onChange={(event) => handleInputChange(event.target.value)}
                      placeholder="0.00"
                      aria-label="Efectivo contado en pesos"
                      className="min-w-0 flex-1 bg-transparent px-1 text-2xl font-black outline-none placeholder:text-[var(--kp-muted)] disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                </label>

                {validationMessage || errorMessage ? (
                  <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-2 font-bold text-[var(--kp-danger-text)]">
                    {validationMessage ?? errorMessage}
                  </p>
                ) : null}

                <div className="grid gap-2 sm:grid-cols-2">
                  <BrutalButton type="button" size="md" disabled={isClosing} onClick={closeDialog}>
                    Volver
                  </BrutalButton>
                  <BrutalButton type="submit" variant="danger" size="md" disabled={!canSubmitClose}>
                    {isClosing ? "Cerrando..." : "Cerrar caja"}
                  </BrutalButton>
                </div>
              </div>

              <CashAmountPad
                value={declaredCash}
                onChange={updateDeclaredCash}
                disabled={isClosing}
                label="Teclado para efectivo contado"
              />
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}

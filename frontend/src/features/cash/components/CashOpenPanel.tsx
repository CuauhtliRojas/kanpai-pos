import { useState, type FormEvent } from "react";
import { CircleCheckBig, OctagonAlert } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import type { CashShift } from "../types/cashTypes";

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

  async function handleClose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cents = parsePesosToCents(declaredCash);
    if (cents === null || cents < 0) {
      setValidationMessage("Escribe el efectivo contado.");
      return;
    }
    setValidationMessage(null);
    try {
      await onClose(cents);
    } catch {
      // El mensaje de la operación se muestra dentro del panel.
    }
  }

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)] md:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-4 text-[var(--kp-success-text)]">
        <div className="flex items-center gap-3">
          <CircleCheckBig className="h-10 w-10" />
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em]">Estado</p>
            <h2 className="text-3xl font-black uppercase">Caja abierta</h2>
          </div>
        </div>
        <div className="text-right font-bold">
          <p className="text-xl font-black">{cashShift.folio}</p>
          <p>{formatOpenedAt(cashShift.opened_at)}</p>
          <p>Fondo inicial: {formatCentsToPesos(cashShift.opening_cash_cents)}</p>
        </div>
      </div>

      <div className="mt-5">
        {canClose ? (
          !showClose ? (
            <BrutalButton type="button" variant="danger" size="lg" onClick={() => setShowClose(true)}>
              <OctagonAlert className="h-7 w-7" />
              Cerrar caja
            </BrutalButton>
          ) : (
            <form onSubmit={handleClose} className="grid max-w-xl gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-4">
              <h3 className="text-xl font-black uppercase text-[var(--kp-danger-text)]">Cerrar caja</h3>
              <label className="grid gap-2 font-black uppercase">
                Efectivo contado
                <div className="flex border-4 border-[var(--kp-ink)] bg-white text-[var(--kp-text-on-light)]">
                  <span className="px-3 py-3 text-xl font-black">$</span>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={declaredCash}
                    onChange={(event) => setDeclaredCash(event.target.value)}
                    placeholder="0.00"
                    className="min-w-0 flex-1 bg-transparent px-1 text-xl font-black outline-none"
                  />
                </div>
              </label>
              {validationMessage || errorMessage ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 font-bold text-[var(--kp-danger-text)]">
                  {validationMessage ?? errorMessage}
                </p>
              ) : null}
              <p className="font-bold text-[var(--kp-danger-text)]">Revisa el efectivo antes de continuar.</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <BrutalButton type="button" size="lg" onClick={() => setShowClose(false)}>
                  Volver
                </BrutalButton>
                <BrutalButton type="submit" variant="danger" size="lg" disabled={isClosing}>
                  {isClosing ? "Cerrando..." : "Cerrar caja"}
                </BrutalButton>
              </div>
            </form>
          )
        ) : (
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-4 text-[var(--kp-warning-contrast)]">
            <p className="font-black uppercase">No tienes permiso para usar esta opción.</p>
            <p className="mt-2 font-bold">Pide ayuda al encargado.</p>
          </div>
        )}
      </div>
    </section>
  );
}

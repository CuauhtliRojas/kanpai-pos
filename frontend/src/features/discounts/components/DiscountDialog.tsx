import { useState } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { parsePesosToCents } from "../../../shared/lib/money";
import type { DiscountCreateRequest, DiscountType } from "../types/discountTypes";

type DiscountDialogProps = {
  employeeId: number;
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onApply: (payload: DiscountCreateRequest) => void;
};

export function DiscountDialog({ employeeId, isSaving, errorMessage, onClose, onApply }: DiscountDialogProps) {
  const [discountType, setDiscountType] = useState<DiscountType>("Monto");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const isAmount = discountType === "Monto";

  function buildPayload(): DiscountCreateRequest | null {
    const cleanReason = reason.trim();
    if (!cleanReason) return null;
    if (isAmount) {
      const amountCents = parsePesosToCents(value);
      if (amountCents === null || amountCents <= 0) return null;
      return { employee_id: employeeId, discount_type: discountType, amount_cents: amountCents, percent_bps: null, reason: cleanReason, is_courtesy: false };
    }
    const percent = Number(value);
    if (!Number.isFinite(percent) || percent <= 0 || percent > 100) return null;
    return {
      employee_id: employeeId,
      discount_type: discountType,
      amount_cents: null,
      percent_bps: Math.round(percent * 100),
      reason: cleanReason,
      is_courtesy: discountType === "Cortesia",
    };
  }

  const payload = buildPayload();
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="discount-title">
      <form
        className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
        onSubmit={(event) => { event.preventDefault(); if (payload) onApply(payload); }}
      >
        <header className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Autorizar descuento</p>
            <h2 id="discount-title" className="mt-1 text-2xl font-black uppercase">Descuento</h2>
          </div>
          <button type="button" aria-label="Cerrar" onClick={onClose} disabled={isSaving} className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50">
            <X className="h-6 w-6" />
          </button>
        </header>

        <div className="mt-4 grid gap-3">
          <label className="grid gap-2 font-black">
            Tipo
            <select value={discountType} onChange={(event) => { setDiscountType(event.target.value as DiscountType); setValue(""); }} disabled={isSaving} className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-3 font-bold">
              <option value="Monto">Monto</option>
              <option value="Porcentaje">Porcentaje</option>
              <option value="Cortesia">Cortesía</option>
            </select>
          </label>
          <label className="grid gap-2 font-black">
            {isAmount ? "Monto" : "Porcentaje"}
            <input value={value} onChange={(event) => setValue(event.target.value)} inputMode="decimal" disabled={isSaving} className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-3 font-bold" />
          </label>
          <label className="grid gap-2 font-black">
            Motivo
            <textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} disabled={isSaving} className="resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] p-3 font-bold" />
          </label>
        </div>
        {errorMessage ? <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p> : null}
        <BrutalButton type="submit" fullWidth disabled={isSaving || payload === null} className="mt-4">Aplicar</BrutalButton>
      </form>
    </div>
  );
}

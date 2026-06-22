import { useState } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos, parsePesosToCents } from "../../../shared/lib/money";
import type { DiscountCreateRequest, DiscountPreset, DiscountType } from "../types/discountTypes";

type DiscountDialogProps = {
  employeeId: number;
  subtotalCents: number;
  currentDiscountCents: number;
  presets: DiscountPreset[];
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onApply: (payload: DiscountCreateRequest) => void;
};

export function DiscountDialog({
  employeeId,
  subtotalCents,
  currentDiscountCents,
  presets,
  isSaving,
  errorMessage,
  onClose,
  onApply,
}: DiscountDialogProps) {
  const [discountType, setDiscountType] = useState<DiscountType>("Monto");
  const [value, setValue] = useState("");
  const [reason, setReason] = useState("");
  const isAmount = discountType === "Monto";
  const isCourtesy = discountType === "Cortesia";
  const availableCents = Math.max(0, subtotalCents - currentDiscountCents);

  const amountCents = isAmount ? parsePesosToCents(value) : null;
  const percent = discountType === "Porcentaje" ? Number(value) : isCourtesy ? 100 : null;
  const previewCents = isAmount
    ? amountCents
    : percent !== null && Number.isFinite(percent)
      ? Math.round(subtotalCents * percent / 100)
      : null;
  const exceedsSubtotal = previewCents !== null && previewCents > availableCents;

  function selectPreset(preset: DiscountPreset) {
    setDiscountType(preset.discount_type);
    if (preset.discount_type === "Monto") {
      setValue(String((preset.amount_cents ?? 0) / 100));
    } else if (preset.discount_type === "Porcentaje") {
      setValue(String((preset.percent_bps ?? 0) / 100));
    } else {
      setValue("");
    }
    setReason(preset.reason_template ?? "");
  }

  function presetDescription(preset: DiscountPreset): string {
    if (preset.discount_type === "Monto") {
      return `-${formatCentsToPesos(preset.amount_cents ?? 0)}`;
    }
    if (preset.discount_type === "Porcentaje") {
      return `${(preset.percent_bps ?? 0) / 100}%`;
    }
    return "Cortesía";
  }

  function buildPayload(): DiscountCreateRequest | null {
    const cleanReason = reason.trim();
    if (!cleanReason) return null;
    if (isAmount) {
      if (amountCents === null || amountCents <= 0) return null;
      if (amountCents > availableCents) return null;
      return { employee_id: employeeId, discount_type: discountType, amount_cents: amountCents, percent_bps: null, reason: cleanReason, is_courtesy: false };
    }
    if (percent === null || !Number.isFinite(percent) || percent <= 0 || percent > 100 || exceedsSubtotal) return null;
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
        className="max-h-[calc(100vh-2rem)] w-full max-w-lg overflow-y-auto border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
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
          {presets.length > 0 ? (
            <section>
              <p className="mb-2 font-black uppercase">Descuentos rápidos</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {presets.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    disabled={isSaving}
                    onClick={() => selectPreset(preset)}
                    className="min-h-16 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 text-left active:translate-x-[2px] active:translate-y-[2px]"
                  >
                    <span className="block font-black">{preset.name}</span>
                    <span className="block text-sm font-bold text-[var(--kp-muted)]">
                      {presetDescription(preset)}
                    </span>
                  </button>
                ))}
              </div>
            </section>
          ) : null}
          <div className="grid grid-cols-3 gap-2" role="group" aria-label="Tipo de descuento">
            {(["Monto", "Porcentaje", "Cortesia"] as const).map((type) => (
              <button
                key={type}
                type="button"
                aria-pressed={discountType === type}
                disabled={isSaving}
                onClick={() => { setDiscountType(type); setValue(""); }}
                className={`min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] px-2 text-sm font-black uppercase ${discountType === type ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]" : "bg-[var(--kp-surface-raised)]"}`}
              >
                {type === "Cortesia" ? "Cortesía" : type}
              </button>
            ))}
          </div>
          {!isCourtesy ? (
            <label className="grid gap-2 font-black">
              {isAmount ? "¿Cuánto descontar?" : "¿Qué porcentaje?"}
              <div className="flex min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)]">
                <span className="flex items-center px-3 text-lg font-black">{isAmount ? "$" : "%"}</span>
                <input
                  value={value}
                  onChange={(event) => setValue(event.target.value)}
                  inputMode="decimal"
                  disabled={isSaving}
                  className="min-w-0 flex-1 bg-transparent px-2 font-bold outline-none"
                />
              </div>
            </label>
          ) : null}
          <label className="grid gap-2 font-black">
            Motivo
            <textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={2} disabled={isSaving} className="resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] p-3 font-bold" />
          </label>
        </div>
        {previewCents !== null && previewCents > 0 ? (
          <div className={`mt-3 border-4 border-[var(--kp-ink)] p-3 ${exceedsSubtotal ? "bg-[var(--kp-danger-bg)] text-[var(--kp-danger-text)]" : "bg-[var(--kp-bg-alt)]"}`}>
            <p className="text-sm font-bold">Se descontará</p>
            <p className="text-2xl font-black">{formatCentsToPesos(previewCents)}</p>
            {exceedsSubtotal ? <p className="mt-1 font-bold">El descuento excede el subtotal disponible.</p> : null}
          </div>
        ) : null}
        {errorMessage ? <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p> : null}
        <BrutalButton type="submit" variant="primary" fullWidth disabled={isSaving || payload === null} className="mt-4">
          {isSaving ? "Aplicando..." : "Aplicar descuento"}
        </BrutalButton>
      </form>
    </div>
  );
}

import { Minus, Plus } from "lucide-react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { VariantGroup } from "../types/variantTypes";

type Props = {
  group: VariantGroup;
  quantities: Record<number, number>;
  disabled: boolean;
  onChange: (optionId: number, quantity: number) => void;
};

export function VariantGroupSelector({ group, quantities, disabled, onChange }: Props) {
  const options = group.options.filter((option) => option.active);
  const selectedCount = options.reduce((total, option) => total + (quantities[option.id] ?? 0), 0);

  return (
    <fieldset className="border-4 border-[var(--kp-ink)] px-2 pb-2 pt-1" disabled={disabled}>
      <legend className="px-2 font-black uppercase">{group.name}</legend>
      <p className="mb-2 text-xs font-bold text-[var(--kp-text-muted)]">
        Elige {group.min_select === group.max_select ? group.min_select : `${group.min_select} a ${group.max_select}`}
      </p>
      {options.length === 0 ? (
        <p className="font-black uppercase text-[var(--kp-muted)]">Sin opciones</p>
      ) : (
        <div className="grid gap-1.5 sm:grid-cols-2">
          {options.map((option) => {
            const quantity = quantities[option.id] ?? 0;
            return (
              <div key={option.id} className="flex min-h-12 items-center justify-between gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1">
                <div className="min-w-0">
                  <p className="truncate text-sm font-black" title={option.name}>{option.name}</p>
                  {option.price_delta_cents !== 0 ? (
                    <p className="text-xs font-bold text-[var(--kp-text-muted)]">
                      {option.price_delta_cents > 0 ? "+" : ""}{formatCentsToPesos(option.price_delta_cents)}
                    </p>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <button type="button" aria-label={`Quitar ${option.name}`} disabled={quantity === 0} onClick={() => onChange(option.id, quantity - 1)} className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"><Minus className="h-4 w-4" /></button>
                  <span className="w-5 text-center font-black">{quantity}</span>
                  <button type="button" aria-label={`Agregar ${option.name}`} disabled={selectedCount >= group.max_select} onClick={() => onChange(option.id, quantity + 1)} className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"><Plus className="h-4 w-4" /></button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

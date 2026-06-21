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
    <fieldset className="border-4 border-[var(--kp-ink)] p-3" disabled={disabled}>
      <legend className="px-2 font-black uppercase">{group.name}</legend>
      <p className="mb-3 text-sm font-bold text-[var(--kp-text-muted)]">
        Elige {group.min_select === group.max_select ? group.min_select : `${group.min_select} a ${group.max_select}`}
      </p>
      {options.length === 0 ? (
        <p className="font-black uppercase text-[var(--kp-muted)]">Sin opciones</p>
      ) : (
        <div className="grid gap-2">
          {options.map((option) => {
            const quantity = quantities[option.id] ?? 0;
            return (
              <div key={option.id} className="flex items-center justify-between gap-3 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2">
                <div>
                  <p className="font-black">{option.name}</p>
                  {option.price_delta_cents !== 0 ? (
                    <p className="text-sm font-bold text-[var(--kp-text-muted)]">
                      {option.price_delta_cents > 0 ? "+" : ""}{formatCentsToPesos(option.price_delta_cents)}
                    </p>
                  ) : null}
                </div>
                <div className="flex items-center gap-2">
                  <button type="button" aria-label={`Quitar ${option.name}`} disabled={quantity === 0} onClick={() => onChange(option.id, quantity - 1)} className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"><Minus className="h-5 w-5" /></button>
                  <span className="w-6 text-center font-black">{quantity}</span>
                  <button type="button" aria-label={`Agregar ${option.name}`} disabled={selectedCount >= group.max_select} onClick={() => onChange(option.id, quantity + 1)} className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"><Plus className="h-5 w-5" /></button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

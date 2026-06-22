import { Check, Minus, Plus } from "lucide-react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { VariantGroup } from "../types/variantTypes";

type Props = {
  group: VariantGroup;
  quantities: Record<number, number>;
  disabled: boolean;
  onChange: (optionId: number, quantity: number) => void;
};

const KNOWN_SHORT_LABELS: Record<string, string> = {
  pollo: "Pollo",
  "pork belly": "Pork belly",
  pulpo: "Pulpo",
  camaron: "Camarón",
  camarón: "Camarón",
  verduras: "Verduras",
  hongos: "Hongos",
};

function toReadableLabel(value: string): string {
  const cleaned = value.trim().replace(/\s+/g, " ");
  const known = KNOWN_SHORT_LABELS[cleaned.toLowerCase()];
  if (known) return known;

  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function getVariantOptionDisplayName(groupName: string, optionName: string): string {
  const group = groupName.trim().toUpperCase();
  const original = optionName.trim();

  if (group.includes("BROCHETA")) {
    const withoutPrefix = original
      .replace(/^brochetas?\s+de\s+/i, "")
      .replace(/^brochetas?\s+/i, "")
      .trim();

    return toReadableLabel(withoutPrefix || original);
  }

  return original;
}

export function VariantGroupSelector({ group, quantities, disabled, onChange }: Props) {
  const options = group.options.filter((option) => option.active);
  const selectedCount = options.reduce((total, option) => total + (quantities[option.id] ?? 0), 0);
  const isSingleSelection = group.min_select === 1 && group.max_select === 1;

  function selectOnly(optionId: number) {
    for (const option of options) {
      onChange(option.id, option.id === optionId ? 1 : 0);
    }
  }

  return (
    <fieldset className="border-4 border-[var(--kp-ink)] px-2 pb-2 pt-1" disabled={disabled}>
      <legend className="px-2 font-black uppercase">{group.name}</legend>
      <p className="mb-2 text-xs font-bold text-[var(--kp-text-muted)]">
        Elige {group.min_select === group.max_select ? group.min_select : `${group.min_select} a ${group.max_select}`}
      </p>
      {options.length === 0 ? (
        <p className="font-black uppercase text-[var(--kp-muted)]">Sin opciones</p>
      ) : isSingleSelection ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {options.map((option) => {
            const selected = (quantities[option.id] ?? 0) === 1;
            const displayName = getVariantOptionDisplayName(group.name, option.name);
            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={selected}
                onClick={() => selectOnly(option.id)}
                className={`flex min-h-14 items-center justify-between gap-3 border-4 border-[var(--kp-ink)] px-3 py-2 text-left font-black active:translate-x-[2px] active:translate-y-[2px] ${
                  selected
                    ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
                    : "bg-[var(--kp-surface-raised)]"
                }`}
              >
                <span>
                  {displayName}
                  {option.price_delta_cents !== 0 ? (
                    <span className="ml-2 text-xs">
                      {option.price_delta_cents > 0 ? "+" : ""}
                      {formatCentsToPesos(option.price_delta_cents)}
                    </span>
                  ) : null}
                </span>
                {selected ? (
                  <span className="flex items-center gap-1 text-xs uppercase">
                    <Check className="h-5 w-5" /> Elegido
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : (
        <div className="grid gap-1.5 sm:grid-cols-2">
          {options.map((option) => {
            const quantity = quantities[option.id] ?? 0;
            const displayName = getVariantOptionDisplayName(group.name, option.name);

            return (
              <div
                key={option.id}
                className="flex min-h-12 items-center justify-between gap-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-black leading-tight" title={option.name}>
                    {displayName}
                  </p>
                  {option.price_delta_cents !== 0 ? (
                    <p className="text-xs font-bold text-[var(--kp-text-muted)]">
                      {option.price_delta_cents > 0 ? "+" : ""}
                      {formatCentsToPesos(option.price_delta_cents)}
                    </p>
                  ) : null}
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    type="button"
                    aria-label={`Quitar ${option.name}`}
                    disabled={quantity === 0}
                    onClick={() => onChange(option.id, quantity - 1)}
                    className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-5 text-center font-black">{quantity}</span>
                  <button
                    type="button"
                    aria-label={`Agregar ${option.name}`}
                    disabled={selectedCount >= group.max_select}
                    onClick={() => onChange(option.id, quantity + 1)}
                    className="flex h-10 w-10 items-center justify-center border-2 border-[var(--kp-ink)] disabled:opacity-40"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

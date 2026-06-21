import { useMemo, useState } from "react";
import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { Product } from "../../products/types/productTypes";
import type { VariantGroup, VariantSelection } from "../types/variantTypes";
import { VariantGroupSelector } from "./VariantGroupSelector";

type Props = {
  product: Product;
  groups: VariantGroup[];
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onSubmit: (selections: VariantSelection[]) => void;
};

export function ProductVariantDialog({ product, groups, isSaving, errorMessage, onClose, onSubmit }: Props) {
  const activeGroups = useMemo(() => groups.filter((group) => group.active), [groups]);
  const [quantities, setQuantities] = useState<Record<number, number>>({});
  const valid = activeGroups.every((group) => {
    const count = group.options.reduce((total, option) => total + (quantities[option.id] ?? 0), 0);
    return count >= group.min_select && count <= group.max_select && (group.min_select === 0 || group.options.some((option) => option.active));
  });

  function submit() {
    if (!valid) return;
    const selections = activeGroups.flatMap((group) =>
      group.options.flatMap((option) => {
        const quantity = quantities[option.id] ?? 0;
        return quantity > 0 ? [{ variant_group_id: group.id, variant_option_id: option.id, quantity }] : [];
      }),
    );
    onSubmit(selections);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="variant-dialog-title">
      <section className="max-h-[90vh] w-full max-w-lg overflow-y-auto border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="flex items-start justify-between gap-3">
          <div><p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Elige una opción</p><h2 id="variant-dialog-title" className="mt-1 text-2xl font-black uppercase">{product.display_name || product.name}</h2></div>
          <button type="button" aria-label="Cerrar" onClick={onClose} disabled={isSaving} className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)]"><X className="h-6 w-6" /></button>
        </header>
        <div className="mt-4 grid gap-4">
          {activeGroups.map((group) => <VariantGroupSelector key={group.id} group={group} quantities={quantities} disabled={isSaving} onChange={(optionId, quantity) => setQuantities((current) => ({ ...current, [optionId]: quantity }))} />)}
        </div>
        {errorMessage ? <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p> : null}
        <BrutalButton type="button" variant="primary" fullWidth disabled={!valid || isSaving} onClick={submit} className="mt-4">{isSaving ? "Agregando..." : "Agregar a cuenta"}</BrutalButton>
      </section>
    </div>
  );
}

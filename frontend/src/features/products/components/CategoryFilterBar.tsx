import type { ProductCategory } from "../types/productTypes";

type CategoryFilterBarProps = {
  categories: ProductCategory[];
  selectedCategoryId: number | null;
  onSelect: (categoryId: number | null) => void;
};

export function CategoryFilterBar({
  categories,
  selectedCategoryId,
  onSelect,
}: CategoryFilterBarProps) {
  const items = [{ id: null, name: "Todo" }, ...categories];

  return (
    <div className="flex gap-2 overflow-x-auto pb-2" aria-label="Categorías">
      {items.map((category) => {
        const selected = category.id === selectedCategoryId;
        return (
          <button
            key={category.id ?? "all"}
            type="button"
            aria-pressed={selected}
            onClick={() => onSelect(category.id)}
            className={[
              "min-h-[var(--kp-touch-md)] shrink-0 border-4 border-[var(--kp-ink)] px-4 text-sm font-black uppercase shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none",
              selected
                ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
                : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
            ].join(" ")}
          >
            {category.name}
          </button>
        );
      })}
    </div>
  );
}

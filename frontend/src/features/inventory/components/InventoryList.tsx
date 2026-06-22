import type { InventoryItem } from "../types/inventoryTypes";
import { InventoryItemCard } from "./InventoryItemCard";

type Props = {
  items: InventoryItem[];
  canAdjust: boolean;
  onAdjust: (item: InventoryItem) => void;
  isFiltered?: boolean;
  onViewMovements?: (item: InventoryItem) => void;
};

export function InventoryList({
  items,
  canAdjust,
  onAdjust,
  isFiltered = false,
  onViewMovements,
}: Props) {
  if (items.length === 0) {
    return (
      <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 text-center font-black uppercase text-[var(--kp-muted)] shadow-[var(--kp-shadow-hard)]">
        {isFiltered
          ? "No hay resultados con estos filtros."
          : "Sin datos de inventario."}
      </p>
    );
  }
  return (
    <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <li key={item.id}>
          <InventoryItemCard
            item={item}
            onAdjust={canAdjust ? onAdjust : undefined}
            onViewMovements={onViewMovements}
          />
        </li>
      ))}
    </ul>
  );
}

import type { InventoryConsumptionItem } from "../types/reportTypes";
import { ReportCard } from "./ReportCard";

export function InventoryConsumptionPanel({ items }: { items: InventoryConsumptionItem[] }) {
  return (
    <ReportCard title="Consumo de inventario">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-2">
          {items.map((item) => (
            <div key={item.inventory_item_id} className="flex items-start justify-between gap-4 border-t-2 border-zinc-700 pt-2 first:border-t-0 first:pt-0">
              <div>
                <p className="font-black">{item.name}</p>
                <p className="text-sm font-bold text-[var(--kp-muted)]">{item.movement_count} movimientos</p>
              </div>
              <p className="shrink-0 font-black">{item.total_quantity_base} {item.base_unit_name}</p>
            </div>
          ))}
        </div>
      )}
    </ReportCard>
  );
}

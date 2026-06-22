import { useState, useMemo } from "react";
import { RefreshCw, X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { InventoryItem, InventoryMovementHistoryParams } from "../types/inventoryTypes";
import { useInventoryMovementsQuery } from "../hooks/useInventoryMovementsQuery";
import { InventoryMovementRow } from "./InventoryMovementRow";

const MOVEMENT_TYPES = [
  "Compra",
  "Ajuste entrada",
  "Ajuste salida",
  "Merma",
  "Consumo venta",
] as const;

type Props = {
  items: InventoryItem[];
  initialItemId?: number;
  onClose: () => void;
};

export function InventoryMovementHistoryDialog({
  items,
  initialItemId,
  onClose,
}: Props) {
  const activeItems = items.filter((i) => i.active);
  const itemById = useMemo(
    () => new Map(items.map((i) => [i.id, i])),
    [items],
  );

  const [filterItemId, setFilterItemId] = useState<string>(
    initialItemId !== undefined ? String(initialItemId) : "",
  );
  const [filterType, setFilterType] = useState("");
  const [filterFrom, setFilterFrom] = useState("");
  const [filterTo, setFilterTo] = useState("");

  const params = useMemo(
    (): InventoryMovementHistoryParams => ({
      inventory_item_id:
        filterItemId !== "" ? Number(filterItemId) : undefined,
      movement_type: filterType || undefined,
      created_from: filterFrom || undefined,
      created_to: filterTo || undefined,
      limit: 100,
    }),
    [filterItemId, filterType, filterFrom, filterTo],
  );

  const movementsQuery = useInventoryMovementsQuery(params);

  const currentItem =
    filterItemId !== "" ? itemById.get(Number(filterItemId)) : undefined;
  const isItemMode = initialItemId !== undefined;
  const showItemName = filterItemId === "";
  const movements = movementsQuery.data ?? [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="hist-dialog-title"
    >
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]">
        {/* Header */}
        <div className="flex shrink-0 items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] p-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Inventario
            </p>
            <h2
              id="hist-dialog-title"
              className="mt-0.5 text-xl font-black uppercase"
            >
              Movimientos de inventario
            </h2>
            {currentItem && (
              <p className="mt-0.5 text-sm font-bold text-[var(--kp-muted)]">
                {currentItem.name} — {currentItem.sku}
              </p>
            )}
            {!isItemMode && !currentItem && (
              <p className="mt-0.5 text-sm font-bold text-[var(--kp-muted)]">
                Todos los insumos
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              aria-label="Actualizar"
              onClick={() => void movementsQuery.refetch()}
              disabled={movementsQuery.isFetching}
              className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50 hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
            >
              <RefreshCw
                className={`h-5 w-5 ${movementsQuery.isFetching ? "animate-spin" : ""}`}
              />
            </button>
            <button
              type="button"
              aria-label="Cerrar"
              onClick={onClose}
              className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Filtros */}
        <div className="shrink-0 border-b-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-4 py-3">
          <div
            className={`grid gap-3 ${
              isItemMode
                ? "sm:grid-cols-3"
                : "sm:grid-cols-2 lg:grid-cols-4"
            }`}
          >
            {!isItemMode && (
              <div>
                <label
                  htmlFor="hist-item"
                  className="block text-xs font-black uppercase tracking-[0.08em]"
                >
                  Insumo
                </label>
                <select
                  id="hist-item"
                  value={filterItemId}
                  onChange={(e) => setFilterItemId(e.target.value)}
                  className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)]"
                >
                  <option value="">Todos los insumos</option>
                  {activeItems.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label
                htmlFor="hist-type"
                className="block text-xs font-black uppercase tracking-[0.08em]"
              >
                Tipo
              </label>
              <select
                id="hist-type"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)]"
              >
                <option value="">Todos los tipos</option>
                {MOVEMENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor="hist-from"
                className="block text-xs font-black uppercase tracking-[0.08em]"
              >
                Desde
              </label>
              <input
                id="hist-from"
                type="date"
                value={filterFrom}
                onChange={(e) => setFilterFrom(e.target.value)}
                className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)]"
              />
            </div>
            <div>
              <label
                htmlFor="hist-to"
                className="block text-xs font-black uppercase tracking-[0.08em]"
              >
                Hasta
              </label>
              <input
                id="hist-to"
                type="date"
                value={filterTo}
                onChange={(e) => setFilterTo(e.target.value)}
                className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)]"
              />
            </div>
          </div>
        </div>

        {/* Cuerpo */}
        <div className="flex-1 overflow-y-auto">
          {movementsQuery.isPending && (
            <p className="p-8 text-center font-bold text-[var(--kp-muted)]">
              Cargando movimientos...
            </p>
          )}

          {movementsQuery.isError && (
            <div className="p-8 text-center">
              <p className="font-black uppercase text-[var(--kp-danger)]">
                No se pudo cargar el historial.
              </p>
              <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
                Intenta de nuevo.
              </p>
              <BrutalButton
                size="sm"
                onClick={() => void movementsQuery.refetch()}
                className="mt-4"
              >
                <RefreshCw className="h-4 w-4" /> Reintentar
              </BrutalButton>
            </div>
          )}

          {!movementsQuery.isPending &&
            !movementsQuery.isError &&
            movements.length === 0 && (
              <p className="p-8 text-center font-bold text-[var(--kp-muted)]">
                No hay movimientos con estos filtros.
              </p>
            )}

          {movements.length > 0 && (
            <>
              {movements.map((movement) => (
                <InventoryMovementRow
                  key={movement.id}
                  movement={movement}
                  item={itemById.get(movement.inventory_item_id)}
                  showItemName={showItemName}
                />
              ))}
              {movements.length >= 100 && (
                <p className="border-t-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-4 py-3 text-xs font-bold text-[var(--kp-muted)]">
                  Mostrando los últimos 100 movimientos. Ajusta los filtros para
                  ver un rango más específico.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

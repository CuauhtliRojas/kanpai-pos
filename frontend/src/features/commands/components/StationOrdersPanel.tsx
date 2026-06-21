import { useMemo } from "react";
import { useProductionStationsQuery } from "../hooks/useProductionStationsQuery";
import { useStationOrdersQuery } from "../hooks/useStationOrdersQuery";
import type { StationOrder } from "../types/commandTypes";
import { StationOrderGroup } from "./StationOrderGroup";

export function StationOrdersPanel({ ticketId }: { ticketId: number | null }) {
  const ordersQuery = useStationOrdersQuery(ticketId);
  const stationsQuery = useProductionStationsQuery(ticketId !== null);
  const stationNames = useMemo(
    () => new Map((stationsQuery.data ?? []).map((station) => [station.id, station.name])),
    [stationsQuery.data],
  );
  const groupedOrders = useMemo(() => {
    const groups = new Map<number, StationOrder[]>();
    for (const order of ordersQuery.data ?? []) {
      const stationOrders = groups.get(order.station_id) ?? [];
      stationOrders.push(order);
      groups.set(order.station_id, stationOrders);
    }
    return [...groups.entries()];
  }, [ordersQuery.data]);

  if (ticketId === null) return null;

  return (
    <aside className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <h2 className="text-xl font-black uppercase">Comandas</h2>

      {ordersQuery.isPending || stationsQuery.isPending ? (
        <p className="mt-3 font-bold">Consultando comandas...</p>
      ) : ordersQuery.isError || stationsQuery.isError ? (
        <p className="mt-3 font-bold">No se pudieron cargar las comandas.</p>
      ) : groupedOrders.length === 0 ? (
        <p className="mt-3 font-bold text-[var(--kp-muted)]">Sin comandas</p>
      ) : (
        <div className="mt-3 grid gap-4">
          {groupedOrders.map(([stationId, orders]) => (
            <StationOrderGroup
              key={stationId}
              stationName={stationNames.get(stationId) ?? "Estación"}
              orders={orders}
            />
          ))}
        </div>
      )}
    </aside>
  );
}

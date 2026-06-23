import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { ProductionOrderGrid } from "../components/ProductionOrderGrid";
import { ProductionStationTabs } from "../components/ProductionStationTabs";
import { ProductionSummaryBar } from "../components/ProductionSummaryBar";
import { ProductionViewFilters } from "../components/ProductionViewFilters";
import { useAcceptProductionOrderMutation } from "../hooks/useAcceptProductionOrderMutation";
import { useDeliverProductionOrderMutation } from "../hooks/useDeliverProductionOrderMutation";
import { useFinishProductionOrderMutation } from "../hooks/useFinishProductionOrderMutation";
import {
  filterProductionOrders,
  formatProductionLastUpdated,
  sortProductionOrders,
  type ProductionViewFilter,
} from "../productionFormatters";
import { useProductionOrdersQuery } from "../hooks/useProductionOrdersQuery";
import { useProductionStationsQuery } from "../hooks/useProductionStationsQuery";
import { useStartProductionOrderMutation } from "../hooks/useStartProductionOrderMutation";
import type { ProductionOrder, ProductionOrderStatus } from "../types/productionTypes";

function getProductionErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 409) {
    return "La comanda cambió. Actualiza para continuar.";
  }
  return "No se pudo actualizar la comanda. Intenta de nuevo.";
}

export function ProductionPage() {
  const { employee } = useAuthSession();
  const [selectedStationId, setSelectedStationId] = useState<number>();
  const [activeOrderId, setActiveOrderId] = useState<number | null>(null);
  const [viewFilter, setViewFilter] = useState<ProductionViewFilter>("active");
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const stationsQuery = useProductionStationsQuery();
  const stations = useMemo(
    () => (stationsQuery.data ?? []).filter((station) => station.active),
    [stationsQuery.data],
  );

  useEffect(() => {
    if (stations.length > 0 && !stations.some((station) => station.id === selectedStationId)) {
      setSelectedStationId(stations[0].id);
    }
  }, [selectedStationId, stations]);

  const ordersQuery = useProductionOrdersQuery(selectedStationId);
  const acceptMutation = useAcceptProductionOrderMutation();
  const startMutation = useStartProductionOrderMutation();
  const finishMutation = useFinishProductionOrderMutation();
  const deliverMutation = useDeliverProductionOrderMutation();

  const orders = ordersQuery.data ?? [];
  const visibleOrders = useMemo(
    () => sortProductionOrders(filterProductionOrders(orders, viewFilter)),
    [orders, viewFilter],
  );
  const isUpdating = stationsQuery.isFetching || ordersQuery.isFetching;

  useEffect(() => {
    const updatedAt = Math.max(stationsQuery.dataUpdatedAt, ordersQuery.dataUpdatedAt);
    if (updatedAt > 0) setLastUpdatedAt(new Date(updatedAt));
  }, [ordersQuery.dataUpdatedAt, stationsQuery.dataUpdatedAt]);

  function getOrderMutationState(status: ProductionOrderStatus) {
    const mutation = status === "En cola"
      ? acceptMutation
      : status === "Recibida"
        ? startMutation
        : status === "En preparacion"
          ? finishMutation
          : status === "Terminada"
            ? deliverMutation
            : null;
    return mutation ? { isPending: mutation.isPending, error: mutation.error } : null;
  }

  async function runAction(
    mutation: typeof acceptMutation,
    orderId: number,
    stationId: number,
  ) {
    if (!employee) return;
    setActiveOrderId(orderId);
    try {
      await mutation.mutateAsync({ orderId, stationId, employeeId: employee.id });
    } catch {
      // El mensaje operativo se muestra en la tarjeta.
    }
  }

  function resetActionState() {
    setActiveOrderId(null);
    acceptMutation.reset();
    startMutation.reset();
    finishMutation.reset();
    deliverMutation.reset();
  }

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Operación</p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Producción</h1>
          <p className="mt-2 max-w-2xl font-bold text-[var(--kp-muted)]">
            Controla comandas activas por cocina y barra.
          </p>
          <p className="mt-2 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            {isUpdating ? "Actualizando..." : `Última actualización: ${formatProductionLastUpdated(lastUpdatedAt)}`}
          </p>
        </div>
        <BrutalButton
          onClick={() => void Promise.all([
            stationsQuery.refetch(),
            selectedStationId === undefined ? Promise.resolve() : ordersQuery.refetch(),
          ])}
          disabled={isUpdating}
        >
          <RefreshCw className="h-5 w-5" /> {isUpdating ? "Actualizando..." : "Actualizar"}
        </BrutalButton>
      </header>

      {stationsQuery.isPending ? <LoadingState /> : null}
      {stationsQuery.isError ? (
        <ErrorState title="No se pudo cargar Producción" message="Intenta de nuevo." />
      ) : null}
      {!stationsQuery.isPending && !stationsQuery.isError ? (
        <>
          <ProductionStationTabs
            stations={stations}
            selectedStationId={selectedStationId}
            onSelect={(stationId) => {
              setSelectedStationId(stationId);
              resetActionState();
            }}
          />
          {stations.length === 0 ? (
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center text-xl font-black uppercase shadow-[var(--kp-shadow-hard)]">
              Sin estaciones disponibles
            </div>
          ) : ordersQuery.isPending ? (
            <LoadingState />
          ) : ordersQuery.isError ? (
            <ErrorState title="No se pudieron cargar las comandas" message="Intenta de nuevo." />
          ) : (
            <div className="grid gap-4">
              <ProductionSummaryBar
                orders={orders}
                activeFilter={viewFilter}
                onFilterSelect={(value) => {
                  setViewFilter(value);
                  resetActionState();
                }}
              />
              <ProductionViewFilters
                value={viewFilter}
                onChange={(value) => {
                  setViewFilter(value);
                  resetActionState();
                }}
              />
              <ProductionOrderGrid
                orders={visibleOrders}
                filter={viewFilter}
                stationId={selectedStationId}
                activeOrderId={activeOrderId}
                isOrderPending={(order: ProductionOrder) => {
                  const mutationState = getOrderMutationState(order.status);
                  return Boolean(activeOrderId === order.id && mutationState?.isPending);
                }}
                getErrorMessage={(order: ProductionOrder) => {
                  const mutationState = getOrderMutationState(order.status);
                  return getProductionErrorMessage(mutationState?.error);
                }}
                onAccept={(order) => void runAction(acceptMutation, order.id, order.station_id)}
                onStart={(order) => void runAction(startMutation, order.id, order.station_id)}
                onFinish={(order) => void runAction(finishMutation, order.id, order.station_id)}
                onDeliver={(order) => void runAction(deliverMutation, order.id, order.station_id)}
              />
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

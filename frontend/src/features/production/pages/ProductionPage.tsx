import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { ProductionOrderCard } from "../components/ProductionOrderCard";
import { ProductionStationTabs } from "../components/ProductionStationTabs";
import { useAcceptProductionOrderMutation } from "../hooks/useAcceptProductionOrderMutation";
import { useDeliverProductionOrderMutation } from "../hooks/useDeliverProductionOrderMutation";
import { useFinishProductionOrderMutation } from "../hooks/useFinishProductionOrderMutation";
import { useProductionOrdersQuery } from "../hooks/useProductionOrdersQuery";
import { useProductionStationsQuery } from "../hooks/useProductionStationsQuery";
import { useStartProductionOrderMutation } from "../hooks/useStartProductionOrderMutation";

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

  function getOrderMutationState(status: string) {
    const mutation = status === "En cola"
      ? acceptMutation
      : status === "Recibida"
        ? startMutation
        : status === "En preparacion"
          ? finishMutation
          : deliverMutation;
    return { isPending: mutation.isPending, error: mutation.error };
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

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Operación</p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Producción</h1>
        </div>
        <BrutalButton
          onClick={() => void Promise.all([
            stationsQuery.refetch(),
            selectedStationId === undefined ? Promise.resolve() : ordersQuery.refetch(),
          ])}
          disabled={stationsQuery.isFetching || ordersQuery.isFetching}
        >
          <RefreshCw className="h-5 w-5" /> Actualizar
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
              setActiveOrderId(null);
              acceptMutation.reset();
              startMutation.reset();
              finishMutation.reset();
              deliverMutation.reset();
            }}
          />
          {stations.length === 0 ? (
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center text-xl font-black uppercase shadow-[var(--kp-shadow-hard)]">
              Sin comandas
            </div>
          ) : ordersQuery.isPending ? (
            <LoadingState />
          ) : ordersQuery.isError ? (
            <ErrorState title="No se pudieron cargar las comandas" message="Intenta de nuevo." />
          ) : (ordersQuery.data ?? []).length === 0 ? (
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center text-xl font-black uppercase shadow-[var(--kp-shadow-hard)]">
              Sin comandas
            </div>
          ) : (
            <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
              {(ordersQuery.data ?? []).map((order) => {
                const mutationState = getOrderMutationState(order.status);
                return (
                  <ProductionOrderCard
                    key={order.id}
                    order={order}
                    isPending={activeOrderId === order.id && mutationState.isPending}
                    errorMessage={activeOrderId === order.id ? getProductionErrorMessage(mutationState.error) : null}
                    onAccept={() => void runAction(acceptMutation, order.id, order.station_id)}
                    onStart={() => void runAction(startMutation, order.id, order.station_id)}
                    onFinish={() => void runAction(finishMutation, order.id, order.station_id)}
                    onDeliver={() => void runAction(deliverMutation, order.id, order.station_id)}
                  />
                );
              })}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

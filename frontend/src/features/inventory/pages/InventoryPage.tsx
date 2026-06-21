import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasPermission } from "../../auth/lib/permissions";
import { useInventoryItemsQuery } from "../hooks/useInventoryItemsQuery";
import { useStockAlertsQuery } from "../hooks/useStockAlertsQuery";
import { useInventoryMovementMutation } from "../hooks/useInventoryMovementMutation";
import { LowStockPanel } from "../components/LowStockPanel";
import { InventoryList } from "../components/InventoryList";
import { InventoryAdjustmentDialog } from "../components/InventoryAdjustmentDialog";
import type { InventoryItem, InventoryMovementCreateRequest } from "../types/inventoryTypes";
import { usePaymentMethodsQuery } from "../../payments/hooks/usePaymentMethodsQuery";
import { PurchaseReceiptDialog } from "../../purchases/components/PurchaseReceiptDialog";
import { usePurchaseReceiptMutation } from "../../purchases/hooks/usePurchaseReceiptMutation";

export function InventoryPage() {
  const { permissions, employee } = useAuthSession();
  const canAdjust = hasPermission(permissions, "INVENTORY_ADJUST");
  const canRegisterExpense = hasPermission(permissions, "EXPENSE_CREATE");

  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [purchaseOpen, setPurchaseOpen] = useState(false);
  const [purchaseMessage, setPurchaseMessage] = useState<string | null>(null);

  const itemsQuery = useInventoryItemsQuery();
  const alertsQuery = useStockAlertsQuery();
  const movementMutation = useInventoryMovementMutation();
  const purchaseMutation = usePurchaseReceiptMutation();
  const paymentMethodsQuery = usePaymentMethodsQuery(purchaseOpen && canRegisterExpense);

  function handleAdjustRequest(item: InventoryItem) {
    setAdjustError(null);
    movementMutation.reset();
    setSelectedItem(item);
  }

  function handleDialogClose() {
    setSelectedItem(null);
    setAdjustError(null);
    movementMutation.reset();
  }

  async function handleAdjustSubmit(payload: InventoryMovementCreateRequest) {
    setAdjustError(null);
    try {
      await movementMutation.mutateAsync(payload);
      setSelectedItem(null);
    } catch (error) {
      setAdjustError(error instanceof Error ? error.message : "Intenta de nuevo.");
    }
  }

  const isLoading = itemsQuery.isPending || alertsQuery.isPending;
  const isError = itemsQuery.isError || alertsQuery.isError;

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
            Existencias
          </p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Inventario</h1>
        </div>
        <div className="flex flex-wrap gap-3">
          {canAdjust ? <BrutalButton variant="primary" onClick={() => { setPurchaseMessage(null); setPurchaseOpen(true); }}>Recibir compra</BrutalButton> : null}
          <BrutalButton
            onClick={() => {
              void itemsQuery.refetch();
              void alertsQuery.refetch();
            }}
            disabled={itemsQuery.isFetching || alertsQuery.isFetching}
          >
            <RefreshCw className="h-5 w-5" /> Actualizar
          </BrutalButton>
        </div>
      </header>

      {!canAdjust && (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 text-sm font-bold">
          Solo lectura. Pide ayuda al encargado para ajustar inventario.
        </p>
      )}
      {purchaseMessage ? <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 font-black text-[var(--kp-success-text)]">{purchaseMessage}</p> : null}

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState title="No se pudo cargar Inventario" message="Intenta de nuevo." />
      ) : (
        <>
          <LowStockPanel alerts={alertsQuery.data ?? []} />
          <InventoryList
            items={itemsQuery.data ?? []}
            canAdjust={canAdjust}
            onAdjust={handleAdjustRequest}
          />
        </>
      )}

      {selectedItem !== null && employee !== null && (
        <InventoryAdjustmentDialog
          item={selectedItem}
          employeeId={employee.id}
          isSaving={movementMutation.isPending}
          errorMessage={adjustError}
          onClose={handleDialogClose}
          onSubmit={(payload) => {
            void handleAdjustSubmit(payload);
          }}
        />
      )}
      {purchaseOpen && employee !== null ? (
        <PurchaseReceiptDialog
          employeeId={employee.id}
          items={itemsQuery.data ?? []}
          methods={paymentMethodsQuery.data ?? []}
          canRegisterExpense={canRegisterExpense}
          isSaving={purchaseMutation.isPending}
          errorMessage={purchaseMutation.isError ? "No se pudo registrar la recepción. Revisa los datos e intenta de nuevo." : null}
          onClose={() => { purchaseMutation.reset(); setPurchaseOpen(false); }}
          onSubmit={(payload) => void purchaseMutation.mutateAsync(payload).then((result) => { setPurchaseMessage(`Recepción ${result.folio} registrada.`); setPurchaseOpen(false); }).catch(() => undefined)}
        />
      ) : null}
    </div>
  );
}

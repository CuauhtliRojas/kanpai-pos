import { useState, useMemo } from "react";
import { RefreshCw, Search } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { ApiError } from "../../../api/http";
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

type FilterStatus = "all" | "agotado" | "bajo" | "correcto";

function getApiDetailText(details: unknown): string | null {
  if (typeof details === "string") return details;

  if (details !== null && typeof details === "object" && "detail" in details) {
    const detail = (details as { detail?: unknown }).detail;
    return typeof detail === "string" ? detail : null;
  }

  return null;
}

function getPurchaseReceiptErrorMessage(error: unknown): string {
  const prefix = "No se pudo registrar la recepción.";

  if (error instanceof ApiError) {
    const detail = getApiDetailText(error.details);

    if (detail) {
      if (detail.includes("corte de caja abierto")) {
        return `${prefix} Para registrar pago necesitas una caja abierta. Abre caja o deja monto pagado en 0 para registrar sólo la entrada de almacén.`;
      }

      return `${prefix} ${detail}`;
    }
  }

  if (error instanceof Error && error.message) {
    return `${prefix} ${error.message}`;
  }

  return `${prefix} Revisa los datos e intenta de nuevo.`;
}


export function InventoryPage() {
  const { permissions, employee } = useAuthSession();
  const canAdjust = hasPermission(permissions, "INVENTORY_ADJUST");
  const canRegisterExpense = hasPermission(permissions, "EXPENSE_CREATE");

  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [adjustError, setAdjustError] = useState<string | null>(null);
  const [purchaseOpen, setPurchaseOpen] = useState(false);
  const [purchaseMessage, setPurchaseMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("all");

  const itemsQuery = useInventoryItemsQuery();
  const alertsQuery = useStockAlertsQuery();
  const movementMutation = useInventoryMovementMutation();
  const purchaseMutation = usePurchaseReceiptMutation();
  const paymentMethodsQuery = usePaymentMethodsQuery(purchaseOpen && canRegisterExpense);

  const allItems = itemsQuery.data ?? [];

  const summary = useMemo(() => {
    const agotados = allItems.filter((i) => {
      const s = i.stock_status.toLowerCase();
      return s.includes("agotado") || s.includes("sin stock");
    }).length;
    const bajo = allItems.filter((i) => {
      const s = i.stock_status.toLowerCase();
      return (
        !s.includes("agotado") &&
        !s.includes("sin stock") &&
        (s.includes("bajo") || s.includes("minimo") || s.includes("mínimo"))
      );
    }).length;
    return {
      total: allItems.length,
      agotados,
      bajo,
      correctos: allItems.length - agotados - bajo,
    };
  }, [allItems]);

  const filteredItems = useMemo(() => {
    let result = allItems;
    const q = searchQuery.trim().toLowerCase();
    if (q.length > 0) {
      result = result.filter(
        (i) =>
          i.name.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q),
      );
    }
    if (filterStatus === "agotado") {
      result = result.filter((i) => {
        const s = i.stock_status.toLowerCase();
        return s.includes("agotado") || s.includes("sin stock");
      });
    } else if (filterStatus === "bajo") {
      result = result.filter((i) => {
        const s = i.stock_status.toLowerCase();
        return (
          !s.includes("agotado") &&
          !s.includes("sin stock") &&
          (s.includes("bajo") || s.includes("minimo") || s.includes("mínimo"))
        );
      });
    } else if (filterStatus === "correcto") {
      result = result.filter((i) => {
        const s = i.stock_status.toLowerCase();
        return (
          !s.includes("agotado") &&
          !s.includes("sin stock") &&
          !s.includes("bajo") &&
          !s.includes("minimo") &&
          !s.includes("mínimo")
        );
      });
    }
    return result;
  }, [allItems, searchQuery, filterStatus]);

  const isFiltered = searchQuery.trim().length > 0 || filterStatus !== "all";

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

  const FILTER_OPTIONS: { value: FilterStatus; label: string }[] = [
    { value: "all", label: `Todos (${summary.total})` },
    { value: "agotado", label: `Agotados (${summary.agotados})` },
    { value: "bajo", label: `Bajo stock (${summary.bajo})` },
    { value: "correcto", label: `Correctos (${summary.correctos})` },
  ];

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
            Existencias
          </p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Inventario</h1>
          <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
            Controla insumos, alertas y entradas de almacén.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {canAdjust ? (
            <BrutalButton
              variant="primary"
              onClick={() => {
                setPurchaseMessage(null);
                setPurchaseOpen(true);
              }}
            >
              Recibir compra
            </BrutalButton>
          ) : null}
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

      {purchaseMessage ? (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-3 font-black text-[var(--kp-success-text)]">
          {purchaseMessage}
        </p>
      ) : null}

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState title="No se pudo cargar Inventario" message="Intenta de nuevo." />
      ) : (
        <>
          {/* Resumen compacto */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
              <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
                Total insumos
              </p>
              <p className="mt-1 text-2xl font-black">{summary.total}</p>
            </div>
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
              <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-danger-contrast)]">
                Agotados
              </p>
              <p className="mt-1 text-2xl font-black text-[var(--kp-danger-contrast)]">
                {summary.agotados}
              </p>
            </div>
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
              <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-warning-contrast)]">
                Bajo stock
              </p>
              <p className="mt-1 text-2xl font-black text-[var(--kp-warning-contrast)]">
                {summary.bajo}
              </p>
            </div>
            <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
              <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-success-contrast)]">
                Correctos
              </p>
              <p className="mt-1 text-2xl font-black text-[var(--kp-success-contrast)]">
                {summary.correctos}
              </p>
            </div>
          </div>

          <LowStockPanel alerts={alertsQuery.data ?? []} items={allItems} />

          {/* Búsqueda y filtros */}
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-48 flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--kp-muted)]" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar por nombre o clave..."
                className="w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] py-2 pl-9 pr-3 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)]"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {FILTER_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setFilterStatus(opt.value)}
                  className={[
                    "min-h-[var(--kp-touch-sm)] border-4 border-[var(--kp-ink)] px-3 text-xs font-black uppercase tracking-[0.08em] transition-[transform,box-shadow]",
                    filterStatus === opt.value
                      ? "translate-x-[2px] translate-y-[2px] bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)] shadow-none"
                      : "bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none",
                  ].join(" ")}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <InventoryList
            items={filteredItems}
            canAdjust={canAdjust}
            onAdjust={handleAdjustRequest}
            isFiltered={isFiltered}
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
          errorMessage={
            purchaseMutation.isError
              ? getPurchaseReceiptErrorMessage(purchaseMutation.error)
              : null
          }
          onClose={() => {
            purchaseMutation.reset();
            setPurchaseOpen(false);
          }}
          onSubmit={(payload) =>
            void purchaseMutation
              .mutateAsync(payload)
              .then((result) => {
                const msg =
                  result.cash_expense_id !== null
                    ? `Recepción ${result.folio} registrada con gasto de caja.`
                    : `Recepción ${result.folio} registrada sin gasto de caja.`;
                setPurchaseMessage(msg);
                setPurchaseOpen(false);
              })
              .catch(() => undefined)
          }
        />
      ) : null}
    </div>
  );
}

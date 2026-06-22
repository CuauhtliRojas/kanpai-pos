import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasPermission } from "../../auth/lib/permissions";
import { useCurrentCashShiftQuery } from "../../cash/hooks/useCurrentCashShiftQuery";
import { CheckoutPanel } from "../../checkout/components/CheckoutPanel";
import { SendCommandPanel } from "../../commands/components/SendCommandPanel";
import { StationOrdersPanel } from "../../commands/components/StationOrdersPanel";
import { CategoryFilterBar } from "../../products/components/CategoryFilterBar";
import { ProductGrid } from "../../products/components/ProductGrid";
import { useCategoriesQuery } from "../../products/hooks/useCategoriesQuery";
import { useProductsQuery } from "../../products/hooks/useProductsQuery";
import type { Product } from "../../products/types/productTypes";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { ActiveTicketLinesPanel } from "../../tickets/components/ActiveTicketLinesPanel";
import { useAddTicketLineMutation } from "../../tickets/hooks/useAddTicketLineMutation";
import { useTicketLinesQuery } from "../../tickets/hooks/useTicketLinesQuery";
import { ProductVariantDialog } from "../../variants/components/ProductVariantDialog";
import { useProductVariantGroupsQuery } from "../../variants/hooks/useProductVariantGroupsQuery";
import type { VariantSelection } from "../../variants/types/variantTypes";
import { ActiveTicketPanel } from "../components/ActiveTicketPanel";
import { OpenTicketDialog } from "../components/OpenTicketDialog";
import { PosBlockedByCashPanel } from "../components/PosBlockedByCashPanel";
import { TableGrid } from "../components/TableGrid";
import { useOpenTableTicketMutation } from "../hooks/useOpenTableTicketMutation";
import { useTablesQuery } from "../hooks/useTablesQuery";
import { useTicketQuery } from "../hooks/useTicketQuery";
import type { DiningTable, Ticket } from "../types/tableTypes";

function getPosErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    return "No se pudo completar la operación. Intenta de nuevo.";
  }
  return "Ocurrió un error inesperado. Intenta de nuevo.";
}

type PosViewMode = "tables" | "capture";

function ticketIsActive(ticket: Ticket | null): ticket is Ticket {
  return ticket !== null && ticket.status !== "Cobrado" && ticket.status !== "Cancelado";
}

export function PosTablesPage() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [productMessage, setProductMessage] = useState<string | null>(null);
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [pendingOpenTable, setPendingOpenTable] = useState<DiningTable | null>(null);
  const [tableSelectionError, setTableSelectionError] = useState<string | null>(null);
  const [pendingTicketTable, setPendingTicketTable] = useState<DiningTable | null>(null);
  const { employee, permissions } = useAuthSession();
  const cashQuery = useCurrentCashShiftQuery();
  const hasOpenCash = cashQuery.data !== null && cashQuery.data !== undefined;
  const {
    selectedTable,
    activeTicket,
    setCurrentOperation,
    clearCurrentOperation,
  } = useCurrentOperation();
  const [viewMode, setViewMode] = useState<PosViewMode>(() =>
    selectedTable && ticketIsActive(activeTicket) && activeTicket.table_id === selectedTable.id
      ? "capture"
      : "tables",
  );
  const requestedTicketId = pendingTicketTable?.active_ticket_id ?? activeTicket?.id ?? null;
  const ticketQuery = useTicketQuery(requestedTicketId);
  const displayedTicket =
    activeTicket && ticketQuery.data?.id === activeTicket.id
      ? ticketQuery.data
      : activeTicket;
  const hasActiveTicket =
    selectedTable !== null &&
    ticketIsActive(displayedTicket) &&
    displayedTicket.table_id === selectedTable.id;
  const isCaptureMode = hasOpenCash && hasActiveTicket && viewMode === "capture";
  const isChangingTable = hasOpenCash && hasActiveTicket && viewMode === "tables";
  const tablesQuery = useTablesQuery(hasOpenCash);
  const categoriesQuery = useCategoriesQuery(isCaptureMode);
  const productsQuery = useProductsQuery(isCaptureMode);
  const openTicketMutation = useOpenTableTicketMutation();
  const addLineMutation = useAddTicketLineMutation();
  const variantGroupsQuery = useProductVariantGroupsQuery(selectedProduct?.id ?? null);
  const linesQuery = useTicketLinesQuery(isCaptureMode ? displayedTicket.id : null);
  const pendingLineCount = (linesQuery.data ?? []).filter(
    (line) => line.status === "Capturado",
  ).length;

  const categories = useMemo(
    () => (categoriesQuery.data ?? []).filter((category) => category.active),
    [categoriesQuery.data],
  );
  const products = useMemo(
    () =>
      (productsQuery.data ?? []).filter(
        (product) =>
          selectedCategoryId === null || product.category_id === selectedCategoryId,
      ),
    [productsQuery.data, selectedCategoryId],
  );

  useEffect(() => {
    if (!pendingTicketTable) return;

    if (ticketQuery.isError) {
      setPendingTicketTable(null);
      setTableSelectionError("No se pudo abrir la cuenta. Intenta de nuevo.");
      return;
    }

    if (
      ticketQuery.data?.id !== pendingTicketTable.active_ticket_id ||
      ticketQuery.data.table_id !== pendingTicketTable.id
    ) {
      return;
    }

    setCurrentOperation(pendingTicketTable, ticketQuery.data);
    setPendingTicketTable(null);
    setTableSelectionError(null);
    setProductMessage(null);
    setCheckoutMessage(null);
    setViewMode("capture");
  }, [pendingTicketTable, setCurrentOperation, ticketQuery.data, ticketQuery.isError]);

  async function addSelectedProduct(
    product: Product,
    variantSelections: VariantSelection[],
    keepDialogOnError = false,
  ) {
    if (!isCaptureMode || !employee) return;
    setProductMessage(null);
    try {
      await addLineMutation.mutateAsync({
        ticketId: displayedTicket.id,
        payload: {
          product_id: product.id,
          employee_id: employee.id,
          quantity: 1,
          variant_selections: variantSelections,
        },
      });
      setSelectedProduct(null);
      setProductMessage("Agregado a cuenta");
    } catch {
      if (!keepDialogOnError) setSelectedProduct(null);
      setProductMessage("No se pudo agregar el producto. Intenta de nuevo.");
    }
  }

  function handleProductSelect(product: Product) {
    if (!isCaptureMode) return;
    addLineMutation.reset();
    setProductMessage(null);
    setSelectedProduct(product);
  }

  function handleTableSelect(table: DiningTable) {
    if (pendingTicketTable) return;
    setTableSelectionError(null);
    openTicketMutation.reset();

    if (table.status === "Libre") {
      setPendingOpenTable(table);
      return;
    }

    if (table.active_ticket_id == null) {
      setTableSelectionError(
        "Esta mesa tiene cuenta abierta, pero no se pudo cargar. Intenta actualizar mesas.",
      );
      return;
    }

    setPendingTicketTable(table);
  }

  useEffect(() => {
    if (!selectedProduct || !variantGroupsQuery.data) return;
    const activeGroups = variantGroupsQuery.data.filter((group) => group.active);
    if (activeGroups.length === 0) void addSelectedProduct(selectedProduct, []);
  }, [selectedProduct, variantGroupsQuery.data]);

  useEffect(() => {
    if (!selectedProduct || !variantGroupsQuery.isError) return;
    setProductMessage("No se pudieron cargar las opciones. Intenta de nuevo.");
    setSelectedProduct(null);
  }, [selectedProduct, variantGroupsQuery.isError]);

  if (cashQuery.isPending) return <LoadingState />;
  if (cashQuery.isError) {
    return (
      <ErrorState
        title="No se pudo consultar la caja"
        message={getPosErrorMessage(cashQuery.error) ?? "Intenta de nuevo."}
      />
    );
  }

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-start justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Venta</p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-4xl">
            {isCaptureMode ? "Captura de venta" : isChangingTable ? "Cambiar mesa" : "Elige mesa"}
          </h1>
          <p className="mt-2 font-bold text-[var(--kp-muted)]">
            {isCaptureMode
              ? "Agrega productos y revisa la cuenta activa."
              : isChangingTable
                ? "Elige otra mesa o vuelve a la cuenta actual."
                : "Selecciona una mesa para abrir o continuar una cuenta."}
          </p>
        </div>
        {isChangingTable ? (
          <BrutalButton
            type="button"
            size="lg"
            onClick={() => {
              setTableSelectionError(null);
              setPendingTicketTable(null);
              setViewMode("capture");
            }}
          >
            Volver a la cuenta actual
          </BrutalButton>
        ) : null}
      </header>

      {!hasOpenCash ? (
        <PosBlockedByCashPanel />
      ) : tablesQuery.isPending ? (
        <LoadingState />
      ) : tablesQuery.isError ? (
        <ErrorState
          title="No se pudo cargar mesas"
          message={getPosErrorMessage(tablesQuery.error) ?? "Intenta de nuevo."}
        />
      ) : isCaptureMode ? (
        <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(360px,0.9fr)]">
          <main className="order-2 min-w-0 border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-4 shadow-[var(--kp-shadow-hard)] lg:order-1">
            <h2 className="text-xl font-black uppercase">Categorías</h2>
            {categoriesQuery.isError ? (
              <p className="mt-3 font-bold">No se pudo cargar productos</p>
            ) : (
              <div className="mt-3">
                <CategoryFilterBar
                  categories={categories}
                  selectedCategoryId={selectedCategoryId}
                  onSelect={setSelectedCategoryId}
                />
              </div>
            )}

            {productMessage ? (
              <p className="mt-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-selected)] p-3 font-black text-[var(--kp-selected-contrast)]">
                {productMessage}
              </p>
            ) : null}

            <div className="mt-4 max-h-[calc(100vh-15rem)] overflow-y-auto pr-1">
              {productsQuery.isPending ? (
                <LoadingState />
              ) : productsQuery.isError ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 text-center font-black uppercase">
                  No se pudo cargar productos
                </p>
              ) : products.length === 0 ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 text-center font-black uppercase">
                  No hay productos en esta categoría
                </p>
              ) : (
                <ProductGrid
                  products={products}
                  disabled={
                    addLineMutation.isPending ||
                    variantGroupsQuery.isFetching ||
                    displayedTicket.status === "En cobro"
                  }
                  onSelect={handleProductSelect}
                />
              )}
            </div>
          </main>

          <div className="order-1 grid gap-4 lg:order-2 lg:sticky lg:top-[calc(var(--kp-topbar-height)+1rem)] lg:max-h-[calc(100vh-var(--kp-topbar-height)-2rem)] lg:overflow-y-auto lg:pr-1">
            <ActiveTicketPanel
              table={selectedTable}
              ticket={displayedTicket}
              onChangeTable={() => {
                setTableSelectionError(null);
                setViewMode("tables");
              }}
            />
            {ticketQuery.isError ? (
              <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                No se pudo actualizar la cuenta. Intenta de nuevo.
              </p>
            ) : null}
            <ActiveTicketLinesPanel
              ticket={displayedTicket}
              lines={linesQuery.data ?? []}
              isLoading={linesQuery.isPending}
              hasError={linesQuery.isError}
              employeeId={employee?.id ?? null}
              canCancel={hasPermission(permissions, "TICKET_CANCEL")}
            />
            <SendCommandPanel
              ticketId={displayedTicket.id}
              employeeId={employee?.id ?? null}
              pendingLineCount={pendingLineCount}
              isLoadingLines={linesQuery.isPending}
            />
            <StationOrdersPanel ticketId={displayedTicket.id} />
            <CheckoutPanel
              hasSelectedTable
              ticket={displayedTicket}
              lineCount={(linesQuery.data ?? []).length}
              lines={linesQuery.data ?? []}
              pendingLineCount={pendingLineCount}
              employeeId={employee?.id ?? null}
              canAuthorizeDiscount={hasPermission(permissions, "DISCOUNT_AUTHORIZE")}
              canCancelTicket={hasPermission(permissions, "TICKET_CANCEL")}
              notice={checkoutMessage}
              onClosed={() => {
                setProductMessage(null);
                setCheckoutMessage("Cuenta cerrada. Mesa liberada.");
                clearCurrentOperation();
                setViewMode("tables");
              }}
              onCancelled={() => {
                setProductMessage(null);
                setCheckoutMessage("Cuenta cancelada. Mesa liberada.");
                clearCurrentOperation();
                setViewMode("tables");
              }}
            />
          </div>
        </div>
      ) : (
        <main className="mx-auto w-full max-w-7xl border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-4 shadow-[var(--kp-shadow-hard)] md:p-6">
          {tableSelectionError ? (
            <div className="mb-4 grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 text-[var(--kp-danger-text)] sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <p className="font-bold">{tableSelectionError}</p>
              <BrutalButton
                type="button"
                size="md"
                onClick={() => {
                  setTableSelectionError(null);
                  void tablesQuery.refetch();
                }}
              >
                Actualizar mesas
              </BrutalButton>
            </div>
          ) : null}
          {pendingTicketTable && ticketQuery.isPending ? (
            <p className="mb-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-info-bg)] p-3 font-black uppercase">
              Cargando cuenta...
            </p>
          ) : null}
          <TableGrid
            tables={tablesQuery.data}
            selectedTableId={
              pendingTicketTable?.id ?? pendingOpenTable?.id ?? selectedTable?.id ?? null
            }
            onSelect={handleTableSelect}
          />
        </main>
      )}

      {pendingOpenTable ? (
        <OpenTicketDialog
          table={pendingOpenTable}
          isOpening={openTicketMutation.isPending}
          errorMessage={
            openTicketMutation.error
              ? "No se pudo abrir la cuenta. Intenta de nuevo."
              : null
          }
          onClose={() => {
            if (openTicketMutation.isPending) return;
            openTicketMutation.reset();
            setPendingOpenTable(null);
          }}
          onConfirm={() => {
            if (!employee || openTicketMutation.isPending) return;
            void openTicketMutation
              .mutateAsync({
                table: pendingOpenTable,
                payload: { employee_id: employee.id },
              })
              .then(() => {
                setPendingOpenTable(null);
                setProductMessage(null);
                setCheckoutMessage(null);
                setViewMode("capture");
              })
              .catch(() => undefined);
          }}
        />
      ) : null}

      {selectedProduct && variantGroupsQuery.data?.some((group) => group.active) ? (
        <ProductVariantDialog
          product={selectedProduct}
          groups={variantGroupsQuery.data}
          isSaving={addLineMutation.isPending}
          errorMessage={
            addLineMutation.isError
              ? "No se pudo agregar el producto. Intenta de nuevo."
              : null
          }
          onClose={() => {
            addLineMutation.reset();
            setSelectedProduct(null);
          }}
          onSubmit={(selections) =>
            void addSelectedProduct(selectedProduct, selections, true)
          }
        />
      ) : null}
    </div>
  );
}

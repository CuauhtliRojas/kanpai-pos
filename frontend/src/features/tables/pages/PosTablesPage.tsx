import { useMemo, useState } from "react";
import { ApiError } from "../../../api/http";
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
import { ActiveTicketLinesPanel } from "../../tickets/components/ActiveTicketLinesPanel";
import { useAddTicketLineMutation } from "../../tickets/hooks/useAddTicketLineMutation";
import { useTicketLinesQuery } from "../../tickets/hooks/useTicketLinesQuery";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { ActiveTicketPanel } from "../components/ActiveTicketPanel";
import { PosBlockedByCashPanel } from "../components/PosBlockedByCashPanel";
import { TableGrid } from "../components/TableGrid";
import { useOpenTableTicketMutation } from "../hooks/useOpenTableTicketMutation";
import { useTablesQuery } from "../hooks/useTablesQuery";
import { useTicketQuery } from "../hooks/useTicketQuery";

function getPosErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    return "No se pudo completar la operación. Intenta de nuevo.";
  }
  return "Ocurrió un error inesperado. Intenta de nuevo.";
}

export function PosTablesPage() {
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [productMessage, setProductMessage] = useState<string | null>(null);
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);
  const { employee, permissions } = useAuthSession();
  const cashQuery = useCurrentCashShiftQuery();
  const hasOpenCash = cashQuery.data !== null && cashQuery.data !== undefined;
  const tablesQuery = useTablesQuery(hasOpenCash);
  const categoriesQuery = useCategoriesQuery(hasOpenCash);
  const productsQuery = useProductsQuery(hasOpenCash);
  const openTicketMutation = useOpenTableTicketMutation();
  const addLineMutation = useAddTicketLineMutation();
  const {
    selectedTable,
    activeTicket,
    selectTable,
    setCurrentOperation,
    clearCurrentOperation,
  } = useCurrentOperation();
  const ticketQuery = useTicketQuery(activeTicket?.id ?? null);
  const displayedTicket = ticketQuery.data ?? activeTicket;
  const linesQuery = useTicketLinesQuery(displayedTicket?.id ?? null);
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

  async function handleProductSelect(product: Product) {
    if (!selectedTable) {
      setProductMessage("Primero elige una mesa.");
      return;
    }
    if (!displayedTicket || displayedTicket.table_id !== selectedTable.id) {
      setProductMessage("Abre una cuenta para esta mesa.");
      return;
    }
    if (!employee) return;

    setProductMessage(null);
    try {
      await addLineMutation.mutateAsync({
        ticketId: displayedTicket.id,
        payload: { product_id: product.id, employee_id: employee.id, quantity: 1 },
      });
      setProductMessage("Agregado a cuenta");
    } catch {
      setProductMessage("No se pudo agregar el producto. Intenta de nuevo.");
    }
  }

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
      <header className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">POS</p>
        <h1 className="mt-1 text-3xl font-black uppercase md:text-4xl">Productos</h1>
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
      ) : (
        <div className="grid items-start gap-4 lg:grid-cols-[230px_minmax(0,1fr)_290px]">
          <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard)]">
            <h2 className="mb-3 text-xl font-black uppercase">Mesas</h2>
            <div className="max-h-[520px] overflow-y-auto pr-1">
              <TableGrid
                tables={tablesQuery.data}
                selectedTableId={selectedTable?.id ?? null}
                compact
                onSelect={(table) => {
                  selectTable(table);
                  setProductMessage(null);
                  setCheckoutMessage(null);
                }}
              />
            </div>
          </section>

          <main className="min-w-0 border-4 border-[var(--kp-ink)] bg-zinc-900 p-4 shadow-[var(--kp-shadow-hard)]">
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

            <div className="mt-4 max-h-[480px] overflow-y-auto pr-1">
              {productsQuery.isPending ? (
                <LoadingState />
              ) : productsQuery.isError ? (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 text-center font-black uppercase">
                  No se pudo cargar productos
                </p>
              ) : (
                <ProductGrid
                  products={products}
                  disabled={addLineMutation.isPending || displayedTicket?.status === "En cobro"}
                  onSelect={(product) => void handleProductSelect(product)}
                />
              )}
            </div>
          </main>

          <div className="grid gap-4">
            <ActiveTicketPanel
              table={selectedTable}
              ticket={displayedTicket}
              isOpening={openTicketMutation.isPending}
              isLoadingTicket={ticketQuery.isPending && activeTicket !== null}
              errorMessage={getPosErrorMessage(openTicketMutation.error ?? ticketQuery.error)}
              onOpen={async (table) => {
                if (!employee) return;
                try {
                  await openTicketMutation.mutateAsync({
                    table,
                    payload: { employee_id: employee.id },
                  });
                } catch {
                  // El panel muestra el mensaje de la operación.
                }
              }}
              onContinue={(table, ticket) => setCurrentOperation(table, ticket)}
            />
            <ActiveTicketLinesPanel
              ticket={displayedTicket}
              lines={linesQuery.data ?? []}
              isLoading={linesQuery.isPending}
              hasError={linesQuery.isError}
              employeeId={employee?.id ?? null}
              canCancel={hasPermission(permissions, "TICKET_CANCEL")}
            />
            <SendCommandPanel
              ticketId={displayedTicket?.id ?? null}
              employeeId={employee?.id ?? null}
              pendingLineCount={pendingLineCount}
              isLoadingLines={linesQuery.isPending}
            />
            <StationOrdersPanel ticketId={displayedTicket?.id ?? null} />
            <CheckoutPanel
              hasSelectedTable={selectedTable !== null}
              ticket={displayedTicket}
              lineCount={(linesQuery.data ?? []).length}
              pendingLineCount={pendingLineCount}
              employeeId={employee?.id ?? null}
              canAuthorizeDiscount={hasPermission(permissions, "DISCOUNT_AUTHORIZE")}
              notice={checkoutMessage}
              onClosed={() => {
                setProductMessage(null);
                setCheckoutMessage("Cuenta cerrada. Mesa liberada.");
                clearCurrentOperation();
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

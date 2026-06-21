import { ApiError } from "../../../api/http";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { useCurrentCashShiftQuery } from "../../cash/hooks/useCurrentCashShiftQuery";
import { useCurrentOperation } from "../../operations/hooks/useCurrentOperation";
import { ActiveTicketPanel } from "../components/ActiveTicketPanel";
import { PosBlockedByCashPanel } from "../components/PosBlockedByCashPanel";
import { TableGrid } from "../components/TableGrid";
import { useOpenTableTicketMutation } from "../hooks/useOpenTableTicketMutation";
import { useTablesQuery } from "../hooks/useTablesQuery";
import { useTicketQuery } from "../hooks/useTicketQuery";

function getPosErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (
    error instanceof ApiError &&
    typeof error.details === "object" &&
    error.details !== null &&
    "detail" in error.details &&
    typeof error.details.detail === "string"
  ) {
    return error.details.detail;
  }
  if (error instanceof ApiError && error.status !== null) {
    return "No se pudo completar la operación. Intenta de nuevo.";
  }
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

export function PosTablesPage() {
  const { employee } = useAuthSession();
  const cashQuery = useCurrentCashShiftQuery();
  const hasOpenCash = cashQuery.data !== null && cashQuery.data !== undefined;
  const tablesQuery = useTablesQuery(hasOpenCash);
  const openTicketMutation = useOpenTableTicketMutation();
  const {
    selectedTable,
    activeTicket,
    selectTable,
    setCurrentOperation,
  } = useCurrentOperation();
  const ticketQuery = useTicketQuery(activeTicket?.id ?? null);
  const displayedTicket = ticketQuery.data ?? activeTicket;

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
        <h1 className="mt-2 text-4xl font-black uppercase md:text-5xl">Mesas</h1>
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
        <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <TableGrid
            tables={tablesQuery.data}
            selectedTableId={selectedTable?.id ?? null}
            onSelect={selectTable}
          />
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
        </div>
      )}
    </div>
  );
}

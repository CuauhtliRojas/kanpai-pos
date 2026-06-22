import { useState } from "react";
import { ApiError } from "../../../api/http";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { hasPermission } from "../../auth/lib/permissions";
import { CashClosedPanel } from "../components/CashClosedPanel";
import { CashExpensePanel } from "../components/CashExpensePanel";
import { CashOpenPanel } from "../components/CashOpenPanel";
import { CashSummaryPanel } from "../components/CashSummaryPanel";
import { CashShiftDetailDialog, type CashDetailTab } from "../components/CashShiftDetailDialog";
import { useCashShiftSummaryQuery } from "../hooks/useCashShiftSummaryQuery";
import { useCloseCashShiftMutation } from "../hooks/useCloseCashShiftMutation";
import { useCreateCashExpenseMutation } from "../hooks/useCreateCashExpenseMutation";
import { useCurrentCashShiftQuery } from "../hooks/useCurrentCashShiftQuery";
import { useOpenCashShiftMutation } from "../hooks/useOpenCashShiftMutation";

function getCashErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return "No tienes permiso para usar esta opción. Pide ayuda al encargado.";
    }
    if (
      typeof error.details === "object" &&
      error.details !== null &&
      "detail" in error.details &&
      typeof error.details.detail === "string"
    ) {
      return error.details.detail;
    }
    if (error.status !== null) {
      return "No se pudo completar la operación. Intenta de nuevo.";
    }
  }
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

export function CashPage() {
  const [detailTab, setDetailTab] = useState<CashDetailTab | null>(null);
  const { employee, permissions } = useAuthSession();
  const currentQuery = useCurrentCashShiftQuery();
  const cashShift = currentQuery.data ?? null;
  const summaryQuery = useCashShiftSummaryQuery(cashShift?.id ?? null);
  const openMutation = useOpenCashShiftMutation();
  const closeMutation = useCloseCashShiftMutation();
  const expenseMutation = useCreateCashExpenseMutation(cashShift?.id ?? 0);

  if (currentQuery.isPending) {
    return <LoadingState />;
  }

  if (currentQuery.isError) {
    return (
      <ErrorState
        title="No se pudo consultar la caja"
        message={getCashErrorMessage(currentQuery.error) ?? "Intenta de nuevo."}
      />
    );
  }

  return (
    <div className="grid gap-4">
      <header className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-4 py-3 shadow-[var(--kp-shadow-hard)] md:px-5">
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Operación</p>
        <h1 className="mt-1 text-3xl font-black uppercase md:text-4xl">Caja</h1>
        <p className="mt-1 font-bold text-[var(--kp-muted)]">
          {cashShift ? "Controla el efectivo y revisa el turno." : "Abre el turno para empezar a vender."}
        </p>
      </header>

      {!cashShift ? (
        <CashClosedPanel
          canOpen={hasPermission(permissions, "CASH_SHIFT_OPEN")}
          isOpening={openMutation.isPending}
          errorMessage={getCashErrorMessage(openMutation.error)}
          onOpen={async (openingCashCents) => {
            if (!employee) return;
            await openMutation.mutateAsync({
              employee_id: employee.id,
              opening_cash_cents: openingCashCents,
            });
          }}
        />
      ) : (
        <>
          <CashOpenPanel
            cashShift={cashShift}
            canClose={hasPermission(permissions, "CASH_SHIFT_CLOSE")}
            isClosing={closeMutation.isPending}
            errorMessage={getCashErrorMessage(closeMutation.error)}
            onClose={async (declaredCashCents) => {
              if (!employee) return;
              await closeMutation.mutateAsync({
                cashShiftId: cashShift.id,
                payload: {
                  employee_id: employee.id,
                  declared_cash_cents: declaredCashCents,
                  allow_pending_print_jobs: true,
                },
              });
            }}
          />
          <CashSummaryPanel
            summary={summaryQuery.data}
            isLoading={summaryQuery.isPending}
            errorMessage={getCashErrorMessage(summaryQuery.error)}
            onViewDetails={() => setDetailTab("expenses")}
          />
          <CashExpensePanel
            canCreate={hasPermission(permissions, "EXPENSE_CREATE")}
            isSaving={expenseMutation.isPending}
            errorMessage={getCashErrorMessage(expenseMutation.error)}
            totalExpensesCents={summaryQuery.data?.total_expenses_cents ?? 0}
            expenseCount={summaryQuery.data?.active_expense_count ?? 0}
            onViewExpenses={() => setDetailTab("expenses")}
            onCreate={async (amountCents, description, category, note) => {
              if (!employee) return;
              await expenseMutation.mutateAsync({
                employee_id: employee.id,
                amount_cents: amountCents,
                description,
                category,
                note,
              });
            }}
          />
          {detailTab ? (
            <CashShiftDetailDialog
              cashShiftId={cashShift.id}
              summary={summaryQuery.data}
              initialTab={detailTab}
              onClose={() => setDetailTab(null)}
            />
          ) : null}
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { useCashShiftAuditQuery } from "../../audit/hooks/useAuditDetailQueries";
import type { CashShiftSummary } from "../types/cashTypes";

export type CashDetailTab = "expenses" | "sales";

type CashShiftDetailDialogProps = {
  cashShiftId: number;
  summary: CashShiftSummary | undefined;
  initialTab: CashDetailTab;
  onClose: () => void;
};

const categoryLabels: Record<string, string> = {
  SUPPLIES: "Insumo",
  SERVICE: "Servicio",
  OPERATIONS: "Operación",
  MAINTENANCE: "Mantenimiento",
  OTHER: "Otro",
};

const statusLabels: Record<string, string> = {
  ACTIVE: "Activo",
  CANCELLED: "Cancelado",
  PAID: "Pagado",
  OPEN: "Abierto",
  CLOSED: "Cerrado",
};

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

function formatCode(value: string): string {
  const knownLabel = statusLabels[value];
  if (knownLabel) return knownLabel;
  const normalized = value.replace(/_/g, " ").toLocaleLowerCase("es-MX");
  return normalized.charAt(0).toLocaleUpperCase("es-MX") + normalized.slice(1);
}

export function CashShiftDetailDialog({
  cashShiftId,
  summary,
  initialTab,
  onClose,
}: CashShiftDetailDialogProps) {
  const [activeTab, setActiveTab] = useState<CashDetailTab>(initialTab);
  const detailQuery = useCashShiftAuditQuery(cashShiftId);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const detail = detailQuery.data;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-3" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="cash-detail-title"
        className="flex max-h-[calc(100vh-1.5rem)] w-full max-w-[1100px] flex-col border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex flex-wrap items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] p-3 md:px-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-selected)]">Movimientos del turno</p>
            <h2 id="cash-detail-title" className="text-2xl font-black uppercase">Detalle del turno</h2>
            <p className="font-bold text-[var(--kp-muted)]">Corte {detail?.cash_shift.folio ?? summary?.folio ?? "actual"}</p>
          </div>
          <BrutalButton type="button" size="md" onClick={onClose}>Volver</BrutalButton>
        </div>

        <div className="grid grid-cols-2 border-b-4 border-[var(--kp-ink)]" role="tablist" aria-label="Detalle del turno">
          {([
            ["expenses", "Gastos"],
            ["sales", "Ventas del turno"],
          ] as const).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`min-h-[var(--kp-touch-sm)] border-r-4 border-[var(--kp-ink)] px-2 text-sm font-black uppercase last:border-r-0 ${
                activeTab === tab
                  ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
                  : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-3 md:p-4">
          {detailQuery.isPending ? <LoadingState /> : null}
          {detailQuery.isError ? (
            <div className="grid gap-3">
              <ErrorState message="No se pudo cargar el detalle del turno. Intenta de nuevo." />
              <BrutalButton type="button" size="md" onClick={() => void detailQuery.refetch()}>
                Reintentar
              </BrutalButton>
            </div>
          ) : null}

          {detail && activeTab === "expenses" ? (
            detail.expenses.length > 0 ? (
              <div className="grid gap-2">
                {detail.expenses.map((expense) => (
                  <article
                    key={expense.id}
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 md:grid-cols-[7rem_minmax(0,1fr)_6rem_6rem_8rem]"
                  >
                    <p className="order-1 text-xs font-black uppercase text-[var(--kp-muted)]">{expense.folio}</p>
                    <div className="order-3 col-span-2 min-w-0 md:order-2 md:col-span-1">
                      <h3 className="font-black">{expense.description}</h3>
                      <p className="mt-0.5 text-sm text-[var(--kp-muted)]">
                        <span className="font-black">Tipo:</span>{" "}
                        {categoryLabels[expense.category ?? "OTHER"] ?? "Otro"}
                      </p>
                      {expense.note ? (
                        <p className="mt-0.5 text-sm"><span className="font-black">Nota:</span> {expense.note}</p>
                      ) : null}
                    </div>
                    <p className="order-4 col-span-2 text-sm font-bold text-[var(--kp-muted)] md:order-3 md:col-span-1">
                      Hora {formatTime(expense.created_at)}
                    </p>
                    <p
                      className={`order-5 justify-self-start border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase md:order-4 ${
                        expense.status === "ACTIVE"
                          ? "bg-[var(--kp-success-bg)] text-[var(--kp-success-text)]"
                          : "bg-[var(--kp-surface)] text-[var(--kp-text)]"
                      }`}
                    >
                      {formatCode(expense.status)}
                    </p>
                    <p className="order-2 text-right text-xl font-black md:order-5">
                      {formatCentsToPesos(expense.amount_cents)}
                    </p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-4 font-bold">
                No hay gastos registrados en este turno.
              </p>
            )
          ) : null}

          {detail && activeTab === "sales" ? (
            <div className="mx-auto grid max-w-4xl gap-4">
              <div>
                <h3 className="text-xl font-black uppercase">Ventas del turno</h3>
                <p className="mt-1 font-bold text-[var(--kp-muted)]">
                  Aquí ves el dinero registrado durante el turno.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3"><p className="text-xs font-black uppercase">Ventas</p><p className="text-xl font-black">{formatCentsToPesos(detail.summary.total_sales_cents)}</p></div>
                <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3"><p className="text-xs font-black uppercase">Ventas cobradas</p><p className="text-xl font-black">{formatCentsToPesos(detail.summary.total_paid_cents)}</p></div>
                <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3"><p className="text-xs font-black uppercase">Pedidos</p><p className="text-xl font-black">{detail.summary.ticket_count}</p></div>
              </div>
              <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
                <p className="text-xs font-black uppercase text-[var(--kp-muted)]">Cobros registrados</p>
                <p className="mt-1 text-xl font-black">{summary?.paid_ticket_count ?? "—"}</p>
              </div>
              <p className="border-l-4 border-[var(--kp-warning)] bg-[var(--kp-surface-raised)] p-3 font-bold text-[var(--kp-muted)]">
                El desglose completo de ventas se revisa en Auditoría.
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

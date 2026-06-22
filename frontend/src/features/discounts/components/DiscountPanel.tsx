import { useState } from "react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";
import { useApplyDiscountMutation } from "../hooks/useApplyDiscountMutation";
import { useDiscountPresetsQuery } from "../hooks/useDiscountPresetsQuery";
import { useTicketDiscountsQuery } from "../hooks/useTicketDiscountsQuery";
import type { DiscountCreateRequest } from "../types/discountTypes";
import { DiscountDialog } from "./DiscountDialog";

type DiscountPanelProps = {
  ticket: Ticket;
  employeeId: number | null;
  canAuthorize: boolean;
  actionOnly?: boolean;
};

function discountError(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 403) return "Pide autorización al encargado.";
  if (error instanceof ApiError) {
    const detail =
      typeof error.details === "object" &&
      error.details !== null &&
      "detail" in error.details &&
      typeof error.details.detail === "string"
        ? error.details.detail
        : null;
    if (detail?.includes("excede el subtotal")) return "El descuento excede el subtotal disponible.";
  }
  return "No se pudo aplicar el descuento.";
}

export function DiscountPanel({ ticket, employeeId, canAuthorize, actionOnly = false }: DiscountPanelProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const discountsQuery = useTicketDiscountsQuery(ticket.id);
  const applyMutation = useApplyDiscountMutation();
  const presetsQuery = useDiscountPresetsQuery(dialogOpen);
  const canApply = ticket.status === "Abierto" && employeeId !== null && canAuthorize;

  function handleApply(payload: DiscountCreateRequest) {
    setNotice(null);
    void applyMutation.mutateAsync({ ticketId: ticket.id, payload }).then(() => {
      setNotice("Total actualizado");
      setDialogOpen(false);
    }).catch(() => undefined);
  }

  const dialog = dialogOpen && employeeId !== null ? (
    <DiscountDialog
      employeeId={employeeId}
      subtotalCents={ticket.subtotal_cents}
      currentDiscountCents={ticket.discount_cents}
      presets={presetsQuery.data ?? []}
      isSaving={applyMutation.isPending}
      errorMessage={discountError(applyMutation.error)}
      onClose={() => setDialogOpen(false)}
      onApply={handleApply}
    />
  ) : null;

  if (actionOnly) {
    return (
      <div className="min-w-0">
        <BrutalButton
          type="button"
          size="md"
          fullWidth
          disabled={!canApply}
          title={!canAuthorize ? "Requiere autorización del encargado." : undefined}
          onClick={() => { applyMutation.reset(); setDialogOpen(true); }}
        >
          Aplicar descuento
        </BrutalButton>
        {dialog}
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between gap-3">
        <p className="font-black uppercase">Descuento</p>
        {canApply ? (
          <BrutalButton type="button" size="sm" onClick={() => { applyMutation.reset(); setDialogOpen(true); }}>Aplicar descuento</BrutalButton>
        ) : ticket.status === "Abierto" && !canAuthorize ? (
          <span className="text-right text-xs font-black uppercase text-[var(--kp-warning-text)]">Pide autorización al encargado.</span>
        ) : null}
      </div>

      {discountsQuery.data?.map((discount) => (
        <div key={discount.id} className="flex items-start justify-between gap-3 bg-[var(--kp-bg-alt)] p-2 text-sm font-bold">
          <span>{discount.is_courtesy ? "Cortesía" : "Descuento"}{discount.reason ? ` · ${discount.reason}` : ""}</span>
          <span className="shrink-0">-{formatCentsToPesos(discount.amount_cents)}</span>
        </div>
      ))}
      {notice ? <p className="font-black text-[var(--kp-success-text)]">{notice}</p> : null}
      {dialog}
    </div>
  );
}

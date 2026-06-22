import { useState, type FormEvent } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { parsePesosToCents } from "../../../shared/lib/money";
import type { InventoryItem } from "../../inventory/types/inventoryTypes";
import type { PaymentMethod } from "../../payments/types/paymentTypes";
import type { PurchaseReceiptCreateRequest } from "../types/purchaseTypes";

type Row = { itemId: string; quantity: string; unitCost: string };

type Props = {
  employeeId: number;
  items: InventoryItem[];
  methods: PaymentMethod[];
  canRegisterExpense: boolean;
  isSaving: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onSubmit: (payload: PurchaseReceiptCreateRequest) => void;
};

export function PurchaseReceiptDialog({
  employeeId,
  items,
  methods,
  canRegisterExpense,
  isSaving,
  errorMessage,
  onClose,
  onSubmit,
}: Props) {
  const activeItems = items.filter((item) => item.active);
  const activeMethods = methods.filter((method) => method.active);

  const [supplier, setSupplier] = useState("");
  const [invoice, setInvoice] = useState("");
  const [paid, setPaid] = useState("0");
  const [methodId, setMethodId] = useState("");
  const [note, setNote] = useState("");
  const [rows, setRows] = useState<Row[]>([
    { itemId: activeItems[0]?.id.toString() ?? "", quantity: "", unitCost: "0" },
  ]);

  const paidCents = parsePesosToCents(paid);

  const validRows = rows.every((row) => {
    const qty = Number(row.quantity);
    const cost = parsePesosToCents(row.unitCost);
    const hasItem = activeItems.some((candidate) => candidate.id === Number(row.itemId));
    return hasItem && Number.isFinite(qty) && qty > 0 && cost !== null && cost >= 0;
  });

  const valid =
    rows.length > 0 &&
    validRows &&
    paidCents !== null &&
    paidCents >= 0 &&
    (paidCents === 0 || (canRegisterExpense && methodId !== ""));

  function updateRow(index: number, patch: Partial<Row>) {
    setRows((current) =>
      current.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );
  }

  function addRow() {
    setRows((current) => [
      ...current,
      { itemId: activeItems[0]?.id.toString() ?? "", quantity: "", unitCost: "0" },
    ]);
  }

  function removeRow(index: number) {
    setRows((current) => current.filter((_, i) => i !== index));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!valid || paidCents === null) return;
    onSubmit({
      employee_id: employeeId,
      supplier_name: supplier.trim() || null,
      invoice_reference: invoice.trim() || null,
      paid_amount_cents: paidCents,
      payment_method_id: paidCents > 0 ? Number(methodId) : null,
      note: note.trim() || null,
      lines: rows.map((row) => {
        const item = activeItems.find((candidate) => candidate.id === Number(row.itemId))!;
        return {
          inventory_item_id: item.id,
          quantity: Number(row.quantity),
          unit_id: item.base_unit_id,
          unit_cost_cents: parsePesosToCents(row.unitCost) ?? 0,
        };
      }),
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="purchase-title"
    >
      <form
        onSubmit={handleSubmit}
        className="flex max-h-[92vh] w-full max-w-2xl flex-col border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]"
      >
        {/* Header */}
        <div className="flex shrink-0 items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] p-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Almacén
            </p>
            <h2 id="purchase-title" className="mt-0.5 text-xl font-black uppercase">
              Recibir compra
            </h2>
            <p className="mt-0.5 text-sm font-bold text-[var(--kp-muted)]">
              Agrega insumos recibidos y, si aplica, registra el gasto de caja.
            </p>
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            onClick={onClose}
            disabled={isSaving}
            className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid gap-5">

            {/* Sección 1: Datos de compra */}
            <section>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                1. Datos de compra
              </p>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label
                    htmlFor="pr-supplier"
                    className="block text-xs font-black uppercase tracking-[0.08em]"
                  >
                    Proveedor
                  </label>
                  <input
                    id="pr-supplier"
                    value={supplier}
                    onChange={(e) => setSupplier(e.target.value)}
                    disabled={isSaving}
                    placeholder="Nombre del proveedor"
                    className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                  />
                </div>
                <div>
                  <label
                    htmlFor="pr-invoice"
                    className="block text-xs font-black uppercase tracking-[0.08em]"
                  >
                    Factura o referencia
                  </label>
                  <input
                    id="pr-invoice"
                    value={invoice}
                    onChange={(e) => setInvoice(e.target.value)}
                    disabled={isSaving}
                    placeholder="Número de factura o referencia"
                    className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                  />
                </div>
              </div>
            </section>

            {/* Sección 2: Insumos recibidos */}
            <section>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                2. Insumos recibidos
              </p>
              <div className="grid gap-3">
                {rows.map((row, index) => {
                  const selectedItem = activeItems.find(
                    (item) => item.id === Number(row.itemId),
                  );
                  return (
                    <div
                      key={index}
                      className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3"
                    >
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <label
                            htmlFor={`pr-item-${index}`}
                            className="block text-xs font-black uppercase tracking-[0.08em]"
                          >
                            Insumo
                          </label>
                          <select
                            id={`pr-item-${index}`}
                            value={row.itemId}
                            onChange={(e) => updateRow(index, { itemId: e.target.value })}
                            disabled={isSaving}
                            className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                          >
                            {activeItems.map((item) => (
                              <option key={item.id} value={item.id}>
                                {item.name} ({item.base_unit_name})
                              </option>
                            ))}
                          </select>
                        </div>
                        <button
                          type="button"
                          aria-label="Quitar insumo"
                          disabled={rows.length === 1 || isSaving}
                          onClick={() => removeRow(index)}
                          className="mt-5 flex h-10 w-10 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] hover:bg-[var(--kp-danger)] hover:text-[var(--kp-danger-contrast)] disabled:opacity-40"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2">
                        <div>
                          <label
                            htmlFor={`pr-qty-${index}`}
                            className="block text-xs font-black uppercase tracking-[0.08em]"
                          >
                            Cantidad
                            {selectedItem
                              ? ` (${selectedItem.base_unit_name})`
                              : ""}
                          </label>
                          <input
                            id={`pr-qty-${index}`}
                            value={row.quantity}
                            onChange={(e) => updateRow(index, { quantity: e.target.value })}
                            inputMode="decimal"
                            disabled={isSaving}
                            placeholder="Ej: 10"
                            className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                          />
                        </div>
                        <div>
                          <label
                            htmlFor={`pr-cost-${index}`}
                            className="block text-xs font-black uppercase tracking-[0.08em]"
                          >
                            Costo unitario ($)
                          </label>
                          <input
                            id={`pr-cost-${index}`}
                            value={row.unitCost}
                            onChange={(e) => updateRow(index, { unitCost: e.target.value })}
                            inputMode="decimal"
                            disabled={isSaving}
                            placeholder="Ej: 45.50"
                            className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <BrutalButton
                type="button"
                size="sm"
                onClick={addRow}
                disabled={isSaving || activeItems.length === 0}
                className="mt-3"
              >
                <Plus className="h-4 w-4" /> Agregar insumo
              </BrutalButton>
            </section>

            {/* Sección 3: Pago / gasto de caja */}
            <section>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                3. Pago / gasto de caja
              </p>
              {canRegisterExpense ? (
                <div className="grid gap-3">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <label
                        htmlFor="pr-paid"
                        className="block text-xs font-black uppercase tracking-[0.08em]"
                      >
                        Monto pagado ($)
                      </label>
                      <input
                        id="pr-paid"
                        value={paid}
                        onChange={(e) => setPaid(e.target.value)}
                        inputMode="decimal"
                        disabled={isSaving}
                        placeholder="0"
                        className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                      />
                    </div>
                    {(paidCents ?? 0) > 0 && (
                      <div>
                        <label
                          htmlFor="pr-method"
                          className="block text-xs font-black uppercase tracking-[0.08em]"
                        >
                          Forma de pago
                        </label>
                        <select
                          id="pr-method"
                          value={methodId}
                          onChange={(e) => setMethodId(e.target.value)}
                          disabled={isSaving}
                          className="mt-1 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
                        >
                          <option value="">Elige una opción</option>
                          {activeMethods.map((method) => (
                            <option key={method.id} value={method.id}>
                              {method.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                  <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-sm font-bold text-[var(--kp-muted)]">
                    {(paidCents ?? 0) > 0
                      ? "También se registrará un gasto de caja."
                      : "Se registrará entrada de almacén sin gasto de caja."}
                  </p>
                </div>
              ) : (
                <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3 text-sm font-bold text-[var(--kp-muted)]">
                  No tienes permiso para registrar gasto. Puedes dejar monto pagado
                  en 0.
                </p>
              )}
            </section>

            {/* Sección 4: Nota */}
            <section>
              <p className="mb-2 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                4. Nota
              </p>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                disabled={isSaving}
                rows={2}
                placeholder="Observaciones opcionales de la recepción..."
                className="w-full resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2 font-bold focus:outline-none focus:ring-4 focus:ring-[var(--kp-info)] disabled:opacity-50"
              />
            </section>

            {errorMessage && (
              <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                {errorMessage}
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t-4 border-[var(--kp-ink)] p-4">
          <BrutalButton
            type="submit"
            variant="primary"
            fullWidth
            disabled={!valid || isSaving || activeItems.length === 0}
          >
            {isSaving ? "Registrando..." : "Registrar recepción"}
          </BrutalButton>
        </div>
      </form>
    </div>
  );
}

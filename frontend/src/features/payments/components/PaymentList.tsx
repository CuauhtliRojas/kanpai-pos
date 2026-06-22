import { formatCentsToPesos } from "../../../shared/lib/money";
import type { PaymentMethod, PaymentSummary } from "../types/paymentTypes";

type PaymentListProps = {
  summary: PaymentSummary;
  methods: PaymentMethod[];
};

export function PaymentList({ summary, methods }: PaymentListProps) {
  const methodNames = new Map(methods.map((method) => [method.id, method.name]));

  return (
    <section>
      <div className="grid gap-1 font-bold">
        <div className="flex justify-between gap-3">
          <span>Pagado</span>
          <span>{formatCentsToPesos(summary.total_paid_cents)}</span>
        </div>
        <div className="flex justify-between gap-3 text-lg font-black">
          <span>Restante</span>
          <span>{formatCentsToPesos(summary.remaining_cents)}</span>
        </div>
      </div>

      {summary.payments.length > 0 ? (
        <ul className="mt-2 grid gap-1 border-t-2 border-[var(--kp-divider)] pt-2">
          {summary.payments.map((payment) => (
            <li key={payment.id} className="text-sm font-bold">
              <div className="flex justify-between gap-3">
                <span>{methodNames.get(payment.payment_method_id) ?? "Pago"}</span>
                <span>{formatCentsToPesos(payment.amount_cents)}</span>
              </div>
              {payment.change_cents > 0 ? (
                <div className="mt-1 flex justify-between gap-3 text-[var(--kp-muted)]">
                  <span>Cambio</span>
                  <span>{formatCentsToPesos(payment.change_cents)}</span>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

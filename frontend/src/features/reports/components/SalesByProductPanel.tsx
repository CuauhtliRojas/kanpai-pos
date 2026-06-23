import { formatCentsToPesos } from "../../../shared/lib/money";
import { formatSoldLabel } from "../utils/reportFormatters";
import type { SalesByProductItem } from "../types/reportTypes";
import { ReportBarRow } from "./ReportBarRow";
import { ReportCard } from "./ReportCard";

export function SalesByProductPanel({ items }: { items: SalesByProductItem[] }) {
  const rankedItems = items.slice(0, 10);
  const maxValue = Math.max(0, ...rankedItems.map((item) => item.total_cents));

  return (
    <ReportCard title="Ventas por producto">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-1">
          {rankedItems.map((item, index) => (
            <ReportBarRow
              key={item.product_id}
              rank={index + 1}
              label={item.product_name}
              value={item.total_cents}
              maxValue={maxValue}
              valueLabel={formatCentsToPesos(item.total_cents)}
              meta={
                <>
                  <span>{formatSoldLabel(item.quantity_sold)}</span>
                  {item.variant_breakdown.length > 0 ? (
                    <span className="block normal-case tracking-normal text-[var(--kp-muted)]">
                      {item.variant_breakdown
                        .map((variant) => `${variant.name}: ${formatSoldLabel(variant.quantity_sold)}`)
                        .join(" · ")}
                    </span>
                  ) : null}
                </>
              }
              tone="success"
            />
          ))}
        </div>
      )}
    </ReportCard>
  );
}

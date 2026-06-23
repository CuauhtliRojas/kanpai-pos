import { formatCentsToPesos } from "../../../shared/lib/money";
import { formatBasisPoints, formatReportQuantity } from "../utils/reportFormatters";
import type { SalesByCategoryItem } from "../types/reportTypes";
import { ReportBarRow } from "./ReportBarRow";
import { ReportCard } from "./ReportCard";

export function SalesByCategoryPanel({ items }: { items: SalesByCategoryItem[] }) {
  const rankedItems = items.slice(0, 10);
  const maxValue = Math.max(0, ...rankedItems.map((item) => item.net_sales_cents));

  return (
    <ReportCard title="Ventas por categoría">
      {items.length === 0 ? <p className="font-bold text-[var(--kp-muted)]">Sin datos</p> : (
        <div className="grid gap-1">
          {rankedItems.map((item, index) => {
            const shareLabel = formatBasisPoints(item.share_bps);

            return (
              <ReportBarRow
                key={item.category_id ?? item.category_name}
                rank={index + 1}
                label={item.category_name}
                value={item.net_sales_cents}
                maxValue={maxValue}
                valueLabel={formatCentsToPesos(item.net_sales_cents)}
                meta={
                  <>
                    <span>{item.ticket_count} tickets</span>
                    <span className="ml-2">Descuento {formatCentsToPesos(item.discount_cents)}</span>
                    <span className="ml-2">{formatReportQuantity(item.quantity_sold)} vendidos</span>
                    {shareLabel ? <span className="ml-2 text-[var(--kp-selected)]">{shareLabel} participación</span> : null}
                  </>
                }
                tone="success"
              />
            );
          })}
        </div>
      )}
    </ReportCard>
  );
}

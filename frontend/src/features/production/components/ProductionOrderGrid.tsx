import type { ProductionViewFilter } from "../productionFormatters";
import type { ProductionOrder } from "../types/productionTypes";
import { ProductionOrderList } from "./ProductionOrderList";

type ProductionOrderGridProps = {
  orders: ProductionOrder[];
  filter: ProductionViewFilter;
  stationId: number | undefined;
  activeOrderId: number | null;
  getErrorMessage: (order: ProductionOrder) => string | null;
  isOrderPending: (order: ProductionOrder) => boolean;
  onAccept: (order: ProductionOrder) => void;
  onStart: (order: ProductionOrder) => void;
  onFinish: (order: ProductionOrder) => void;
  onDeliver: (order: ProductionOrder) => void;
};

export function ProductionOrderGrid(props: ProductionOrderGridProps) {
  return <ProductionOrderList {...props} />;
}

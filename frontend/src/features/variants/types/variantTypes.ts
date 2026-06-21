import type { VariantSelectionRequest } from "../../tickets/types/ticketTypes";

export type VariantOption = {
  id: number;
  variant_group_id: number;
  product_id: number | null;
  name: string;
  sku: string | null;
  price_delta_cents: number;
  station_id: number | null;
  active: boolean;
};

export type VariantGroup = {
  id: number;
  product_id: number;
  name: string;
  min_select: number;
  max_select: number;
  required: boolean;
  active: boolean;
  options: VariantOption[];
};

export type VariantSelection = VariantSelectionRequest & { quantity: number };

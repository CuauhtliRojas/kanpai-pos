export type ProductCategory = {
  id: number;
  name: string;
  sort_order: number;
  active: boolean;
  sync_status: string;
};

export type Product = {
  id: number;
  sku: string;
  product_type: string;
  name: string;
  display_name: string;
  category_id: number | null;
  price_cents: number;
  active: boolean;
  visible_pos: boolean;
  image_path?: string | null;
  image_url?: string | null;
};

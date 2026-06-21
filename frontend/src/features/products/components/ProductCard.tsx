import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Product } from "../types/productTypes";
import { ProductImage } from "./ProductImage";

type ProductCardProps = {
  product: Product;
  disabled: boolean;
  onSelect: (product: Product) => void;
};

export function ProductCard({ product, disabled, onSelect }: ProductCardProps) {
  const unavailable = !product.active || !product.visible_pos;
  const isDisabled = disabled || unavailable;

  return (
    <button
      type="button"
      disabled={isDisabled}
      onClick={() => onSelect(product)}
      className={[
        "overflow-hidden border-4 border-[var(--kp-ink)] text-left shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
        isDisabled
          ? "cursor-not-allowed bg-zinc-700 text-zinc-400 opacity-70"
          : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
      ].join(" ")}
    >
      <ProductImage alt={product.display_name || product.name} />
      <span className="grid min-h-24 content-between gap-2 p-3">
        <span className="text-base font-black uppercase leading-tight">
          {product.display_name || product.name}
        </span>
        <span className="flex items-end justify-between gap-2">
          <span className="text-lg font-black">{formatCentsToPesos(product.price_cents)}</span>
          {unavailable ? (
            <span className="text-xs font-black uppercase">No disponible</span>
          ) : null}
        </span>
      </span>
    </button>
  );
}

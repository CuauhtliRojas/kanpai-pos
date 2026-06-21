import type { Product } from "../types/productTypes";
import { ProductCard } from "./ProductCard";

type ProductGridProps = {
  products: Product[];
  disabled: boolean;
  onSelect: (product: Product) => void;
};

export function ProductGrid({ products, disabled, onSelect }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 text-center text-xl font-black uppercase">
        Sin productos disponibles
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          disabled={disabled}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

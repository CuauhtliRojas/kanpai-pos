import { useState } from "react";
import { brandAssets } from "../../../shared/assets/brandAssets";

type ProductImageProps = {
  imageUrl?: string | null;
  alt: string;
};

export function ProductImage({ imageUrl, alt }: ProductImageProps) {
  const [failed, setFailed] = useState(false);
  const source = imageUrl && !failed ? imageUrl : brandAssets.productPlaceholder;

  return (
    <img
      src={source}
      alt={alt}
      className="h-24 w-full border-b-4 border-[var(--kp-ink)] bg-zinc-800 object-cover"
      onError={() => setFailed(true)}
    />
  );
}

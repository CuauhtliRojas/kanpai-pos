import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../../api/apiConfig";
import { brandAssets } from "../../../shared/assets/brandAssets";

type ProductImageProps = {
  imageUrl?: string | null;
  alt: string;
};

function resolveProductImageSource(imageUrl?: string | null): string | null {
  const value = imageUrl?.trim();
  if (!value) return null;

  if (/^(https?:|data:|blob:|file:)/i.test(value)) {
    return value;
  }

  if (value.startsWith("/")) {
    return `${API_BASE_URL}${value}`;
  }

  return `${API_BASE_URL}/${value.replace(/^\.\//, "")}`;
}

export function ProductImage({ imageUrl, alt }: ProductImageProps) {
  const [failed, setFailed] = useState(false);
  const resolvedSource = resolveProductImageSource(imageUrl);

  useEffect(() => {
    setFailed(false);
  }, [resolvedSource]);

  const source = resolvedSource && !failed ? resolvedSource : brandAssets.productPlaceholder;

  return (
    <img
      src={source}
      alt={alt}
      className="h-24 w-full border-b-4 border-[var(--kp-ink)] bg-zinc-800 object-cover"
      onError={() => setFailed(true)}
    />
  );
}

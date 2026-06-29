import { useEffect, useState } from "react";
import { buildApiUrl } from "../../../api/apiConfig";
import { brandAssets } from "../../../shared/assets/brandAssets";

type ProductImageProps = {
  imageUrl?: string | null;
  alt: string;
};

function isAbsoluteImageSource(value: string): boolean {
  return /^(https?:|data:|blob:|file:)/i.test(value);
}

async function resolveProductImageSource(imageUrl?: string | null): Promise<string | null> {
  const value = imageUrl?.trim();
  if (!value) return null;

  if (isAbsoluteImageSource(value)) {
    return value;
  }

  if (value.startsWith("/")) {
    return buildApiUrl(value);
  }

  return buildApiUrl(`/${value.replace(/^\.\//, "")}`);
}

export function ProductImage({ imageUrl, alt }: ProductImageProps) {
  const [failed, setFailed] = useState(false);
  const [resolvedSource, setResolvedSource] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    setFailed(false);
    setResolvedSource(null);

    resolveProductImageSource(imageUrl)
      .then((source) => {
        if (!cancelled) {
          setResolvedSource(source);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setResolvedSource(null);
          setFailed(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [imageUrl]);

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

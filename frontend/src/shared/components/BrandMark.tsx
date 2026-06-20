import { brandAssets } from "../assets/brandAssets";

type BrandMarkProps = {
  variant: "logo" | "icon";
  className?: string;
};

export function BrandMark({ variant, className }: BrandMarkProps) {
  const src = variant === "logo" ? brandAssets.appLogo : brandAssets.appIcon;

  return <img src={src} alt="Kanpai" className={className} draggable={false} />;
}

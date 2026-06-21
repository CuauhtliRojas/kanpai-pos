import type { ButtonHTMLAttributes, ReactNode } from "react";

type BrutalButtonVariant = "primary" | "secondary" | "danger" | "success" | "warning" | "ghost";
type BrutalButtonSize = "sm" | "md" | "lg";

type BrutalButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: BrutalButtonVariant;
  size?: BrutalButtonSize;
  fullWidth?: boolean;
};

const variantClassName: Record<BrutalButtonVariant, string> = {
  primary:
    "border-[var(--kp-ink)] bg-[var(--kp-accent)] text-[var(--kp-accent-contrast)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
  secondary:
    "border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
  danger:
    "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
  success:
    "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
  warning:
    "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
  ghost:
    "border-[var(--kp-ink)] bg-[var(--kp-bg)] text-[var(--kp-text-on-dark)] shadow-[var(--kp-shadow-hard)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
};

const sizeClassName: Record<BrutalButtonSize, string> = {
  sm: "min-h-[var(--kp-touch-sm)] px-3 text-xs",
  md: "min-h-[var(--kp-touch-md)] px-4 text-sm",
  lg: "min-h-[var(--kp-touch-lg)] px-6 text-lg",
};

export function BrutalButton({
  children,
  variant = "secondary",
  size = "md",
  fullWidth = false,
  className = "",
  disabled,
  ...props
}: BrutalButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled}
      className={[
        "inline-flex items-center justify-center gap-2 border-4 font-black uppercase tracking-[0.08em] transition-[transform,box-shadow,opacity]",
        "focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[var(--kp-info)]",
        "disabled:translate-x-0 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-45 disabled:shadow-none",
        variantClassName[variant],
        sizeClassName[size],
        fullWidth ? "w-full" : "",
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}

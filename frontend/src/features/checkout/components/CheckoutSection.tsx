import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";

type CheckoutSectionProps = {
  title: string;
  summary?: string;
  defaultOpen?: boolean;
  tone?: "default" | "warning" | "danger";
  children: ReactNode;
};

const toneClassName = {
  default: "bg-[var(--kp-surface-raised)]",
  warning: "bg-[var(--kp-warning-bg)]",
  danger: "bg-[var(--kp-danger-bg)]",
};

export function CheckoutSection({
  title,
  summary,
  defaultOpen = false,
  tone = "default",
  children,
}: CheckoutSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <section className="border-2 border-[var(--kp-ink)]">
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
        className={`flex min-h-[var(--kp-touch-md)] w-full items-center justify-between gap-3 px-3 py-2 text-left ${toneClassName[tone]}`}
      >
        <span className="min-w-0">
          <span className="block font-black uppercase">{title}</span>
          {summary ? (
            <span className="block truncate text-sm font-bold text-[var(--kp-muted)]">{summary}</span>
          ) : null}
        </span>
        <ChevronDown
          aria-hidden="true"
          className={`h-5 w-5 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen ? <div className="border-t-2 border-[var(--kp-ink)] p-3">{children}</div> : null}
    </section>
  );
}

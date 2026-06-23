import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { ProductionOrderStatus } from "../types/productionTypes";

type ProductionActionBarProps = {
  status: ProductionOrderStatus;
  isPending: boolean;
  compact?: boolean;
  onAccept: () => void;
  onStart: () => void;
  onFinish: () => void;
  onDeliver: () => void;
};

export function ProductionActionBar({
  status,
  isPending,
  compact = false,
  onAccept,
  onStart,
  onFinish,
  onDeliver,
}: ProductionActionBarProps) {
  const buttonSize = compact ? "sm" : "lg";
  const buttonClassName = compact ? "px-3 text-xs" : "";

  if (status === "En cola") {
    return (
      <div className="grid gap-2">
        <BrutalButton
          variant="warning"
          size={buttonSize}
          onClick={onAccept}
          disabled={isPending}
          fullWidth
          className={buttonClassName}
        >
          {isPending ? "Recibiendo..." : "Recibir"}
        </BrutalButton>
        {!compact ? (
          <p className="text-sm font-bold text-[var(--kp-muted)]">La estación confirma que vio la comanda.</p>
        ) : null}
      </div>
    );
  }
  if (status === "Recibida") {
    return (
      <div className="grid gap-2">
        <BrutalButton
          variant="primary"
          size={buttonSize}
          onClick={onStart}
          disabled={isPending}
          fullWidth
          className={buttonClassName}
        >
          {isPending ? "Marcando..." : "Preparar"}
        </BrutalButton>
        {!compact ? (
          <p className="text-sm font-bold text-[var(--kp-muted)]">Marca que ya se está preparando.</p>
        ) : null}
      </div>
    );
  }
  if (status === "En preparacion") {
    return (
      <div className="grid gap-2">
        <BrutalButton
          variant="success"
          size={buttonSize}
          onClick={onFinish}
          disabled={isPending}
          fullWidth
          className={buttonClassName}
        >
          {isPending ? "Marcando..." : "Marcar lista"}
        </BrutalButton>
        {!compact ? (
          <p className="text-sm font-bold text-[var(--kp-muted)]">La comanda ya está lista para entregar.</p>
        ) : null}
      </div>
    );
  }
  if (status === "Terminada") {
    return (
      <div className="grid gap-2">
        <BrutalButton
          variant="success"
          size={buttonSize}
          onClick={onDeliver}
          disabled={isPending}
          fullWidth
          className={buttonClassName}
        >
          {isPending ? "Entregando..." : "Entregar"}
        </BrutalButton>
        {!compact ? (
          <p className="text-sm font-bold text-[var(--kp-muted)]">Confirma que salió al cliente.</p>
        ) : null}
      </div>
    );
  }
  if (status === "Entregada") {
    return (
      <p
        className={`border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-center font-black uppercase text-[var(--kp-muted)] ${
          compact ? "px-2 py-2 text-xs" : "p-3"
        }`}
      >
        {compact ? "Entregada" : "Comanda entregada"}
      </p>
    );
  }
  return null;
}

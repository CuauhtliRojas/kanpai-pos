import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { ProductionOrderStatus } from "../types/productionTypes";

type ProductionActionBarProps = {
  status: ProductionOrderStatus;
  isPending: boolean;
  onAccept: () => void;
  onStart: () => void;
  onFinish: () => void;
  onDeliver: () => void;
};

export function ProductionActionBar({
  status,
  isPending,
  onAccept,
  onStart,
  onFinish,
  onDeliver,
}: ProductionActionBarProps) {
  if (status === "En cola") {
    return <BrutalButton variant="warning" size="lg" onClick={onAccept} disabled={isPending} fullWidth>{isPending ? "Aceptando..." : "Aceptar"}</BrutalButton>;
  }
  if (status === "Recibida") {
    return <BrutalButton variant="primary" size="lg" onClick={onStart} disabled={isPending} fullWidth>{isPending ? "Iniciando..." : "Iniciar"}</BrutalButton>;
  }
  if (status === "En preparacion") {
    return <BrutalButton variant="success" size="lg" onClick={onFinish} disabled={isPending} fullWidth>{isPending ? "Terminando..." : "Terminar"}</BrutalButton>;
  }
  if (status === "Terminada") {
    return <BrutalButton variant="success" size="lg" onClick={onDeliver} disabled={isPending} fullWidth>{isPending ? "Entregando..." : "Entregar"}</BrutalButton>;
  }
  return null;
}

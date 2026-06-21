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
    return <BrutalButton onClick={onAccept} disabled={isPending} fullWidth>Aceptar</BrutalButton>;
  }
  if (status === "Recibida") {
    return <BrutalButton onClick={onStart} disabled={isPending} fullWidth>Iniciar</BrutalButton>;
  }
  if (status === "En preparacion") {
    return <BrutalButton variant="success" onClick={onFinish} disabled={isPending} fullWidth>Terminar</BrutalButton>;
  }
  if (status === "Terminada") {
    return <BrutalButton variant="success" onClick={onDeliver} disabled={isPending} fullWidth>Entregar</BrutalButton>;
  }
  return null;
}

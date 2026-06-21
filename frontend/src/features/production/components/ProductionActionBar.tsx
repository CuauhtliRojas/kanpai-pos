import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { ProductionOrderStatus } from "../types/productionTypes";

type ProductionActionBarProps = {
  status: ProductionOrderStatus;
  isPending: boolean;
  onAccept: () => void;
  onStart: () => void;
  onFinish: () => void;
};

export function ProductionActionBar({
  status,
  isPending,
  onAccept,
  onStart,
  onFinish,
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
  return null;
}

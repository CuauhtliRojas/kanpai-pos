import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useRunAirtableSyncMutation } from "../hooks/useRunAirtableSyncMutation";

type SyncActionPanelProps = {
  canRun: boolean;
  disabled: boolean;
};

export function SyncActionPanel({ canRun, disabled }: SyncActionPanelProps) {
  const [confirming, setConfirming] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const runMutation = useRunAirtableSyncMutation();

  if (!canRun) return null;

  return (
    <div className="border-t-2 border-[var(--kp-divider)] pt-4">
      {confirming ? (
        <div className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] p-3">
          <p className="font-bold text-[var(--kp-warning-text)]">
            La actualización revisará la entrada y salida de datos. Continúa solo si la operación está lista.
          </p>
          <div className="flex flex-wrap gap-3">
            <BrutalButton
              size="sm"
              onClick={() => {
                setMessage(null);
                void runMutation.mutateAsync({
                  dry_run: false,
                  confirm: "RUN_AIRTABLE_SYNC_NOW",
                  force_pull_during_active_shift: false,
                }).then((result) => {
                  setMessage(
                    result.status.includes("error")
                      ? "Revisar conexión o pedir ayuda"
                      : result.status === "success"
                        ? "Datos al día"
                        : "Actualización pendiente",
                  );
                  setConfirming(false);
                }).catch(() => {
                  setMessage("Revisar conexión o pedir ayuda");
                  setConfirming(false);
                });
              }}
              disabled={disabled || runMutation.isPending}
            >
              Actualizar ahora
            </BrutalButton>
            <BrutalButton size="sm" variant="secondary" onClick={() => setConfirming(false)} disabled={runMutation.isPending}>
              Volver
            </BrutalButton>
          </div>
        </div>
      ) : (
        <BrutalButton size="sm" onClick={() => setConfirming(true)} disabled={disabled || runMutation.isPending}>
          Actualizar ahora
        </BrutalButton>
      )}
      {message ? <p className="mt-3 font-black">{message}</p> : null}
    </div>
  );
}

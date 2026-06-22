import { useEffect, useId, useState } from "react";
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
  const titleId = useId();

  useEffect(() => {
    if (!confirming) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !runMutation.isPending) {
        setConfirming(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [confirming, runMutation.isPending]);

  const closeModal = () => {
    if (runMutation.isPending) return;
    setConfirming(false);
  };

  const runSync = () => {
    setMessage(null);
    void runMutation
      .mutateAsync({
        dry_run: false,
        confirm: "RUN_AIRTABLE_SYNC_NOW",
        force_pull_during_active_shift: false,
      })
      .then((result) => {
        setMessage(
          result.status.includes("error")
            ? "Revisar sistema o pedir ayuda"
            : result.status === "success"
              ? "Datos al día"
              : "Actualización pendiente",
        );
        setConfirming(false);
      })
      .catch(() => {
        setMessage("Revisar sistema o pedir ayuda");
        setConfirming(false);
      });
  };

  if (!canRun) return null;

  return (
    <div className="border-t-2 border-[var(--kp-divider)] pt-4">
      <BrutalButton
        size="md"
        onClick={() => setConfirming(true)}
        disabled={disabled || runMutation.isPending}
      >
        Actualizar ahora
      </BrutalButton>

      {confirming ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.62)] p-4"
          onClick={closeModal}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="w-full max-w-lg border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)] md:p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id={titleId} className="text-2xl font-black uppercase leading-none">
              Actualizar datos
            </h2>
            <p className="mt-4 font-bold leading-6 text-[var(--kp-muted)]">
              Esto revisa cambios del catálogo y guarda movimientos pendientes para oficina. Puede
              tardar unos minutos. No cierres la aplicación mientras termina.
            </p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <BrutalButton
                autoFocus
                size="md"
                variant="success"
                onClick={runSync}
                disabled={disabled || runMutation.isPending}
                fullWidth
              >
                {runMutation.isPending ? "Actualizando" : "Actualizar ahora"}
              </BrutalButton>
              <BrutalButton
                size="md"
                variant="danger"
                onClick={closeModal}
                disabled={runMutation.isPending}
                fullWidth
              >
                Volver
              </BrutalButton>
            </div>
          </div>
        </div>
      ) : null}

      {message ? <p className="mt-3 font-black">{message}</p> : null}
    </div>
  );
}

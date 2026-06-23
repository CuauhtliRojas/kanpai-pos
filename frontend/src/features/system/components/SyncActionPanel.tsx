import { useEffect, useId, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { AirtableSyncRunResponse } from "../types/systemTypes";
import {
  usePullAirtableCatalogMutation,
  usePushAirtableMovementsMutation,
  useRunAirtableSyncMutation,
} from "../hooks/useRunAirtableSyncMutation";

type SyncActionPanelProps = {
  canRun: boolean;
  syncEnabled: boolean;
  pullEnabled: boolean;
  pushEnabled: boolean;
  running: boolean;
};

type ActionKind = "pull" | "push" | "run" | "force-pull";
type ResultTone = "success" | "warning" | "danger";

type ResultMessage = {
  text: string;
  tone: ResultTone;
  canForcePull?: boolean;
};

const resultClassName: Record<ResultTone, string> = {
  success:
    "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
  warning:
    "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  danger:
    "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
};

const actionCopy: Record<ActionKind, { title: string; body: string; confirmLabel: string }> = {
  pull: {
    title: "Recibir catálogo y fotos",
    body: "Trae cambios del catálogo y descarga fotos de productos. Si hay caja o cuentas activas, la descarga se puede omitir para no afectar ventas en curso.",
    confirmLabel: "Recibir catálogo y fotos",
  },
  push: {
    title: "Enviar movimientos",
    body: "Envía movimientos pendientes a oficina. No cambia el catálogo local.",
    confirmLabel: "Enviar movimientos",
  },
  run: {
    title: "Actualizar todo",
    body: "Recibe catálogo y fotos, y también envía movimientos pendientes. Si hay operación activa, el catálogo y las fotos se pueden omitir.",
    confirmLabel: "Actualizar todo",
  },
  "force-pull": {
    title: "Forzar descarga de catálogo y fotos",
    body: "Esto puede cambiar productos mientras se está operando. Úsalo solo si sabes que no afectará ventas en curso.",
    confirmLabel: "Forzar descarga",
  },
};

function isPullSkipped(result: AirtableSyncRunResponse) {
  return (
    result.status === "success_pull_skipped_active_operation" ||
    result.pull?.status === "skipped_active_operation"
  );
}

function hasError(result: AirtableSyncRunResponse) {
  return (
    result.status.includes("error") ||
    result.pull?.status === "error" ||
    result.push?.status === "error"
  );
}

function resultMessage(action: ActionKind, result: AirtableSyncRunResponse): ResultMessage {
  if (isPullSkipped(result)) {
    return {
      text:
        action === "run"
          ? "Se enviaron movimientos, pero no se recibió catálogo ni fotos porque hay operación activa."
          : "No se recibió catálogo ni fotos porque hay operación activa.",
      tone: "warning",
      canForcePull: true,
    };
  }

  if (hasError(result)) {
    if (action === "push") {
      return {
        text: "No se pudieron enviar movimientos. Revisa conexión y credenciales.",
        tone: "danger",
      };
    }
    return {
      text: "No se pudo recibir catálogo y fotos. Revisa conexión y credenciales.",
      tone: "danger",
    };
  }

  if (action === "pull" || action === "force-pull") {
    return { text: "Catálogo y fotos actualizados.", tone: "success" };
  }

  if (action === "push") {
    return { text: "Movimientos enviados.", tone: "success" };
  }

  return { text: "Datos actualizados.", tone: "success" };
}

export function SyncActionPanel({
  canRun,
  syncEnabled,
  pullEnabled,
  pushEnabled,
  running,
}: SyncActionPanelProps) {
  const [activeAction, setActiveAction] = useState<ActionKind | null>(null);
  const [message, setMessage] = useState<ResultMessage | null>(null);
  const pullMutation = usePullAirtableCatalogMutation();
  const pushMutation = usePushAirtableMovementsMutation();
  const runMutation = useRunAirtableSyncMutation();
  const titleId = useId();

  const isPending =
    pullMutation.isPending || pushMutation.isPending || runMutation.isPending || running;

  useEffect(() => {
    if (!activeAction) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isPending) {
        setActiveAction(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeAction, isPending]);

  const closeModal = () => {
    if (isPending) return;
    setActiveAction(null);
  };

  const executeAction = (action: ActionKind) => {
    setMessage(null);
    const forcePull = action === "force-pull";
    const mutation =
      action === "push" ? pushMutation : action === "run" ? runMutation : pullMutation;
    const confirm =
      action === "push"
        ? "PUSH_SQLITE_TO_AIRTABLE"
        : action === "run"
          ? "RUN_AIRTABLE_SYNC_NOW"
          : "PULL_AIRTABLE_TO_SQLITE";

    void mutation
      .mutateAsync({
        dry_run: false,
        confirm,
        force_pull_during_active_shift: forcePull,
      })
      .then((result) => {
        setMessage(resultMessage(action, result));
        setActiveAction(null);
      })
      .catch(() => {
        setMessage({
          text:
            action === "push"
              ? "No se pudieron enviar movimientos. Revisa conexión y credenciales."
              : "No se pudo recibir catálogo y fotos. Revisa conexión y credenciales.",
          tone: "danger",
        });
        setActiveAction(null);
      });
  };

  if (!canRun) return null;

  const canPull = syncEnabled && pullEnabled && !isPending;
  const canPush = syncEnabled && pushEnabled && !isPending;
  const canRunAll = syncEnabled && (pullEnabled || pushEnabled) && !isPending;
  const modalCopy = activeAction ? actionCopy[activeAction] : null;

  return (
    <div className="grid gap-3 border-t-2 border-[var(--kp-divider)] pt-3">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <p className="max-w-2xl text-sm font-bold leading-5 text-[var(--kp-muted)]">
          Revisión automática activa. Para traer cambios del catálogo y fotos, usa Recibir catálogo.
        </p>
        <div className="flex flex-wrap gap-2">
          <BrutalButton
            size="sm"
            variant="primary"
            onClick={() => setActiveAction("pull")}
            disabled={!canPull}
          >
            Recibir catálogo y fotos
          </BrutalButton>
          <BrutalButton size="sm" onClick={() => setActiveAction("push")} disabled={!canPush}>
            Enviar movimientos
          </BrutalButton>
          <BrutalButton size="sm" onClick={() => setActiveAction("run")} disabled={!canRunAll}>
            Actualizar todo
          </BrutalButton>
        </div>
      </div>

      {activeAction && modalCopy ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.62)] p-4"
          onClick={closeModal}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="w-full max-w-xl border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)] md:p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id={titleId} className="text-2xl font-black uppercase leading-none">
              {modalCopy.title}
            </h2>
            <p className="mt-4 font-bold leading-6 text-[var(--kp-muted)]">{modalCopy.body}</p>
            {activeAction === "pull" ? (
              <div className="mt-4 border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-3 text-sm font-black text-[var(--kp-warning-contrast)]">
                Si necesitas recibir catálogo y fotos durante operación activa, usa la descarga
                forzada solo después de confirmar que no afectará ventas en curso.
              </div>
            ) : null}
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <BrutalButton
                autoFocus
                size="md"
                variant={activeAction === "force-pull" ? "warning" : "success"}
                onClick={() => executeAction(activeAction)}
                disabled={isPending}
                fullWidth
              >
                {isPending ? "Actualizando" : modalCopy.confirmLabel}
              </BrutalButton>
              {activeAction === "pull" ? (
                <BrutalButton
                  size="md"
                  variant="warning"
                  onClick={() => setActiveAction("force-pull")}
                  disabled={isPending}
                  fullWidth
                >
                  Forzar descarga de catálogo y fotos
                </BrutalButton>
              ) : null}
              <BrutalButton
                size="md"
                variant="danger"
                onClick={closeModal}
                disabled={isPending}
                fullWidth
              >
                Volver
              </BrutalButton>
            </div>
          </div>
        </div>
      ) : null}

      {message ? (
        <div className={`border-4 p-3 text-sm font-black ${resultClassName[message.tone]}`}>
          <p>{message.text}</p>
          {message.canForcePull ? (
            <BrutalButton
              type="button"
              size="sm"
              variant="warning"
              className="mt-3"
              onClick={() => setActiveAction("force-pull")}
              disabled={isPending}
            >
              Forzar descarga de catálogo y fotos
            </BrutalButton>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

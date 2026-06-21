import { CircleCheckBig, UserRound } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { DiningTable, Ticket } from "../types/tableTypes";

type ActiveTicketPanelProps = {
  table: DiningTable | null;
  ticket: Ticket | null;
  isOpening: boolean;
  isLoadingTicket: boolean;
  errorMessage: string | null;
  onOpen: (table: DiningTable) => Promise<void>;
  onContinue: (table: DiningTable, ticket: Ticket) => void;
};

export function ActiveTicketPanel({
  table,
  ticket,
  isOpening,
  isLoadingTicket,
  errorMessage,
  onOpen,
  onContinue,
}: ActiveTicketPanelProps) {
  if (!table) {
    return (
      <aside className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 shadow-[var(--kp-shadow-hard)]">
        <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Mesa actual</p>
        <h2 className="mt-1 text-2xl font-black uppercase">Sin mesa</h2>
        <p className="mt-3 font-bold text-[var(--kp-muted)]">Elige una mesa para comenzar.</p>
      </aside>
    );
  }

  const isFree = table.status === "Libre";
  const ticketMatchesTable = ticket?.table_id === table.id;

  return (
    <aside className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 shadow-[var(--kp-shadow-hard)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Mesa actual</p>
      <h2 className="mt-2 text-3xl font-black uppercase">{table.display_name}</h2>

      {isLoadingTicket ? (
        <p className="mt-4 font-black uppercase">Consultando cuenta...</p>
      ) : ticketMatchesTable ? (
        <div className="mt-4 grid gap-4">
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-4 text-[var(--kp-success-text)]">
            <div className="flex items-center gap-3">
              <CircleCheckBig className="h-8 w-8" />
              <div>
                <p className="text-xl font-black uppercase">Cuenta abierta</p>
                <p className="font-bold">{ticket.folio}</p>
              </div>
            </div>
            <p className="mt-3 flex items-center gap-2 font-bold">
              <UserRound className="h-5 w-5" />
              Personas: {ticket.guest_count}
            </p>
          </div>
          <BrutalButton
            type="button"
            variant="warning"
            size="lg"
            fullWidth
            onClick={() => onContinue(table, ticket)}
          >
            Abrir cuenta activa
          </BrutalButton>
        </div>
      ) : isFree ? (
        <div className="mt-4 grid gap-4">
          <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-success-bg)] p-4 text-lg font-black uppercase text-[var(--kp-success-text)]">
            Mesa libre
          </p>
          <BrutalButton
            type="button"
            variant="warning"
            size="lg"
            fullWidth
            disabled={isOpening}
            onClick={() => void onOpen(table)}
          >
            {isOpening ? "Abriendo cuenta..." : "Abrir cuenta"}
          </BrutalButton>
        </div>
      ) : (
        <div className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-info-bg)] p-4 text-[var(--kp-text)]">
          <p className="text-xl font-black uppercase">Cuenta abierta</p>
          <p className="mt-2 font-bold">Esta mesa ya está ocupada.</p>
        </div>
      )}

      {errorMessage ? (
        <p className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
          {errorMessage}
        </p>
      ) : null}
    </aside>
  );
}

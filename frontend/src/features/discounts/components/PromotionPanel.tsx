export function PromotionPanel() {
  return (
    <div className="border-t-2 border-[var(--kp-divider)] pt-3">
      <div className="flex items-center justify-between gap-3">
        <p className="font-black uppercase">Promociones</p>
        <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-xs font-black uppercase">No disponible en esta versión</span>
      </div>
    </div>
  );
}

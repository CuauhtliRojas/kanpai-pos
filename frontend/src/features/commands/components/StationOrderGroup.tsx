import type { StationOrder } from "../types/commandTypes";

type StationOrderGroupProps = {
  stationName: string;
  orders: StationOrder[];
};

export function StationOrderGroup({ stationName, orders }: StationOrderGroupProps) {
  return (
    <section className="border-t-2 border-zinc-700 pt-3 first:border-t-0 first:pt-0">
      <h3 className="text-lg font-black uppercase">{stationName}</h3>
      <div className="mt-2 grid gap-3">
        {orders.map((order) => (
          <div key={order.id} className="bg-zinc-900 p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="font-black">{order.folio}</p>
              <p className="text-sm font-bold text-[var(--kp-muted)]">{order.status}</p>
            </div>
            <ul className="mt-2 grid gap-1">
              {order.lines.map((line) => (
                <li key={line.id} className="flex justify-between gap-3 text-sm font-bold">
                  <span>{line.product_name_snapshot}</span>
                  <span className="shrink-0">{line.quantity}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

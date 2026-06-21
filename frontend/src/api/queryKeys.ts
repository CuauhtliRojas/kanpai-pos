export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  cash: {
    current: ["cash", "current"] as const,
    summary: (cashShiftId: number) => ["cash", "summary", cashShiftId] as const,
  },
  checkout: {
    current: (ticketId: number) => ["checkout", "current", ticketId] as const,
  },
  catalog: {
    categories: ["catalog", "categories"] as const,
    paymentMethods: ["catalog", "payment-methods"] as const,
    products: ["catalog", "products"] as const,
    stations: ["catalog", "stations"] as const,
  },
  commands: {
    stationOrders: (ticketId: number) =>
      ["commands", "station-orders", ticketId] as const,
  },
  payments: {
    list: (ticketId: number) => ["payments", "list", ticketId] as const,
  },
  tables: {
    list: ["tables", "list"] as const,
  },
  tickets: {
    detail: (ticketId: number) => ["tickets", "detail", ticketId] as const,
    lines: (ticketId: number) => ["tickets", "lines", ticketId] as const,
  },
  system: {
    health: ["system", "health"] as const,
    airtableSyncStatus: ["system", "airtable-sync-status"] as const,
  },
};

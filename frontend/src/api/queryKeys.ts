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
    productVariantGroups: (productId: number) =>
      ["catalog", "product-variant-groups", productId] as const,
  },
  commands: {
    stationOrders: (ticketId: number) =>
      ["commands", "station-orders", ticketId] as const,
  },
  discounts: {
    presets: ["discounts", "presets"] as const,
    ticket: (ticketId: number) => ["discounts", "ticket", ticketId] as const,
  },
  payments: {
    list: (ticketId: number) => ["payments", "list", ticketId] as const,
  },
  production: {
    stations: ["production", "stations"] as const,
    orders: (
      params?: number | { stationId?: number; status?: string; dateFrom?: string; dateTo?: string },
    ) => {
      if (typeof params === "number" || params === undefined) {
        return ["production", "orders", params ?? "all"] as const;
      }
      return [
        "production",
        "orders",
        {
          stationId: params.stationId ?? "all",
          status: params.status ?? "all",
          dateFrom: params.dateFrom ?? "all",
          dateTo: params.dateTo ?? "all",
        },
      ] as const;
    },
  },
  printing: {
    jobs: ["printing", "jobs"] as const,
    pending: ["printing", "jobs", "pending"] as const,
    job: (printJobId: number) => ["printing", "jobs", printJobId] as const,
  },
  ticketHistory: {
    all: ["ticket-history"] as const,
    list: (filters: unknown) => ["ticket-history", "list", filters] as const,
    detail: (ticketId: number) => ["ticket-history", "detail", ticketId] as const,
  },
  reports: {
    dailySales: ["reports", "daily-sales"] as const,
    inventoryConsumption: ["reports", "inventory-consumption"] as const,
    salesByProduct: ["reports", "sales-by-product"] as const,
    salesByPaymentMethod: ["reports", "sales-by-payment-method"] as const,
    productionTimes: ["reports", "production-times"] as const,
    printJobs: ["reports", "print-jobs"] as const,
  },
  audit: {
    events: ["audit", "events"] as const,
    ticket: (ticketId: number) => ["audit", "ticket", ticketId] as const,
    cashShift: (cashShiftId: number) => ["audit", "cash-shift", cashShiftId] as const,
  },
  tables: {
    list: ["tables", "list"] as const,
  },
  tickets: {
    detail: (ticketId: number) => ["tickets", "detail", ticketId] as const,
    lines: (ticketId: number) => ["tickets", "lines", ticketId] as const,
    splits: (ticketId: number) => ["tickets", "splits", ticketId] as const,
  },
  inventory: {
    items: ["inventory", "items"] as const,
    stockAlerts: ["inventory", "stock-alerts"] as const,
    movements: (params: unknown) => ["inventory", "movements", params] as const,
  },
  security: {
    employees: ["security", "employees"] as const,
  },
  system: {
    health: ["system", "health"] as const,
    airtableSyncStatus: ["system", "airtable-sync-status"] as const,
  },
};

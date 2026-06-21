export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  system: {
    health: ["system", "health"] as const,
    airtableSyncStatus: ["system", "airtable-sync-status"] as const,
  },
};

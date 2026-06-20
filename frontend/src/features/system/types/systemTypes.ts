export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  database: string;
};

export type AirtableSyncStatus = {
  enabled: boolean;
  interval_minutes: number;
  pull_enabled: boolean;
  push_enabled: boolean;
  running: boolean;
  last_started_at: string | null;
  last_finished_at: string | null;
  last_status: string;
  last_error: string | null;
};

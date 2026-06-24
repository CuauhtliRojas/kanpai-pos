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

export type AirtableSyncRunRequest = {
  confirm: string;
  force_pull_during_active_shift: boolean;
};

export type AirtableSyncDirectionResult = {
  status: string;
  errors: number;
  warnings: number;
  error_messages: string[];
  warning_messages: string[];
};

export type AirtableSyncRunResponse = {
  accepted: boolean;
  status: string;
  mode: string;
  error?: string | null;
  pull?: AirtableSyncDirectionResult | null;
  push?: AirtableSyncDirectionResult | null;
  pull_requested?: boolean;
  push_requested?: boolean;
};

export type DatabaseStatus = {
  status: string;
  database: string;
};

export type SeedSummary = {
  business_settings: number;
  tables: number;
  categories: number;
  stations: number;
  payment_methods: number;
  employees: number;
};

export type PreflightCheckStatus = "OK" | "WARNING" | "ERROR" | string;

export type PreflightCheck = {
  key: string;
  status: PreflightCheckStatus;
  message: string;
};

export type PreflightSummary = {
  active_cash_shifts: number;
  open_tickets: number;
  in_payment_tickets: number;
  pending_print_jobs: number;
  failed_print_jobs: number;
  active_stock_alerts: number;
};

export type PreflightResponse = {
  status: PreflightCheckStatus;
  database: string;
  checks: PreflightCheck[];
  summary: PreflightSummary;
};

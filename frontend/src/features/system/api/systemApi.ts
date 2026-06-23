import { apiRequest } from "../../../api/http";
import type {
  AirtableSyncStatus,
  DatabaseStatus,
  AirtableSyncRunRequest,
  AirtableSyncRunResponse,
  HealthResponse,
  PreflightResponse,
  SeedSummary,
} from "../types/systemTypes";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export function getAirtableSyncStatus(): Promise<AirtableSyncStatus> {
  return apiRequest<AirtableSyncStatus>("/api/v1/system/airtable-sync");
}

export function runAirtableSync(payload: AirtableSyncRunRequest): Promise<AirtableSyncRunResponse> {
  return apiRequest<AirtableSyncRunResponse>("/api/v1/system/airtable-sync/run", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: 120_000,
  });
}

export function pullAirtableCatalog(
  payload: AirtableSyncRunRequest,
): Promise<AirtableSyncRunResponse> {
  return apiRequest<AirtableSyncRunResponse>("/api/v1/system/airtable-sync/pull", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: 120_000,
  });
}

export function pushAirtableMovements(
  payload: AirtableSyncRunRequest,
): Promise<AirtableSyncRunResponse> {
  return apiRequest<AirtableSyncRunResponse>("/api/v1/system/airtable-sync/push", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: 120_000,
  });
}

export function getDatabaseStatus(sessionToken: string): Promise<DatabaseStatus> {
  return apiRequest<DatabaseStatus>("/api/v1/system/db", {
    headers: { "X-Kanpai-Session": sessionToken },
  });
}

export function getSeedSummary(sessionToken: string): Promise<SeedSummary> {
  return apiRequest<SeedSummary>("/api/v1/system/seed-summary", {
    headers: { "X-Kanpai-Session": sessionToken },
  });
}

export function getPreflight(sessionToken: string): Promise<PreflightResponse> {
  return apiRequest<PreflightResponse>("/api/v1/preflight/local-backend", {
    headers: { "X-Kanpai-Session": sessionToken },
  });
}

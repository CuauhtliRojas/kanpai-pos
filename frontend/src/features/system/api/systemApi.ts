import { apiRequest } from "../../../api/http";
import type {
  AirtableSyncStatus,
  AirtableSyncRunRequest,
  AirtableSyncRunResponse,
  HealthResponse,
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

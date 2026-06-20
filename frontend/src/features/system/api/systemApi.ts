import { apiRequest } from "../../../api/http";
import type {
  AirtableSyncStatus,
  HealthResponse,
} from "../types/systemTypes";

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export function getAirtableSyncStatus(): Promise<AirtableSyncStatus> {
  return apiRequest<AirtableSyncStatus>("/api/v1/system/airtable-sync");
}

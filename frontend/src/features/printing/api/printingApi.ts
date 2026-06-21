import { apiRequest } from "../../../api/http";
import type { PrintJob, ReprintInput, RetryPrintJobsResponse } from "../types/printingTypes";

export function getPendingPrintJobs(): Promise<PrintJob[]> {
  return apiRequest<PrintJob[]>("/api/v1/printing/jobs/pending");
}

export function retryFailedPrintJobs(): Promise<RetryPrintJobsResponse> {
  return apiRequest<RetryPrintJobsResponse>("/api/v1/printing/jobs/retry-failed", {
    method: "POST",
    body: JSON.stringify({ reset_all: false }),
  });
}

export function reprintJob(input: ReprintInput): Promise<PrintJob> {
  return apiRequest<PrintJob>(`/api/v1/printing/jobs/${input.jobId}/reprint`, {
    method: "POST",
    body: JSON.stringify({ employee_id: input.employeeId, reason: input.reason }),
  });
}

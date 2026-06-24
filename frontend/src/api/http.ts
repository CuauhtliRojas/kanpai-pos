import { API_BASE_URL } from "./apiConfig";

import { readSession } from "../features/auth/lib/sessionStorage";

type ApiRequestOptions = RequestInit & {
  timeoutMs?: number;
};

export class ApiError extends Error {
  status: number | null;
  details: unknown;

  constructor(message: string, status: number | null = null, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function readErrorBody(response: Response): Promise<unknown> {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs ?? 8_000);

  try {
    const headers = new Headers(options.headers);
    headers.set("Accept", headers.get("Accept") ?? "application/json");
    headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");

    const session = readSession();
    if (session && !headers.has("X-Kanpai-Session")) {
      headers.set("X-Kanpai-Session", session.sessionToken);
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers,
    });

    if (!response.ok) {
      const details = await readErrorBody(response);
      throw new ApiError(
        `El sistema respondio con error ${response.status}.`,
        response.status,
        details,
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("El sistema tardo demasiado en responder.");
    }

    throw new ApiError(
      "No se pudo conectar con el sistema local. Verifica que Kanpai este iniciado en esta computadora.",
      null,
      error,
    );
  } finally {
    window.clearTimeout(timeout);
  }
}


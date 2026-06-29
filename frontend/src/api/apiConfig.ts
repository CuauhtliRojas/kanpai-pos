const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

let cachedApiBaseUrl: string | null = null;

function normalizeBaseUrl(value: string | null | undefined): string {
  const raw = value?.trim() || DEFAULT_API_BASE_URL;
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

async function readTauriApiBaseUrl(): Promise<string | null> {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const value = await invoke<string>("get_api_base_url");
    return normalizeBaseUrl(value);
  } catch {
    return null;
  }
}

export async function getApiBaseUrl(): Promise<string> {
  if (cachedApiBaseUrl) {
    return cachedApiBaseUrl;
  }

  const envBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (envBaseUrl?.trim()) {
    cachedApiBaseUrl = normalizeBaseUrl(envBaseUrl);
    return cachedApiBaseUrl;
  }

  cachedApiBaseUrl = (await readTauriApiBaseUrl()) ?? normalizeBaseUrl(DEFAULT_API_BASE_URL);
  return cachedApiBaseUrl;
}

export function getApiBaseUrlSync(): string {
  return cachedApiBaseUrl ?? normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
}

export async function buildApiUrl(path: string): Promise<string> {
  const baseUrl = await getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

export function buildApiUrlSync(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrlSync()}${normalizedPath}`;
}

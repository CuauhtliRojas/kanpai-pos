import { apiRequest } from "../../../api/http";
import type {
  LogoutResponse,
  MeResponse,
  PinLoginRequest,
  PinLoginResponse,
} from "../types/authTypes";

export function loginPin(payload: PinLoginRequest): Promise<PinLoginResponse> {
  return apiRequest<PinLoginResponse>("/api/v1/auth/login-pin", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMe(sessionToken: string): Promise<MeResponse> {
  return apiRequest<MeResponse>("/api/v1/auth/me", {
    headers: { "X-Kanpai-Session": sessionToken },
  });
}

export function logout(sessionToken: string): Promise<LogoutResponse> {
  return apiRequest<LogoutResponse>("/api/v1/auth/logout", {
    method: "POST",
    headers: { "X-Kanpai-Session": sessionToken },
    body: JSON.stringify({ session_token: sessionToken }),
  });
}

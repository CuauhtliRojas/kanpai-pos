export type PinLoginRequest = {
  employee_code: string;
  pin: string;
};

export type EmployeeAuthResponse = {
  id: number;
  employee_code: string;
  full_name: string;
  pos_alias: string | null;
};

export type PinLoginResponse = {
  employee: EmployeeAuthResponse;
  session_token: string;
  expires_at: string;
};

export type MeResponse = {
  employee: EmployeeAuthResponse;
  roles: string[];
  permissions: string[];
};

export type LogoutResponse = {
  status: string;
};

export type StoredAuthSession = {
  employee: EmployeeAuthResponse;
  sessionToken: string;
  expiresAt: string;
};

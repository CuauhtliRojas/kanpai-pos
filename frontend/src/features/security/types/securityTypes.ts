export type EmployeeListItem = {
  id: number;
  employee_code: string;
  full_name: string;
  pos_alias: string | null;
  active: boolean;
  sync_status: string;
};

export type Permission = {
  id: number;
  permission_key: string;
  description: string | null;
  active: boolean;
};

export type Role = {
  id: number;
  role_key: string;
  name: string;
  active: boolean;
  permissions: Permission[];
};

export type EmployeeDetail = {
  id: number;
  employee_code: string;
  full_name: string;
  pos_alias: string | null;
  active: boolean;
  sync_status: string;
  pin_enabled: boolean;
  last_login_at: string | null;
  roles: Role[];
};

export type EmployeePermissions = {
  employee_id: number;
  roles: Role[];
  permissions: Permission[];
};

export type Employee = EmployeeListItem;

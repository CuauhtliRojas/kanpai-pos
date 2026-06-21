import { useMutation } from "@tanstack/react-query";
import { logout } from "../api/authApi";

export function useLogoutMutation() {
  return useMutation({ mutationFn: logout });
}

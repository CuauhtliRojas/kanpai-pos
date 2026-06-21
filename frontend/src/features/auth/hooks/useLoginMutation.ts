import { useMutation } from "@tanstack/react-query";
import { loginPin } from "../api/authApi";

export function useLoginMutation() {
  return useMutation({ mutationFn: loginPin });
}

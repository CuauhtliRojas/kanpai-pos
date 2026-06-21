import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { AuthSessionProvider } from "../features/auth/context/AuthSessionProvider";
import { CurrentOperationProvider } from "../features/operations/context/CurrentOperationProvider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 15_000,
    },
  },
});

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthSessionProvider>
        <CurrentOperationProvider>{children}</CurrentOperationProvider>
      </AuthSessionProvider>
    </QueryClientProvider>
  );
}

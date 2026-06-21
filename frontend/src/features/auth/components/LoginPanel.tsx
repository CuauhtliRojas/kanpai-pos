import { useState } from "react";
import type { FormEvent } from "react";
import { LogIn } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useAuthSession } from "../hooks/useAuthSession";
import { PinKeypad } from "./PinKeypad";

const inputClassName =
  "h-[50px] w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-base font-black text-[var(--kp-text)] outline-none focus:border-[var(--kp-selected)]";

function getLoginErrorMessage(error: unknown): string {
  if (error instanceof ApiError && [400, 401, 403].includes(error.status ?? 0)) {
    return "Código o PIN incorrecto.";
  }
  return "No se pudo iniciar sesión. Revisa que Kanpai esté abierto.";
}

export function LoginPanel() {
  const { login } = useAuthSession();
  const [employeeCode, setEmployeeCode] = useState("");
  const [pin, setPin] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await login({ employee_code: employeeCode.trim(), pin });
    } catch (error) {
      setErrorMessage(getLoginErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="grid gap-2" onSubmit={submitLogin}>
      <label className="grid gap-1 text-sm font-black uppercase tracking-[0.08em]">
        Código de empleado
        <input
          type="text"
          value={employeeCode}
          onChange={(event) => setEmployeeCode(event.target.value)}
          autoComplete="username"
          autoCapitalize="characters"
          required
          disabled={isSubmitting}
          className={inputClassName}
        />
      </label>
      <label className="grid gap-1 text-sm font-black uppercase tracking-[0.08em]">
        PIN
        <input
          type="password"
          inputMode="numeric"
          value={pin}
          onChange={(event) => setPin(event.target.value.replace(/\D/g, ""))}
          autoComplete="current-password"
          required
          disabled={isSubmitting}
          className={inputClassName}
        />
      </label>
      <PinKeypad
        disabled={isSubmitting}
        onDigit={(digit) => setPin((currentPin) => `${currentPin}${digit}`)}
        onBackspace={() => setPin((currentPin) => currentPin.slice(0, -1))}
        onClear={() => setPin("")}
      />
      {errorMessage ? (
        <div role="alert" className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger)] px-3 py-2 text-sm font-black text-[var(--kp-danger-contrast)] shadow-[var(--kp-shadow-hard-sm)]">
          {errorMessage}
        </div>
      ) : null}
      <BrutalButton type="submit" variant="warning" size="md" fullWidth className="h-14 text-base" disabled={isSubmitting || !employeeCode.trim() || !pin}>
        <LogIn className="h-5 w-5" />
        {isSubmitting ? "Ingresando..." : "Iniciar sesión"}
      </BrutalButton>
    </form>
  );
}

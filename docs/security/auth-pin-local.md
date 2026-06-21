# Autenticación local por PIN

## Configuración

`KANPAI_ADMIN_PIN` define el PIN temporal del seed `EMP-0001`. En desarrollo el fallback es `1234`; debe cambiarse antes de producción. `KANPAI_SESSION_HOURS` controla la vigencia, con 12 horas por defecto.

El PIN nunca se guarda en claro. `hash_pin` contiene `pbkdf2_sha256$iteraciones$salt$hash`; la comparación es de tiempo constante.

## Flujo

1. `POST /api/v1/auth/login-pin` con `employee_code` y `pin`.
2. Guardar temporalmente `session_token`.
3. Consultar `GET /api/v1/auth/me` con `X-Kanpai-Session` para obtener empleado, roles y permisos.
4. Enviar el `employee_id` resultante en operaciones POS existentes.
5. `POST /api/v1/auth/logout` al terminar turno o bloquear pantalla.

Estados persistidos: `Activa`, `Cerrada`, `Expirada`. El token no sustituye todavía `employee_id`; esa transición requiere middleware global y queda fuera de esta fase.

QA: login válido, PIN incorrecto, expiración/cierre, roles y permisos, y comprobación directa de que `1234` no aparece en `hash_pin`.

## Frontera de administración y soporte

Las rutas `admin-support` y `admin-read-only` requieren `X-Kanpai-Session`. `SUPPORT_ACCESS` habilita diagnóstico local y `ADMIN_READ` habilita catálogos administrativos; el rol `ADMIN` se acepta para bases existentes que aún no hayan vuelto a ejecutar el seed.

Las respuestas de empleados nunca incluyen `pin_hash`. `POST /api/v1/notifications/sms/test` requiere además `SMS_SEND` y `"confirm": "SEND_SMS_TEST"`.

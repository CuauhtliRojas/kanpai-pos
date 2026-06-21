# Autenticación y sesión frontend V1 — Kanpai POS

## Flujo de acceso por PIN

Al abrir la aplicación, el frontend busca una sesión local vigente. Si existe, consulta la identidad actual antes de permitir el acceso. Una sesión ausente, expirada o rechazada lleva a `/login`. Un acceso correcto guarda la sesión y abre `/`; cerrar sesión intenta informar al servicio local, elimina siempre la copia local y regresa al acceso.

## Almacenamiento

La sesión se centraliza en `frontend/src/features/auth/lib/sessionStorage.ts` y actualmente usa `localStorage`. Guarda únicamente:

- `session_token` bajo el nombre interno `sessionToken`.
- Empleado autenticado.
- `expires_at` bajo el nombre interno `expiresAt`.

El PIN nunca se persiste. Tampoco se almacena información relacionada con Airtable. En una fase futura puede evaluarse migrar el token a almacenamiento seguro de Tauri.

## Contratos consumidos

- `POST /api/v1/auth/login-pin`: acceso con código de empleado y PIN.
- `GET /api/v1/auth/me`: validación y recuperación de identidad mediante `X-Kanpai-Session`.
- `POST /api/v1/auth/logout`: cierre de sesión.

## Interfaz operativa

La barra superior muestra `Cajero: <alias>` cuando existe `pos_alias`; de lo contrario muestra el nombre completo. La mesa permanece como `Mesa: Sin mesa` hasta una fase posterior. El menú hamburguesa contiene la acción `Cerrar sesión`.

Los mensajes visibles usan lenguaje de operación: iniciar sesión, código de empleado, PIN, cajero, mesa y problemas de acceso. No muestran tokens, contratos ni detalles internos.

## Pendientes

- Aplicar permisos y navegación cuando se defina la fase 3. Aunque `/auth/me` ya devuelve roles y permisos, esta fase no inventa ni habilita comportamiento basado en ellos.
- Evaluar almacenamiento seguro de Tauri para el token de sesión.
- Validar el flujo completo en Tauri con una credencial real de prueba.

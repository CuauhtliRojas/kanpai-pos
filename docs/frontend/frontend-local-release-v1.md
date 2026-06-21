# Release local — Kanpai POS Frontend v1

## Requisitos

| Herramienta | Versión mínima | Verificar |
| --- | --- | --- |
| Windows 10/11 (x64) | — | `winver` |
| Microsoft WebView2 Runtime | Cualquier versión reciente | Viene preinstalado en W10/11 actualizado |
| Node.js | 20 LTS | `node --version` |
| corepack | incluido con Node.js | `corepack --version` |
| pnpm | gestionado por corepack | `corepack pnpm --version` |
| Rust (rustup) | 1.70+ | `rustc --version` |
| Python | 3.12 | `python --version` |
| uv | 0.10+ | `uv --version` |

> **Nota:** Rust se instala via [rustup.rs](https://rustup.rs). Después de instalar, `~/.cargo/bin` debe estar en el PATH de sesión. En Windows puede requerir reiniciar la terminal.

---

## 1. Preparar el entorno (primera vez)

```powershell
# Habilitar corepack (solo una vez por máquina)
corepack enable

# Instalar dependencias del frontend
cd frontend
corepack pnpm install

# Instalar dependencias del backend
cd ..
uv sync

# Aplicar migraciones de base de datos (si es primera vez)
uv run alembic upgrade head
```

---

## 2. Variables de entorno necesarias

### Backend (archivo `.env` en la raíz del proyecto)

Copiar `.env.example` como `.env` y completar:

```env
# Obligatorio
DATABASE_URL=sqlite:///./data/kanpai_pos.db
KANPAI_ADMIN_PIN=<PIN del administrador>
KANPAI_SESSION_HOURS=12

# CORS — debe incluir el origen de Tauri dev
KANPAI_CORS_ORIGINS=http://localhost:1420,http://127.0.0.1:1420

# Airtable (opcional — dejar vacío para desactivar sincronización)
AIRTABLE_API_TOKEN=
AIRTABLE_BASE_ID=
AIRTABLE_SYNC_ENABLED=false
```

### Frontend (archivo `frontend/.env`)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Este archivo ya existe en el repositorio con el valor correcto para uso local.

---

## 3. Levantar el backend

```powershell
# Desde la raíz del proyecto
uv run uvicorn app.main:app --reload
```

El backend queda disponible en `http://127.0.0.1:8000`. Verificar salud:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

---

## 4. Correr el frontend en modo desarrollo

```powershell
# Requiere que el backend ya esté levantado
cd frontend
corepack pnpm tauri dev
```

Esto inicia la ventana Tauri en `1180×760` con recarga en caliente.

Login de prueba:
- Código: `EMP-0001`
- PIN: según `KANPAI_ADMIN_PIN` en el `.env`

---

## 5. Construir el frontend web (sin Tauri)

```powershell
cd frontend
corepack pnpm build
```

Salida en `frontend/dist/`. Útil para verificar TypeScript y el bundle antes de hacer el build nativo.

---

## 6. Construir la aplicación Tauri (instalador)

```powershell
# Verificar que Rust esté en PATH
rustc --version
# Si no responde: agregar %USERPROFILE%\.cargo\bin al PATH

cd frontend
corepack pnpm tauri build
```

El build compila el frontend web y luego la capa Rust/Tauri. Tarda ~3–5 minutos la primera vez (descarga y compila dependencias Rust).

---

## 7. Ubicación de los instaladores

Después de `corepack pnpm tauri build`:

| Archivo | Ruta | Tamaño |
| --- | --- | --- |
| Instalador MSI | `frontend/src-tauri/target/release/bundle/msi/Kanpai POS_0.1.0_x64_en-US.msi` | ~2.9 MB |
| Instalador NSIS | `frontend/src-tauri/target/release/bundle/nsis/Kanpai POS_0.1.0_x64-setup.exe` | ~1.9 MB |
| Ejecutable solo | `frontend/src-tauri/target/release/frontend.exe` | ~8.6 MB |

Para instalar en otra máquina: ejecutar el `.msi` o el `.exe` setup. WebView2 debe estar instalado en el destino.

---

## 8. Checklist de conexión

Antes de abrir la app verificar:

- [ ] Backend responde en `http://127.0.0.1:8000/health`
- [ ] OpenAPI accesible en `http://127.0.0.1:8000/openapi.json`
- [ ] CORS incluye `http://localhost:1420` y `http://127.0.0.1:1420`
- [ ] Base de datos existe en `data/kanpai_pos.db`
- [ ] Al menos un empleado activo con PIN configurado

---

## 9. Checklist de prueba E2E local

| Paso | Módulo | Modifica datos |
| ---: | --- | :---: |
| 1 | Login con código y PIN válidos | Sí (sesión) |
| 2 | Abrir caja | Sí |
| 3 | Abrir mesa y cuenta | Sí |
| 4 | Agregar producto a la cuenta | Sí |
| 5 | Enviar comanda | Sí |
| 6 | Ver producción — estaciones con comandas | No |
| 7 | Aceptar/iniciar/terminar comanda de prueba | Sí |
| 8 | Ver impresión — cola pendiente | No |
| 9 | Modificar o cancelar producto (motivo requerido) | Sí |
| 10 | Aplicar descuento o cortesía | Sí |
| 11 | Iniciar cobro y registrar pago | Sí |
| 12 | Confirmar mesa liberada | Sí |
| 13 | Ver reportes del día (solo ADMIN) | No |
| 14 | Ver auditoría (solo ADMIN) | No |
| 15 | Ver inventario — stock y alertas | No |
| 16 | Ajustar stock con insumo de prueba (solo INVENTORY_ADJUST) | Sí |
| 17 | Ver empleados (solo ADMIN) | No |
| 18 | Ver estado del sistema y sincronización | No |
| 19 | Cerrar sesión | Sí |

---

## 10. Problemas conocidos

### Airtable — sincronización

Si `AIRTABLE_API_TOKEN` o `AIRTABLE_BASE_ID` no están configurados o son inválidos, la sincronización fallará y la pantalla de Estado mostrará "Revisar conexión". Esto no afecta la operación local del POS (ventas, caja, inventario). Para desactivar la sincronización completamente: `AIRTABLE_SYNC_ENABLED=false`.

### Rust no en PATH (Windows)

Si `corepack pnpm tauri build` falla con "rustc no se reconoce", agregar manualmente al PATH de sesión:

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;" + $env:PATH
```

O agregar permanentemente en Configuración del sistema → Variables de entorno.

### Promociones — pendiente

No existe contrato de backend para catálogo o aplicación de promociones. La sección no está disponible.

### Ventas por categoría — pendiente

El reporte de ventas por categoría no tiene endpoint de backend actualmente.

### Roles y permisos por empleado — pendiente

La pantalla de Permisos/Empleados muestra solo nombre, código y estado activo/inactivo. Los endpoints de roles y permisos por empleado no existen en el contrato actual.

### beforeBuildCommand — corepack

El archivo `tauri.conf.json` usa `corepack pnpm build` en `beforeBuildCommand` para ser compatible con el entorno donde pnpm se gestiona via corepack. En entornos donde pnpm está instalado globalmente en PATH, esto también funciona correctamente.

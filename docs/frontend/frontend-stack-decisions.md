# Decisiones de stack frontend

## Tauri

Se usa Tauri para empaquetar una aplicacion nativa de escritorio ligera, adecuada para PC de produccion con recursos limitados.

## React + TypeScript + Vite

React cubre la composicion de UI; TypeScript estricto protege contratos; Vite mantiene ciclos de desarrollo rapidos.

## Tailwind CSS

Tailwind es el motor principal de layout. La identidad visual se concentra en `src/styles/theme.css`.

## React Router

Se usa como router SPA declarativo. No se adopta framework fullstack ni SSR.

## TanStack Query

Se usa para estado remoto de FastAPI: cache, loading, error, refetch e invalidacion futura.

## fetch nativo

No se agrega Axios en Foundation V1. El cliente HTTP queda centralizado en `src/api/http.ts`.

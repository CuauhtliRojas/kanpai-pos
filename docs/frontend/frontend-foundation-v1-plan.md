# Frontend Foundation V1

## Alcance

Esta fase crea la base de escritorio para Kanpai POS usando Tauri, React, TypeScript, Vite, Tailwind CSS, React Router y TanStack Query.

## Fuera de alcance

No implementa POS, carrito, ticket, cobro, comandas, impresion fisica ni edicion de catalogos.

## Contrato operativo

El frontend consume exclusivamente el Backend V1 local en `http://127.0.0.1:8000`.

No se conecta directo a Airtable, no maneja tokens Airtable y no lee `.env` del backend.

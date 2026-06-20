# Cuentas divididas y variantes

## Orden armable

`DEV-YAKITORI-ORDEN-3` tiene el grupo obligatorio `Sabores yakitori`, mínimo 3 y máximo 3. El payload de línea incluye tres objetos `variant_selections`. Cada selección se imprime debajo del producto, queda en auditoría y suma `price_delta_cents` al precio unitario. Si una opción apunta a `product_id`, al cobrar se consume la receta de ese producto además de la receta base.

Ejemplo: Pollo 1, Pulpo 1 y Verduras 1. Dos o cuatro piezas fallan antes de crear la línea.

Catálogo: `GET /api/v1/catalog/variant-groups` y `GET /api/v1/catalog/products/{id}/variant-groups`.

## División

El pago parcial normal sigue disponible en `POST /pos/tickets/{id}/payments`. La división formal ofrece:

- `POST /pos/tickets/{id}/splits/equal`: crea importes exactos y distribuye centavos residuales.
- `POST /pos/tickets/{id}/splits/by-lines`: asigna líneas completas no usadas.
- `GET /pos/tickets/{id}/splits`: consulta partes y líneas.
- `POST /pos/ticket-splits/{id}/payments`: registra pago, recibido y cambio.

No se divide un ticket cobrado o cancelado. En `En cobro`, el ticket solo pasa a `Cobrado` cuando pagos normales y pagos de divisiones cubren el total. Las divisiones usan `Abierta`, `Pagada` y `Cancelada`.

QA: partes iguales, líneas repetidas, cambio en efectivo, pago parcial sin cierre, cierre con última parte y eventos `Division de cuenta creada` / `Pago de division registrado`.

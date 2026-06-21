# POS: productos y cuenta activa (Fase 6)

## Alcance

La Fase 6 incorpora el catálogo táctil de productos en `/pos` y permite agregar una unidad de un producto a la cuenta activa. La pantalla mantiene la selección de mesa, da mayor espacio al catálogo y muestra las líneas actuales de la cuenta.

> Fase 6 captura productos en cuenta. No envía comanda. El envío de comanda se implementará en Fase 7 con confirmación explícita.

## Bloque A: catálogo visual

- Consulta categorías con `GET /api/v1/catalog/categories`.
- Consulta productos con `GET /api/v1/catalog/products`.
- Permite filtrar por categoría o mostrar todo el catálogo.
- Muestra nombre, precio y disponibilidad en tarjetas táctiles.
- El contrato actual de productos no incluye imagen. Por ello se muestra `product-placeholder.svg` mediante `brandAssets.productPlaceholder`. El componente de imagen también vuelve al placeholder si una imagen no puede cargarse.

## Bloque B: agregar producto

- Consulta la cuenta con `GET /api/v1/pos/tickets/{ticket_id}` mediante el flujo existente de mesas.
- Consulta sus líneas con `GET /api/v1/pos/tickets/{ticket_id}/lines`.
- Agrega una unidad con `POST /api/v1/pos/tickets/{ticket_id}/lines` usando los campos obligatorios confirmados por el contrato vivo: producto, empleado y cantidad `1`.
- Después del alta actualiza el detalle, las líneas y el estado de mesas. Los totales mostrados provienen de la respuesta del servicio.
- Requiere caja abierta, mesa seleccionada y cuenta activa. La interfaz guía al operador cuando falta alguno de estos pasos.

## Fuera de alcance

Esta fase no implementa variantes, notas, descuentos, cancelación de líneas, comandas, cobro, impresión ni edición del catálogo.

## QA esperado

1. Iniciar sesión y abrir caja.
2. Confirmar que categorías y productos cargan y que el filtro cambia el catálogo visible.
3. Confirmar que cada producto muestra el placeholder y su precio.
4. Seleccionar una mesa y abrir o continuar su cuenta.
5. Tocar un producto y confirmar que se agrega una unidad y se actualizan líneas y total.
6. Verificar los mensajes de guía sin mesa y sin cuenta.
7. Confirmar que la pantalla cabe y puede recorrerse en una ventana de 1180 × 760.

El paso 5 modifica datos y debe realizarse únicamente con una mesa y cuenta de prueba.

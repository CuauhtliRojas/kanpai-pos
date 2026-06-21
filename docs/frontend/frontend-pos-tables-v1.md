# Mesas y cuenta activa inicial

## Alcance de Fase 5

La ruta `/pos` valida que exista una caja abierta, consulta las mesas activas, permite seleccionar una mesa libre y abrir su cuenta. La mesa y cuenta actuales quedan disponibles en un contexto operativo compartido para las siguientes fases.

No se agregan productos, comandas, cobro ni impresión.

## Operaciones consumidas

- `GET /api/v1/pos/cash-shifts/current`
- `GET /api/v1/operations/tables`
- `POST /api/v1/pos/tables/{table_id}/open-ticket`
- `GET /api/v1/pos/tickets/{ticket_id}`

No existe una operación para buscar la cuenta activa mediante la mesa. La lista de mesas tampoco incluye el identificador de esa cuenta. Por ello, el detalle se recupera cuando la cuenta fue abierta y conocida durante la sesión actual; no se infiere para mesas previamente ocupadas.

## Dependencia con caja

POS reutiliza la consulta de caja actual. Sin una caja abierta muestra “Primero abre caja” y ofrece acceso a Caja. La consulta de mesas y la apertura de cuenta permanecen bloqueadas.

## Mesa actual

Seleccionar una tarjeta establece la mesa actual. La selección usa amarillo y se conserva al navegar dentro de la sesión. Cambiar de empleado o cerrar sesión limpia la operación actual.

## Cuenta activa

Abrir cuenta usa el empleado autenticado y el valor predeterminado de personas definido por el contrato. La respuesta completa se guarda como cuenta activa, se registra en caché y se actualiza la lista de mesas.

## Topbar

La barra superior muestra el cajero y `MESA: <nombre>` cuando hay selección. Sin selección muestra `MESA: SIN MESA`. Se priorizan el nombre y código legibles de la mesa.

## Fuera de alcance

No se muestran catálogos de productos, líneas de cuenta, modificadores, comandas, pagos ni trabajos de impresión. Tampoco se inventa un permiso de acceso a POS.

## QA esperado

1. Iniciar sesión y confirmar cajero y mesa sin seleccionar en la barra superior.
2. Entrar a POS sin caja y verificar el bloqueo y acceso a Caja.
3. Con caja abierta, verificar la cuadrícula responsive y los estados libre, ocupada y seleccionada.
4. Seleccionar una mesa libre y confirmar que aún no se modifica ningún dato.
5. En una mesa de prueba, abrir cuenta y comprobar que cambia a ocupada, aparece la cuenta activa y la barra superior muestra la mesa.
6. Navegar fuera y regresar para comprobar que la operación actual se conserva.
7. Cerrar sesión y confirmar que la mesa y cuenta actuales se limpian.

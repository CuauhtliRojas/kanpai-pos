# Permisos y navegación frontend V1 — Kanpai POS

## Datos de sesión

Después del acceso y al recuperar una sesión, el frontend consulta `/auth/me`. Conserva el empleado autenticado, sus roles y sus permisos para decidir la navegación y el acceso a rutas. El contrato sigue aceptando roles y permisos como listas de texto, mientras los permisos conocidos tienen tipos explícitos en el frontend.

## Roles y permisos conocidos

Los roles observados en el contrato actual son `ADMIN` y `CAJERO`. No se asignan capacidades por nombre de rol salvo que una opción futura declare explícitamente acceso administrativo.

Los permisos conocidos son:

- `CASH_SHIFT_OPEN`
- `CASH_SHIFT_CLOSE`
- `EXPENSE_CREATE`
- `DISCOUNT_AUTHORIZE`
- `INVENTORY_ADJUST`
- `REPRINT`
- `SMS_SEND`
- `TICKET_CANCEL`

## Decisión de navegación

Inicio y Estado están disponibles para toda sesión válida. Caja está disponible con al menos uno de `CASH_SHIFT_OPEN`, `CASH_SHIFT_CLOSE` o `EXPENSE_CREATE`. Impresión requiere `REPRINT` e Inventario requiere `INVENTORY_ADJUST`.

Una opción habilitada se puede abrir. Una opción sin la capacidad requerida se muestra como `Sin permiso` y su ruta presenta el mensaje de acceso restringido. Las opciones sin módulo construido se muestran como `Próximo` y abren un panel temporal, sin simular funcionalidad operativa.

## Módulos futuros

POS, Producción, Reportes, Auditoría y Permisos permanecen en preparación porque esta fase no dispone de pantalla operativa o de un permiso específico confirmado para habilitarlos.

## Mensaje para el operador

Cuando falta acceso, el operador ve:

> No tienes permiso para usar esta opción.  
> Pide ayuda al encargado.

## Fuera de alcance

Esta fase no implementa apertura o cierre de caja, venta, productos, producción, impresión real, inventario, cobro, reportes, auditoría ni administración de permisos. Tampoco cambia contratos ni servicios del servidor.

## Próxima fase sugerida

Caja operativa, reutilizando las reglas de acceso ya modeladas para apertura, cierre y registro de gastos.

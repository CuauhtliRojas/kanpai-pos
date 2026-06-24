# Reset productivo e inventario inicial

## Objetivo

Dejar la base SQLite local lista para el primer turno real de Kanpai POS sin
arrastrar datos QA, tickets de prueba, cortes, pagos, impresiones, movimientos
de inventario, recepciones de prueba, SMS, auditoría o sesiones antiguas.

## Qué se conserva

- Configuración del negocio.
- Empleados, roles, permisos, PIN/hash local y asignaciones de rol.
- Mesas, zonas, estaciones, impresoras lógicas y métodos de pago.
- Productos, variantes, paquetes, insumos, unidades, conversiones y recetas.
- Canales de notificación.
- Secuencias de folio, salvo que se use `--reset-folios`.

## Qué se elimina

- Sesiones POS y sesiones de empleado.
- Cortes, tickets, líneas, pagos, descuentos y divisiones.
- Comandas, órdenes de producción y trabajos de impresión.
- Gastos de caja.
- Recepciones de compra y líneas de recepción de prueba.
- Movimientos de inventario y alertas de stock.
- SMS enviados.
- Eventos de auditoría y cambios de estado de mesa.
- Autorizaciones operativas.

## Vista previa

```powershell
uv run python scripts/prepare_production_database.py
```

La vista previa no modifica datos.

Ejecución real
uv run python scripts/prepare_production_database.py `  --execute`
--confirm PREPARE_KANPAI_PRODUCTION_DB `
--reset-folios

El script crea respaldo previo en data/backups/.

Inventario inicial sin gasto

La carga inicial debe registrarse como recepción de inventario con monto pagado
en cero:

{
"supplier_name": "Inventario inicial",
"paid_amount_cents": 0,
"payment_method_id": null,
"note": "Carga inicial antes del primer turno real",
"lines": []
}

Regla vigente: si paid_amount_cents es 0, no se crea gasto de caja, no se
requiere corte abierto y no se asocia método de pago. La recepción sí genera
movimientos de inventario para dejar el stock inicial trazable.

Validación posterior
uv run python scripts/prepare_production_database.py
uv run python scripts/check_pre_sync_invariants.py
uv run pytest tests/test_operational_reset.py tests/test_inventory.py -q

---

## 3. En `tests/test_operational_reset.py`

Busca esta línea:

```python id="vnfoba"
from scripts.reset_operational_data import main, reset_operational_data

Reemplázala por esto:

from scripts.prepare_production_database import (
    CONFIRMATION,
    main as production_main,
    prepare_production_database,
)
from scripts.reset_operational_data import main, reset_operational_data
```

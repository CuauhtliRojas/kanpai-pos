# Impresión física en Windows

La impresión no se ejecuta desde frontend: el navegador no ofrece control fiable de cola, reintentos, idempotencia ni mapeo estable de impresoras. La API crea `PrintJob`; `scripts/print_worker_windows.py` reclama por `printer_key`, imprime el snapshot y marca `printed` o `failed`.

## Instalación

1. Copiar `scripts/print_worker_config.example.json` a `scripts/print_worker_config.json`.
2. Reemplazar cada valor por el nombre exacto mostrado por Windows.
3. Configurar el mismo secreto fuerte en `KANPAI_WORKER_KEY` del backend y en `worker_key` del JSON del worker, y reiniciar ambos procesos.
4. Si se imprimirá realmente, instalar `pywin32` en el entorno del worker. No es dependencia del backend y no se añadió automáticamente.
5. Validar con `scripts/run_print_worker_windows.ps1 -DryRun -Once`.
6. Ejecutar sin `-DryRun` y revisar `logs/print_worker.log`.

## Una computadora y tres impresoras

Un mapeo habitual es: `CAJA` a impresora de caja, `COCINA` a cocina, y `BARRA_FRIA`, `COCTELERIA`, `BARRA_CALIENTE` a la misma impresora física de barra. Cinco claves lógicas pueden apuntar a tres nombres físicos. `GET /api/v1/printing/printers` muestra las claves disponibles.

El worker usa `--once` para un ciclo de QA y `--dry-run` para reclamar y confirmar sin tocar hardware. Un error físico se reporta a `/failed`; la cola conserva el snapshot para reintento.

Los callbacks envían `X-Kanpai-Worker-Key`. Para migración, si `KANPAI_WORKER_KEY` está vacía en `local`, `dev` o `test`, el backend conserva compatibilidad temporal. Al configurarla, una clave ausente o incorrecta se rechaza. En otros entornos, no configurarla cierra los callbacks con `503`.

QA: backend en `127.0.0.1:8011`, trabajo pendiente por cada clave, ciclo dry-run, impresión de prueba, desconexión de una impresora, estado `Fallido`, reconexión y retry.

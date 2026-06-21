# Inventario y permisos — Frontend v1

## Bloque A — Inventario

### Contratos consumidos

| Endpoint | Método | Uso |
| --- | --- | --- |
| `/api/v1/inventory/items` | GET | Lista de insumos con stock actual, mínimo y estado |
| `/api/v1/inventory/stock-alerts/active` | GET | Alertas activas de bajo stock |
| `/api/v1/inventory/movements` | POST | Ajuste manual de stock (requiere `INVENTORY_ADJUST`) |

### Archivos creados

```
frontend/src/features/inventory/
  types/inventoryTypes.ts
  api/inventoryApi.ts
  hooks/useInventoryItemsQuery.ts
  hooks/useStockAlertsQuery.ts
  hooks/useInventoryMovementMutation.ts
  components/InventoryItemCard.tsx
  components/LowStockPanel.tsx
  components/InventoryAdjustmentDialog.tsx
  components/InventoryList.tsx
  pages/InventoryPage.tsx
```

### Comportamiento

- Todos los usuarios autenticados pueden ver el inventario (lectura).
- El botón "Ajustar" solo aparece si el usuario tiene el permiso `INVENTORY_ADJUST`.
- Sin el permiso se muestra aviso: "Solo lectura. Pide ayuda al encargado para ajustar inventario."
- Las alertas de bajo stock se muestran en panel amarillo si existen.
- El estado de stock proviene de `stock_status` del backend (`Disponible`, `Bajo stock`, `Agotado`).
- El ajuste usa `movement_type: "Ajuste manual"` y requiere cantidad (con signo) y motivo.
- Tras un ajuste exitoso se invalidan `inventory.items` y `inventory.stockAlerts`.

### Pendiente

- `GET /api/v1/inventory/movements` no existe en el contrato actual; el historial de movimientos no se muestra.
- `GET /api/v1/inventory/items/{id}/stock` existe pero no se usa; la lista ya incluye `current_stock`.

---

## Bloque B — Permisos / Empleados

### Contratos consumidos

| Endpoint | Método | Uso |
| --- | --- | --- |
| `/api/v1/operations/employees` | GET | Lista de empleados con estado activo/inactivo |

### Archivos creados

```
frontend/src/features/security/
  types/securityTypes.ts
  api/securityApi.ts
  hooks/useEmployeesQuery.ts
  components/EmployeeCard.tsx
  components/EmployeeList.tsx
  pages/SecurityPage.tsx
```

### Comportamiento

- Solo accesible para `ADMIN` (ruta protegida con `AdminRoute`).
- Vista de solo lectura: no expone PINs, tokens ni hashes.
- Los empleados se agrupan en Activos e Inactivos.
- Se muestra `full_name`, `pos_alias` (si difiere) y `employee_code`.
- Los endpoints `GET /api/v1/security/users`, `/security/roles` y `/security/permissions` no existen en el contrato actual; no se consumen.

### Pendiente

- Roles y permisos por empleado no tienen contrato. No existen query keys reservados para rutas inexistentes.
- No hay endpoint de edición ni creación de empleados; ninguna acción de escritura está expuesta.

---

## Query keys activas

```typescript
inventory: {
  items: ["inventory", "items"],
  stockAlerts: ["inventory", "stock-alerts"],
}
security: {
  employees: ["security", "employees"],
}
```

## Ruta de navegación

| Ruta | Estado | Acceso |
| --- | --- | --- |
| `/inventory` | Activo | Todos los usuarios autenticados |
| `/security` | Activo | Solo `ADMIN` |

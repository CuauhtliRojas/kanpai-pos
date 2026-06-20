# Identidad Visual Frontend V1 — Kanpai POS

## 1. Filosofía visual

Kanpai POS adopta una identidad visual **Neo-Brutalista** y **Maximizadora de Operación**. La interfaz debe sentirse como una herramienta física de trabajo: directa, resistente, táctil y sin ornamentación innecesaria.

El objetivo visual no es verse “corporativo” ni “elegante” en sentido administrativo, sino permitir que un operador en un Tachinomi pueda cobrar, abrir mesa, agregar productos, enviar comandas y resolver errores bajo presión, con poca luz, ruido, prisa y mínimo margen de error.

La estética debe reforzar tres principios: velocidad, claridad y confirmación física.

## 2. Reglas absolutas

Queda prohibido usar:

- Sidebar fijo.
- Degradados.
- Fondos decorativos.
- Animaciones largas.
- Botones pequeños en flujos operativos.
- Jerarquías visuales ambiguas.
- Menús anidados visibles de forma permanente.
- Componentes UI pesados que impongan estilos ajenos.
- Colores hardcodeados dispersos por pantallas.

La navegación administrativa debe vivir en un **menú hamburguesa oculto**, nunca en un sidebar permanente. El espacio horizontal pertenece al POS.

## 3. Layout base

La aplicación se compone de:

1. **Topbar ultradelgado**
2. **Área operativa principal**
3. **Menú hamburguesa administrativo bajo demanda**
4. **Modales o paneles temporales para acciones secundarias**

El topbar debe mostrar únicamente información crítica:

- Cajero activo.
- Mesa actual, si aplica.
- Estado de sincronización con Airtable.
- Estado básico de backend local, solo si hay error o advertencia.
- Botón hamburguesa.

El topbar no debe crecer para convertirse en navegación. Su altura debe mantenerse mínima para no robar espacio al POS.

## 4. Sistema visual Neo-Brutalista

Los elementos principales deben usar:

- Bordes gruesos.
- Sombras duras.
- Colores sólidos.
- Alto contraste.
- Tipografía clara y pesada.
- Estados visuales obvios.
- Feedback físico al presionar.

Los botones principales deben sentirse como bloques presionables. En estado normal tienen sombra dura desplazada. En estado activo o presionado, la sombra desaparece y el botón se desplaza visualmente, simulando presión física.

Ejemplo conceptual:

```text
Normal:    bloque sólido + borde grueso + sombra dura
Pressed:   bloque baja 2-4px + sombra desaparece
Disabled:  bloque opaco + sin sombra + cursor no operativo
```

## 5. Tokens visuales obligatorios

La identidad debe concentrarse en `frontend/src/styles/theme.css`.

Tokens mínimos:

```css
--kp-bg;
--kp-surface;
--kp-surface-raised;
--kp-text;
--kp-muted;
--kp-border;
--kp-border-strong;

--kp-accent;
--kp-accent-contrast;

--kp-success;
--kp-warning;
--kp-danger;
--kp-info;

--kp-shadow-hard;
--kp-shadow-hard-sm;

--kp-radius-none;
--kp-radius-sm;
--kp-radius-md;

--kp-touch-sm;
--kp-touch-md;
--kp-touch-lg;
--kp-topbar-height;
```

La aplicación no debe depender de radios grandes ni sombras suaves como identidad principal. El estilo base debe ser más cuadrado, sólido y táctil.

## 6. Color

El esquema debe ser de alto contraste y bajo ruido.

Paleta base recomendada:

```text
Fondo principal: negro cálido o carbón profundo.
Superficie: marfil o crema para bloques de alta legibilidad, cuando convenga.
Texto principal: casi blanco o negro absoluto según superficie.
Acento principal: rojo kanpai sólido.
Éxito: verde sólido.
Advertencia: amarillo/ámbar sólido.
Error: rojo intenso.
Información: azul eléctrico o cian sólido.
```

Los colores no deben indicar decoración; deben indicar acción, estado o jerarquía.

## 7. Botones

Tamaños mínimos:

```text
Botón operativo crítico: mínimo 72px de alto.
Botón operativo normal: mínimo 64px de alto.
Botón administrativo: mínimo 48px de alto.
Botón compacto de topbar: mínimo 40px de alto.
```

Reglas:

- Un botón primario debe verse inequívocamente primario.
- Un botón destructivo debe requerir confirmación si afecta ticket, pago, corte, comanda o inventario.
- Un botón deshabilitado debe explicar por qué no puede usarse cuando el bloqueo sea operativo.
- En POS, las acciones frecuentes deben estar a una mano y con área de toque grande.

## 8. Tipografía

La tipografía debe priorizar lectura rápida:

- Pesos fuertes para acciones.
- Mayúsculas moderadas solo para etiquetas cortas.
- Números grandes para importes.
- Evitar textos largos dentro de botones.
- Usar lenguaje operativo, no técnico.

Ejemplos:

```text
Correcto: COBRAR
Correcto: ENVIAR RONDA
Correcto: MESA 04
Correcto: FALTA COMANDA
Incorrecto: Ejecutar proceso de creación de pago
```

## 9. Semáforo de sincronización

La sincronización con Airtable debe representarse como semáforo compacto:

```text
Verde: sincronización habilitada, sin error reciente.
Amarillo: sync deshabilitado, pausado, no iniciado o con advertencia.
Rojo: error, credenciales faltantes, conflicto o backend inaccesible.
Azul: sincronización corriendo.
```

El semáforo no debe mostrar detalles largos en el topbar. Los detalles viven en pantalla de sistema/admin.

## 10. Estados operativos

La UI debe modelar estados visibles:

- Backend apagado.
- Sync corriendo.
- Sync con error.
- Corte cerrado.
- Corte abierto.
- Mesa libre.
- Mesa ocupada.
- Ticket abierto.
- Ticket en cobro.
- Ticket cobrado.
- Líneas capturadas sin enviar.
- Ronda enviada.
- Pago parcial.
- Pago completo.
- Impresión pendiente.
- Impresión fallida.

Cada estado debe tener color, texto corto y consecuencia operativa clara.

## 11. Navegación

La navegación visible permanente debe ser mínima.

Estructura:

```text
Topbar:
  [☰] [Cajero activo] [Mesa actual] [Sync semáforo]

Menú hamburguesa:
  Sistema
  Caja
  POS
  Producción
  Impresión
  Inventario
  Reportes
  Auditoría
  Configuración
  Cerrar sesión
```

El menú hamburguesa debe ser overlay o drawer temporal. No debe desplazar permanentemente el layout operativo.

## 12. Pantalla POS

La pantalla POS debe priorizar:

1. Mesa/ticket activo.
2. Productos y categorías.
3. Ticket/líneas.
4. Acciones críticas: enviar ronda, iniciar cobro, cobrar.
5. Estados de comanda e impresión.

No debe parecer dashboard administrativo.

## 13. Pantallas administrativas

Las pantallas administrativas pueden ser más densas, pero deben conservar:

- Bloques sólidos.
- Alto contraste.
- Botones claros.
- Tablas legibles.
- Filtros grandes.
- Estados vacíos explícitos.

No deben competir visualmente con POS ni contaminar el flujo operativo.

## 14. Criterio de aceptación visual

Una pantalla cumple la identidad si:

- Puede operarse con dedo sin precisión fina.
- El operador entiende la acción principal en menos de 2 segundos.
- No hay navegación lateral fija.
- No hay degradados.
- Las acciones parecen botones físicos.
- Los estados críticos se distinguen a distancia.
- Cambiar el color principal requiere tocar principalmente `theme.css`.

## 15. Personalización de marca y assets

La aplicación debe permitir personalización simple de marca sin tocar lógica de React.

Regla: los assets de identidad visual deben vivir en una carpeta estable, por ejemplo:

```text
frontend/src/assets/brand/
  app-logo.svg
  app-icon.svg
  product-placeholder.webp
```

Si se reemplaza `app-logo.svg` por otro archivo con el mismo nombre, la aplicación debe tomar automáticamente el nuevo logo sin cambiar imports, componentes ni rutas.

La misma regla aplica para imágenes de referencia futuras de productos. Los productos deben contemplar imagen visual, pero la UI no debe competir con dichas imágenes. Por eso la paleta base debe mantenerse sobria: fondo Sumi oscuro, superficies zinc, texto blanco hueso, rojo solo para acción crítica/error y amarillo solo para selección o énfasis operativo.

La interfaz visible debe usar lenguaje de operador, no lenguaje técnico. Quedan prohibidos en flujos normales términos como API, endpoint, backend, FastAPI, SQLite, scheduler, request, response o token. Esos términos solo pueden aparecer en diagnóstico administrativo avanzado.

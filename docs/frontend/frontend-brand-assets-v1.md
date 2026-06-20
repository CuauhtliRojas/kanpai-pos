# Assets de marca del frontend

## Ubicación

Los assets reemplazables de marca viven en:

```text
frontend/src/assets/brand/
  app-logo.svg
  app-icon.svg
  product-placeholder.svg
```

La aplicación los importa únicamente desde `frontend/src/shared/assets/brandAssets.ts`. Los componentes no deben crear rutas propias hacia estos archivos.

## Personalización sin cambios de código

Para cambiar el logo horizontal, reemplaza `app-logo.svg` por el nuevo SVG y conserva exactamente el mismo nombre y extensión.

Para cambiar el icono compacto, reemplaza `app-icon.svg` con el mismo criterio.

Para cambiar la imagen predeterminada de productos sin foto, reemplaza `product-placeholder.svg` sin renombrarlo.

Después de reemplazar un archivo, reinicia el entorno de desarrollo o vuelve a construir la aplicación para comprobar el resultado. No es necesario modificar imports, rutas ni componentes React.

## Reglas de los archivos

- Los nombres y extensiones son contratos estables y no deben cambiarse.
- Usa SVG para logos e iconos de marca.
- No incluyas scripts, fuentes, imágenes remotas ni recursos externos dentro de los SVG.
- Evita imágenes pesadas y datos base64 grandes.
- Optimiza dimensiones y peso antes de incorporar cualquier imagen.
- Para fotografías futuras de productos, usa WebP o JPG optimizado.
- Conserva una composición sobria: la interfaz no debe competir visualmente con las fotos de productos.

`BrandMark` es el componente compartido para renderizar el logo o el icono. Las pantallas futuras deben reutilizarlo en vez de importar SVG directamente.

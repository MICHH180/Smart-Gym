Medios de los ejercicios (fotos y videos)
=========================================

Por cada carpeta (una por ejercicio), agrega estos archivos exactos:

  thumbnail.jpg   -> foto que aparece en la lista de la landing (recomendado 320x220 o similar, horizontal)
  1.mp4           -> video de demostración en /ejercicios/{id} (recomendado 16:9, unos segundos)
  1.webm          -> alternativa al MP4 (mismo nombre base: 1)

También puedes usar una foto en lugar de video:

  1.jpg   (o .png / .webp)

El nombre debe ser exactamente "1" (no "demo", "squat_demo", etc.).
Si existe 1.mp4 se muestra el video con controles; si no hay MP4, se intenta
1.webm y luego 1.jpg (y demás extensiones de imagen).

IMPORTANTE (Windows): activa "Extensiones de nombre de archivo" en el
Explorador (Vista > Mostrar > Extensiones de nombre de archivo). Si no,
al renombrar un archivo a "1.mp4" el nombre real puede quedar como
"1.mp4.mp4" y no se verá en la app.

Carpetas disponibles:
  sentadillas/
  desplantes/
  curl-biceps/
  elevaciones-laterales/
  flexiones/
  puente-gluteos/
  plancha/

No hace falta tocar ningún archivo .tsx: mientras el nombre y la carpeta
coincidan, el medio aparece solo. Si no existe todavía, se muestra un
placeholder grande en su lugar.

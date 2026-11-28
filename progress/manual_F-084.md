<!-- progress/manual_F-084.md -->
# F-084 · Verificaciones manuales (T11)

Las ejecuta el líder el 2026-11-28, tras el despliegue del humano de ese día (sv3
`r20261128121243`, sv5 `r20261128121503`, sv4 `r20261128121721`). Solo lecturas.

## M1 · base `partes`, solo lectura: EN VERDE

`SELECT column_name FROM information_schema.columns WHERE table_name = 'parte_documents' AND
column_name LIKE 'sustituido%' ORDER BY 1` ⇒ **2 filas**: `sustituido_at_utc` y
`sustituido_por_id`. El DDL de arranque de sv3 las ha creado.

## M2 · portal, solo lectura: EN VERDE

- `/problemas` responde 200. El parte `5c1a9b04` sale en el grupo «Sustituido por otra página del
  mismo correo (10)», con el enlace «ver» a `/partes/89f17181-…` (su sustituto) y los botones
  «Ver PDF», «Recuperar» y «Descartar».
- `GET /api/problemas/resumen` ⇒ `total: 41`. La insignia del enlace «Problemas» de la navegación
  dice **41** («41 parte(s) con problemas»). Coinciden.
- Grupos en pantalla: sin obra casada 1, sin fecha 5, fecha posterior al correo 1, sin líneas 1,
  sustituido por otra página del mismo correo 10, desactivado sin sustituto 23 (suman 41) y
  «Sustituido por un reenvío (61) · no cuentan en el aviso». `por_motivo` da `sin_lineas: 2`
  porque cuenta motivos; un parte con dos motivos se agrupa por el primero (decisión del informe).

## M3 · portal, ESCRIBE en producción: PENDIENTE

Recuperar o descartar `5c1a9b04`. Solo con el OK expreso del humano para esa acción.

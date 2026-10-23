<!-- progress/spec_F-058.md -->
# F-058 · spec_ready, enmendada (2026-10-23): relectura de la cabecera con Gemini y prompt de cabecera en sv2

Spec en `specs/F-058-relectura-cabecera-gemini/` (rama `feature/F-058-relectura-cabecera-gemini`,
worktree `partes-wt-f058`). Primera versión en f8f3062; esta enmienda aplica las respuestas del
humano del 2026-10-23. Rigor **estándar**. Tamaños: requirements 149/150, design 249/250,
tasks 21 tareas (puerta de tamaño en verde).

## Respuestas del humano que aplica (literales)

1. DA1: «da1, vacia o no casa con ninguna obra».
2. «para el tema de la cabecera podemos mejorar el prompt diciendole que hay una cabecera y que
   debera obtener la obra el dia mes, etc... añadelo a f58, lo demas ok» ⇒ DA2–DA8 aprobadas con
   la recomendación (A en todas, DA5 incluida) y la comprobación de existencia en sv2 (opción A).

## Qué cambia respecto a f8f3062

- **DA1 enmendada**: con al menos una fila, se relee si (a) `obra_numero` y `fecha` vacíos
  (`cabecera_vacia`) **o** (b) la obra leída no está en la lista de obras de Sigrid
  (`obra_inexistente`). Fecha sin obra no relee (F-054 la manda a revisión).
- **Comprobación de existencia en sv2**: lista de códigos `SELECT DISTINCT con.cod FROM obr JOIN
  con` por `sql/read` con el `SigridLookupClient` que ya usa el catálogo auxhor, cacheada
  `OBRAS_CACHE_TTL_S` (600). Clave: sin acentos, mayúsculas, sin blancos ni guiones y sin ceros a
  la izquierda; cualquier empresa, con o sin baja. `truncated: true` o 0 códigos = fallo; si
  sigrid-api falla o no está cableado, no se relee por obra, no se propaga y no se reintenta
  hasta pasado el TTL. No es la conciliación de sv3 (la clave es más gruesa: todo lo que sv3
  casaría por código está en la lista) y la lista cerrada de duplicados no crece.
- **Relectura útil por motivo** y resultado nuevo `no_casa` (la releída trae otra obra que
  tampoco está en la lista). Traza `meta.relectura_cabecera.motivo` ∈ `cabecera_vacia` |
  `obra_inexistente`.
- **Prompt**: párrafo nuevo al inicio del punto 1 de `parte_trabajo_es` (toda página tiene
  cabecera; de ella salen obra, día, mes, año, membrete y el resto; búscala aunque el escaneo
  salga desplazado; con trabajadores, cabecera entera a null = no localizada; nunca inventar) y
  una frase en la viñeta de fecha (casillas separadas día/mes/año). Texto exacto en
  `design.md` §5. Afecta a todas las extracciones de ambos proveedores.
- **Banco MB** (T3, lo lanza el líder con `lanzar.ps1` y `-Repo` al worktree, sobre el commit de
  T2): (a) sincab con `gpt-6.1-sol` ×2 ⇒ cuántas de 12 traen obra y fecha (antes 0; se mide, no
  es puerta); (b) control con `gpt-6.1-sol`; (c) sincab con `gemini-4-argon`; (d) batería de
  F-051 ×3 con `corregir.py`. Puerta: (b)–(d) sin regresión. Resultado en
  `progress/banco_F-058.md`. Que el prompt mejore no quita la relectura.
- `azure-apps/partes.md`: sv2 consume Gemini para releer y sigrid-api (catálogo auxhor, que ya
  consumía sin estar documentado, y lista de obras). M0 comprueba también las `SIGRID_API_*`.
  Sin cambios de entorno en Azure.

## Decisiones abiertas para el humano (`design.md` §11)

| DA | Tema | Recomendación |
|---|---|---|
| DA9 | Puerta del prompt | Si MB (b)–(d) empeora, se quita el párrafo y queda la relectura |
| DA10 | Comprobación de existencia | A: lista cacheada (1 consulta por TTL; truncated o vacía = fallo; fallo = no releer por obra). B: consulta por página. C: fallo = releer |
| DA11 | Cabecera con obra inexistente | A: la releída entera si su obra está en la lista (como DA3). B: conservar la fecha primaria si la releída no la trae |

## Hallazgos del spec-author que conviene saber

- `SigridLookupClient` de sv2 no mira `truncated` hoy (pide `max_rows` 10.000 para auxhor);
  la spec lo exige solo para la lista de obras (`exigir_completo`), sin cambiar auxhor.
- `azure-apps/partes.md` no documentaba que sv2 ya lee sigrid-api (catálogo auxhor); T15 lo
  corrige. `azure-apps/sigrid_api.md` (de sigrid-api) no lista a partes entre sus consumidores:
  no se toca aquí por la regla de propiedad; lo decide el humano.
- `docs/ARCHITECTURE.md` dice «máx. 1.000 filas por petición» de sigrid-api; la instancia sirve
  500.000 (CLAUDE.md raíz). T13 lo corrige de paso.
- sv3 también casa por nombre cuando el código no existe: una relectura por `obra_inexistente`
  solo sustituye la cabecera si la obra releída está en la lista; si no, `no_casa` y sv3 sigue
  como hoy.

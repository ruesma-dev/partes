<!-- progress/spec_F-058.md -->
# F-058 · spec_ready, enmendada otra vez (2026-10-23): relectura de la cabecera con Gemini y prompt de cabecera en sv2

Spec en `specs/F-058-relectura-cabecera-gemini/` (rama `feature/F-058-relectura-cabecera-gemini`,
worktree `partes-wt-f058`). Primera versión en f8f3062, primera enmienda en a631600 (DA1,
comprobación de obra en sv2 y prompt); esta segunda enmienda aplica la respuesta del humano a
la DA10. Rigor **estándar**. Tamaños: requirements 150/150, design 250/250, tasks 22 tareas.

## Respuesta del humano que aplica (literal, 2026-10-23)

«da10, vamos a poner una consulta en el momento al vuelo, y vemos tiempos. si la obra no existe
se manda a relectura a gemini»

## Qué cambia respecto a a631600

- **DA10 = B (decidida)**: fuera la lista de códigos cacheada, `OBRAS_CACHE_TTL_S`, `ObrasSigrid`,
  `CodigosObraPort`, `fetch_codigos_obra` y el riesgo de «obra nueva dentro del TTL». En su
  lugar, por cada página con trabajadores, obra leída y relectura activa, sv2 hace en ese
  momento una consulta `sql/read` de existencia de esa obra (`SigridLookupClient.existe_obra`,
  `_SQL_EXISTE_OBRA` con un solo `?`: la clave va en `parameters`, nunca en el texto). El SQL
  calcula sobre `con.cod` la misma clave que Python (sin espacios ni guiones, sin ceros a la
  izquierda si son solo dígitos, mayúsculas y acentos por `COLLATE Latin1_General_CI_AI`), en
  cualquier empresa y también de baja; `TOP 1`, `max_rows` 2 y `truncated` = fallo.
- **Como mucho dos consultas por página**: la de la primaria y, si la releída por
  `obra_inexistente` trae otra clave, la de la releída (misma clave ⇒ `no_casa` sin consultar).
  Con `cabecera_vacia` no se consulta nada.
- **«Vemos tiempos»**: `ComprobadorObra` (application, sin estado) mide cada consulta con reloj
  monotónico y deja INFO `[obra-sigrid] document_id=… resultado=existe|no_existe ms=…` (WARNING
  con `error=<tipo>` si falla), sin código, nombres ni DNIs. Al releer, además,
  `meta.relectura_cabecera.consulta_obra_ms` (lista); sin relectura, meta y debug como hoy
  (DA6). Para tener `document_id` en el log, `ExtractParteRequest` gana `document_id` opcional y
  `main_worker.py` lo pasa (R15). Nueva verificación **M4** (T20): KQL en Log Analytics sobre
  `ca-sv2-extraccion` con número, mediana, p95, máximo y errores por día (`design.md` §10).
- **«Si la obra no existe se manda a relectura a gemini»**: confirma la DA1 enmendada
  (`obra_inexistente` ⇒ relectura); anotado en §11.
- **Fallo o lentitud (DA12, nueva, pendiente)**: propuesta `OBRA_EXISTE_TIMEOUT_S` = 5 s
  (`httpx` y `timeout_seconds` de sigrid-api); fallo, `truncated` o tope = «no se sabe»: no relee
  por obra, WARNING, la extracción sigue; en la segunda consulta, «no se sabe» da `no_casa`.

## Decisiones pendientes de confirmar por el humano (`design.md` §11)

| DA | Tema | Recomendación |
|---|---|---|
| DA9 | Puerta del prompt | Si MB (b)–(d) empeora, se quita el párrafo y queda la relectura |
| DA11 | Cabecera con obra inexistente | A: la releída entera si su obra existe (como DA3). B: conservar la fecha primaria si la releída no la trae |
| DA12 | Consulta de obra que falla o tarda | A: tope 5 s; fallo, `truncated` o tope = no releer por obra, WARNING y seguir. B: fallo = releer (Gemini en todas las páginas con obra mientras sigrid-api falle). Se revisa con los tiempos de M4 |

## Hallazgos del spec-author que conviene saber

- **Sin medir**: la clave calculada sobre `con.cod` impide usar un índice, así que cada consulta
  recorre `obr ⨝ con`. El agente no tiene acceso a sigrid-api; los primeros tiempos salen de M1
  (local) y los reales de M4. Casi todas las páginas traen obra y filas: casi todas consultan.
- **El tope de 5 s no es total**: `httpx` lo aplica por fase y `HTTPTransport(retries=1)`
  reintenta la conexión; el peor caso ronda 2–3 veces el tope. Un arranque en frío de
  sigrid-api puede pasarlo: esa página no relee por obra y F-054 es la red.
- Si sigrid-api rechazara la sentencia (`CROSS APPLY`, `COLLATE`), M1 lo verá como `error`
  sin romper la extracción; el implementer no puede comprobarlo sin red.
- Siguen valiendo: `SigridLookupClient` de sv2 no mira `truncated` hoy (solo se exige para la
  consulta nueva); `azure-apps/partes.md` no documentaba que sv2 ya lee sigrid-api (T15);
  `azure-apps/sigrid_api.md` no lista a partes entre sus consumidores (no se toca por la regla
  de propiedad; lo decide el humano); `docs/ARCHITECTURE.md` dice 1.000 filas y son 500.000
  (T13).

## Aprobación del humano (2026-10-23)

Literal: «a a todo» ⇒ DA9, DA11 y DA12 = A. Con DA1–DA8 (aprobadas antes) y DA10 = B, todas las
decisiones están cerradas: F-058 queda aprobada, a la espera de su turno (prioridad 3, detrás de
F-059 y F-056).

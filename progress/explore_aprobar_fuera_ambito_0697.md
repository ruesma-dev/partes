# Exploración · «N línea(s) no son de esta vista» al aprobar la obra 0697 (obr-2491656)

Fecha: 2026-11-12. Investigación de SOLO LECTURA: código de sv4/sv3, logs de
Log Analytics (sv4 y sv3) y base `partes` con `default_transaction_read_only=on`.
No se ha escrito código del repositorio ni se ha tocado nada en Azure.
Revisiones en producción: sv4 `r20261031093735` y sv3 `r20261031093921`
(imagen del 31-oct, código equivalente a `6597baf`; las partes implicadas son
iguales en `dev`).

## Causa en una frase

El front y el validador **no discrepan**: calculan la misma lista. Lo que pasa
es que **sv3 borra y vuelve a crear las extras automáticas con ids nuevos en
cada pasada de conciliación**, y esa mañana hubo una pasada cada 5-40 s (una
tanda de partes nuevos entrando por 4 réplicas de sv3). Los ids de las 4
extras automáticas pendientes de la vista dejan de existir entre que se pinta
la página y se pulsa «Aprobar» (o entre el preflight y el encolar), así que
`_validar_ambito` las cuenta como «fuera del ámbito».

## El mecanismo, con fichero:línea

1. Cada mensaje de `q-persistencia` (parte nuevo o recálculo) lanza una pasada
   **global** de toda la base:
   - parte nuevo: `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:283`
   - recálculo: `services/partes-persistencia/interface_adapters/workers/despacho.py:86`
   - la pasada: `services/partes-persistencia/application/services/recurso_conciliador.py:459` (`_pasada`).
2. Al empezar, `revert_extras_auto()` (`recurso_conciliador.py:465`) **borra
   físicamente** todas las extras `extra_auto` no congeladas y devuelve las
   ordinarias a su `horas_orig`, y hace **commit**:
   `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:410-416`
   (`session.delete(...)`, `session.commit()`).
3. Después lee Sigrid y reparte, y al final `apply_extras_splits(splits)`
   (`recurso_conciliador.py:552`) **inserta extras nuevas** en otra
   transacción (`sqlalchemy_parte_repository.py:475-496`). `_extra_de`
   (`:421-473`) solo conserva el id si el split trae `id` (que solo pone F-046
   para sus reservas); en la pasada normal no lo trae ⇒ id nuevo de la
   secuencia.
4. sv4 valida contra lo que haya en ese instante:
   `services/partes-front/interface_adapters/web/app.py:2502` (`_validar_ambito`)
   → `infrastructure/database/parte_repository.py:2602` (`registro_ids_de_obra`)
   → `get_obra` (`:1407`), que solo ve filas vivas. El id viejo ya no existe
   ⇒ `fuera = 4` (`app.py:2529`).

## Respuesta a la pregunta 1 (modo natural)

**El modo natural no tiene nada que ver.** Se descartan las tres hipótesis:

- Botón con `period`/`mode` equivocado: **descartado.** El botón lleva
  `data-period="{{ detail.period_key }}"` y `data-mode="{{ detail.mode }}"`
  (`templates/obra_detail.html:22-23`) y `ambitoDe` los manda tal cual
  (`static/app.js:4699-4703`); el validador llama a `get_obra` con ellos.
  Ejecutando el código real de `get_obra` contra producción (solo lectura),
  `period=None` y `period="2026-11"` dan exactamente la misma lista en los dos
  modos.
- Filas que no salen de `detail.registros`: **descartado.** La tabla es
  `{% for r in detail.registros %}` (`obra_detail.html:213-214`) y
  `conjuntoAprobacion` solo coge `#lines-table tbody tr[data-registro-id]`
  (`app.js:4630-4659`); ningún JS añade filas a esa tabla.
- Filas con fecha fuera del periodo: **descartado.** `fecha` y `fecha_int`
  son coherentes en todas las líneas de la obra; render y validación usan el
  mismo `in_period`.

Lo que sí hay que corregir del enunciado: **el usuario nunca estuvo en
octubre.** Ninguna de sus peticiones lleva `period`
(`GET /obras/obr-2491656`, `?modo=natural`, `?modo=nomina`), así que la vista
cogía el periodo más reciente: **noviembre** (natural: 3-10 nov, 19 líneas;
nómina: 19 oct-10 nov, 47 líneas). Octubre de esta obra ya está todo en
Sigrid (28 `registrado` + 8 extras `registrado` + 28 `omitido`). Lo pendiente
son 19 líneas de noviembre: 15 ordinarias y **4 extras automáticas**.

Las dos vistas de noviembre (natural y nómina) contienen esas 4 extras, y son
las **únicas** líneas de la vista que sv3 rehace (las de octubre están
congeladas). Por eso siempre salían exactamente 4, en los dos modos.

## Respuesta a la pregunta 2 (preflight 200 y encolar 422 a los 3 s)

**El servidor no amplía los ids.** `confirmar()` (`app.js:4216-4262`) manda en
`encolar` `idsDe(plan.cola)`, que son los `registro_ids` de los grupos del
preflight; esos salen de `GrupoObra.registro_ids`
(`application/services/reparto_obras.py:44-45`), que son solo las líneas
pedidas que viajan (`lineas_para_registro`, `parte_repository.py:2252-2346`).
Las rachas CIZ (`racha_registro_ids`) van dentro del payload de cada línea, no
en `registro_ids`; repartos y franquicias solo añaden decisiones, no ids. Es
decir, el encolar manda un **subconjunto** de lo que el preflight acababa de
validar, con el mismo `ambito`.

Lo que cambió en esos 3 s es la base: una pasada de sv3 (réplica `jmr6d`)
hizo el revert a las 09:24:11,2 y creó extras nuevas a las 09:24:12,6. El
preflight validó justo antes del commit del revert (su llamada a sv5 vuelve a
las 09:24:12,58) y el encolar de las 09:24:16,7 validó con las extras ya
recreadas con otros ids.

## Evidencia

**Cronología** (hora local; las pasadas son las líneas `[repo] revert de
extras` → `[recurso-concil] … extras_reclasificadas=` de sv3):

| Hora | sv4 (usuario) | sv3: pasadas desde la acción anterior |
|---|---|---|
| 09:18:11 | carga `/obras/obr-2491656` (nómina nov) | — |
| 09:20:29 | preflight → 422, 4 fuera | 6 pasadas (09:18:54 … 09:20:25) |
| 09:20:53 | recarga `?modo=natural` (natural nov) | — |
| 09:21:11 | preflight → 422 | pasada 09:21:04-05 |
| 09:21:28 | preflight → 422 | pasadas 09:21:11, 09:21:22, 09:21:26 |
| 09:22:09 | preflight → 422 | más pasadas |
| 09:22:20 | recarga `?modo=natural` | revert 09:22:19,1 / alta 09:22:20,5 (`jmr6d`) |
| 09:22:21,5 | preflight → 422 | revert 09:22:20,7 / alta 09:22:22,4 (`stjnf`): la petición cae **dentro** de la ventana sin extras |
| 09:23:56 | recarga `?modo=nomina` | alta anterior 09:23:44,6 (`dqlxr`) |
| ~09:24:11 | preflight → 200 | revert 09:24:11,2 (`jmr6d`), justo después |
| 09:24:16,7 | encolar → 422, 4 fuera | alta 09:24:12,6 con ids nuevos |
| 09:25:33 | — | última pasada de la tanda |
| 09:27 | aprueba con éxito la otra 0697 (`obr-2598022`) | sin pasadas |

Entre 09:16 y 09:25 hubo unas 27 pasadas en 4 réplicas de sv3, cada una con
~50 extras recreadas.

**Rastro en la base** (solo lectura, 2026-11-12 ~10:10 local):

- De los ids 23512-24301 (790 valores de la secuencia) solo existen 68 filas:
  unos 720 ids se gastaron en extras que se crearon y se borraron en pasadas
  posteriores.
- Las extras automáticas vivas no congeladas son 61 en toda la base, todas
  recreadas en la última pasada.
- Nada de la obra se movió de obra, de periodo ni a la papelera: los 25
  documentos están activos, ninguna línea tiene `deleted_at_utc` y ningún
  documento de la obra tuvo recálculo propio hoy (el último fue el
  11-nov 17:00 UTC). Las pasadas las dispararon partes de **otras** obras
  (0721, 0692…), porque la pasada es global.
- Las reasignaciones que otro usuario hizo en paralelo eran de la obra 0721:
  no tocan esta obra, salvo porque piden recálculo, que es otra pasada global.

## Las 4 líneas

Son las 4 extras automáticas (`extra_auto=true`, `tipo_hora=extra`, 1,0 h,
`HEGR`, sin `sigrid_estado`) del mismo trabajador (recurso 2121960), una por
día. Cada una es la pareja de una ordinaria HLGR de 8,0 h (`horas_orig` 9,0).
Los ids que tenían a las 09:20-09:24 ya no existen (borrados físicamente);
estos son los ids actuales, de la última pasada (~09:25):

| Fecha | Id actual de la extra | Ordinaria pareja | Documento |
|---|---|---|---|
| 2026-11-03 | 24259 | 22871 | d2b99bfa… |
| 2026-11-04 | 24268 | 22913 | 184df7f3… |
| 2026-11-05 | 24257 | 22828 | eded19f8… |
| 2026-11-10 | 24254 | 22747 | 4cab15ba… |

(Se identifica al trabajador solo por el id de recurso; no figura ningún
nombre ni DNI.)

## Riesgo que destapa (no observado, pero posible hoy)

Mientras dura la ventana entre el revert y el alta de cada pasada (de 1 a
40 s), la ordinaria de la pareja vale **9,0 h sin extra**. Una aprobación que
lea en ese momento sin pasar por el ámbito (aprobar una sola línea, R9, o una
página pintada dentro de la ventana) mandaría a Sigrid 9 h ordinarias en vez
de 8 + 1 extra. Además la línea quedaría congelada (`encolado`) y F-037 ya no
volvería a partirla. El 422 de ámbito, en realidad, protege de una parte de
esto.

## Propuesta de arreglo

La raíz está en **sv3**, que es el dueño del cómputo de extras. sv4 solo lee,
y no hay lógica que duplicar. Una feature nueva de sv3, en dos piezas:

1. **Ids estables para las extras automáticas.** Al revertir, guardar
   `clave de pareja → id` de cada extra borrada (la clave ya existe:
   `clave_pareja` con `document_id`, `line_index`, `empleado_line_no` y
   `fecha_int`). Al hacer el split, si la pareja vuelve a necesitar extra, se
   le pone ese mismo `id` (`_extra_de` ya acepta `s["id"]` desde F-046).
   Mejor todavía: actualizar en el sitio la extra existente en vez de borrarla
   y crearla de nuevo. Arregla el 422 después de cada pasada, y de paso las
   referencias por id que guarda sv4 (repartos, franquicias, `undo_log`,
   selección en pantalla).
   Ficheros: `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py`
   (`revert_extras_auto` :361, `apply_extras_splits` :475) y
   `services/partes-persistencia/application/services/recurso_conciliador.py`
   (`_pasada` :459-552), con el plan de `pareja_extra` (F-037) si hace falta.
2. **Cerrar la ventana**: hacer el revert y el alta de las extras en **una
   sola transacción**. Por ejemplo, calcular el revert en memoria sobre lo
   leído por `fetch_registros_para_recurso` y escribir revert, casados y
   splits juntos al final de `_pasada`. Así sv4 nunca ve «9 h sin extra» ni
   ids que todavía no existen. Ficheros: los mismos.

Tests nuevos en `services/partes-persistencia/tests/`: dos pasadas seguidas
sin cambios dejan los mismos ids de extra, y un lector concurrente nunca ve
la pareja sin su extra.

Mitigación opcional en sv4 (no sustituye a lo anterior):
`interface_adapters/web/app.py:2529-2536` puede distinguir los ids que **ya no
existen** de los que son de otra vista, y en ese caso decir «se están
recalculando las extras; recarga en unos segundos» en vez de «otra obra, otro
periodo…», que despista. Fuera de alcance aquí: que cada parte nuevo dispare
una pasada **global** de toda la base. Es la razón de que la tanda de las
09:16-09:25 tocara obras ajenas, y conviene valorarlo aparte.

## ¿Puede aprobar hoy?

**Sí, ahora mismo debería pasar.** La tanda de sv3 terminó a las 09:25:33 y
desde entonces no ha habido más pasadas: a las 10:13 local la secuencia
seguía en 24301 y las 4 extras conservaban sus ids. Pasos:

1. **Recargar** la vista (`/obras/obr-2491656`, nómina o natural de noviembre:
   da igual) justo antes de aprobar y pulsar «Aprobar» enseguida.
2. Si vuelve a salir el 422, es que ha entrado otra tanda de partes: esperar a
   que termine (un par de minutos sin partes nuevos) y repetir el paso 1.
3. Mientras haya una tanda en curso, **no** aprobar línea a línea (con el
   botón de la fila no se valida el ámbito, y en la ventana se mandarían 9 h
   ordinarias sin la extra).

No hace falta tocar nada en la base ni en Sigrid. Octubre de esta obra ya
está registrado: lo que falta por aprobar es noviembre.

## Observación al margen

Hay extras automáticas con `fecha`/`fecha_int` NULL (ids 24260, 24261, 24263,
24273, 24282, 24299), de partes sin fecha (por ejemplo, uno guardado con
`fecha=None` a las 09:18:30). No afectan a esta obra: no salen en ninguna
vista por periodo y no se pueden aprobar desde la de obra.

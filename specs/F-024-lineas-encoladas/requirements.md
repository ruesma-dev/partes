<!-- specs/F-024-lineas-encoladas/requirements.md -->
# F-024 · Líneas borradas en Sigrid y estado «encolado» — Requisitos (EARS)

Origen: `progress/explore_F-024.md`. sv5 escribió 35 líneas el 30/09 en
PT26/00314 con `synckey`; Administración las **borró a propósito** en Sigrid
y el portal las sigue dando por `registrado` y congeladas. El «encolado» de la
captura es una vista recargada antes de que llegue el resultado. Decisión del
humano (2026-10-01): lo que Administración borra en Sigrid se refleja en el
portal. Servicios: **sv5** (comprobación de solo lectura) y **sv4** (estado,
vistas, sondeo). sv3 no se toca. Diseño y decisiones: `design.md`.

Vocabulario: «línea» = fila de `parte_registros`; «comprobar» = preguntar a
Sigrid si la línea escrita por sv5 sigue allí; `synckey` = `partes:<id>`.
Tests: `test_f024_rN_*`, sin red ni BBDD (dobles, `httpx` simulado, SQLite).

## A1 · Comprobación en sv5 (solo lectura)

- **R1** (evento). CUANDO sv5 recibe `POST /api/registro/comprobar` con
  1–500 líneas (`registro_id`, `hmores_ide`, `hmoide`, `recurso_ide`,
  `fecha_int`, `horas`, `es_incidencia`), debe devolver `ok: true` y
  **exactamente un veredicto por `registro_id` distinto**, sin emitir
  ninguna escritura a sigrid-api y sin adquirir el lock de escritura.
- **R2** (ubicuo). Una línea debe ser `presente` si su `synckey` aparece en
  `hmores`, con la **misma lectura que la idempotencia del pipeline**
  (`lineas_por_synckey`, paso 6): `borrada` ⇔ reaprobarla la escribiría.
- **R3** (evento). CUANDO la `synckey` no aparece pero existe la fila
  `hmores.ide = hmores_ide` con `synckey` vacía y el mismo recurso, fecha y
  (si se envió) `hmoide`, el veredicto debe ser `presente` con
  `sin_synckey: true`. Con cualquier otro valor en esa fila (otra `synckey`,
  otro recurso u otra fecha: `ide` reutilizado) debe ser `borrada`.
- **R4** (ubicuo). En el resto de casos el veredicto debe ser `borrada`, con
  `parte_existe: false` y un motivo propio cuando el `hmoide` enviado ya no
  existe en `hmo` (cabecera borrada entera).
- **R5** (ubicuo). Todo veredicto `presente` debe llevar el `hmores_ide`, el
  `hmoide` y el `parte_cod` (`con.cod`) **actuales** de Sigrid.
- **R6** (evento). CUANDO una línea `presente` difiere en recurso, fecha o
  —si no es incidencia— horas (tolerancia 0,005), el veredicto debe listar
  esas `diferencias` en texto, sin dejar de ser `presente`.
- **R7** (ubicuo). Las lecturas deben ir en lotes de ≤ 200 claves o `ide`
  por consulta, con `max_rows` 1000.
- **R8** (no deseado). SI una lectura falla o devuelve `truncated: true`,
  ENTONCES sv5 debe responder 502 `{ok: false, error}` sin ningún veredicto.
- **R9** (no deseado). SI la petición trae 0 o más de 500 líneas o un cuerpo
  inválido, ENTONCES sv5 debe responder 422 sin leer Sigrid.

## A2 · Estado en el portal (sv4)

- **R10** (evento). CUANDO llega un veredicto `borrada` para una línea que
  sigue en `registrado` con el mismo `sigrid_hmores_ide` que se envió, sv4
  debe pasarla a `sigrid_estado='borrado_sigrid'` (≤ 16 caracteres, cabe en
  la columna) con un `sigrid_motivo` que diga parte, línea y fecha UTC de la
  comprobación, y **conservar** `sigrid_parte_cod`, `sigrid_hmoide`,
  `sigrid_hmores_ide`, `sigrid_registrado_at_utc` y `sigrid_registrado_by`.
- **R11** (no deseado). SI al aplicar el veredicto la línea ya no está en
  `registrado` o su `sigrid_hmores_ide` cambió, ENTONCES sv4 no debe tocarla
  (comprobación y cambio en la misma transacción).
- **R12** (evento). CUANDO llega `presente` con `hmores_ide`, `hmoide` o
  `parte_cod` distintos de los guardados, sv4 debe actualizar esas
  referencias y dejar la línea en `registrado`.
- **R13** (ubicuo). `borrado_sigrid` no debe congelar la línea ni el
  documento ni bloquear su borrado definitivo (F-004 R1, R2, R12), y la
  regla de sv3 (`esta_congelado`) debe decir lo mismo que la de sv4.
- **R14** (no deseado). SI sv5 no responde, responde `ok: false` o falta un
  veredicto, ENTONCES no debe cambiar ninguna línea de ese lote.
- **R15** (evento). CUANDO un resultado de sv5 trae en `ya_registradas` una
  línea en `borrado_sigrid`, sv4 debe dejarla en `registrado`.
- **R16** (ubicuo). El motivo del candado de una línea `registrado` debe
  explicar la vía nueva: borrarla en Sigrid, comprobar y reaprobar.

## A3 · Cuándo se comprueba

- **R17** (evento). CUANDO se llama a `POST /api/sigrid/comprobar` con
  `registro_ids`, sv4 debe comprobar solo las que están en `registrado`, en
  lotes de `COMPROBACION_SIGRID_LOTE` (500), y responder `{ok, comprobadas,
  borradas, actualizadas, sin_synckey, con_diferencias: [{registro_id,
  diferencias}]}`. Sin sv5 configurado, 503; sin ids, 422.
- **R18** (opcional). DONDE `COMPROBACION_SIGRID_INTERVALO_S` > 0 y sv5 esté
  configurado, sv4 debe arrancar un hilo daemon que, 60 s después de
  arrancar y luego cada intervalo (3600 por defecto), compruebe toda línea
  `registrado` —activa o en papelera— con `fecha_int` ≥ el día 1 del mes
  actual menos `COMPROBACION_SIGRID_MESES − 1` meses (3 por defecto).
- **R19** (no deseado). SI una pasada falla, ENTONCES el hilo debe registrar
  el error y seguir con la siguiente pasada a su hora.
- **R20** (opcional). DONDE el intervalo sea 0 o falte sv5, el hilo no debe
  arrancar y el arranque debe decirlo en el log.
- **R21** (ubicuo). Cada pasada y cada comprobación manual deben dejar una
  línea de log `[comprobacion-sigrid]` con origen y recuentos.

## A4 · Aprobación y vistas (sv4)

- **R22** (ubicuo). El payload de registro (preflight, encolar, ejecutar)
  debe excluir siempre las líneas `registrado` y, salvo
  `incluir_borradas: true`, las `borrado_sigrid`; las respuestas deben
  devolver `excluidas: {registrado: n, borrado_sigrid: n}`.
- **R23** (no deseado). SI tras excluir no queda ninguna línea, ENTONCES el
  portal debe responder 422 diciendo cuántas se excluyeron y por qué.
- **R24** (estado). MIENTRAS una línea esté en `borrado_sigrid`, las vistas
  de obra y de trabajador deben pintarla como «borrada en Sigrid» (motivo en
  el tooltip) con un botón «Reaprobar» que envíe `incluir_borradas: true`, y
  la cabecera de la vista debe avisar de cuántas hay.
- **R25** (evento). CUANDO el preflight de una aprobación masiva devuelve
  `excluidas.borrado_sigrid > 0`, el modal debe decirlo y ofrecer una
  casilla que repita el preflight incluyéndolas (JS: verificación manual).
- **R26** (opcional). DONDE el registro esté configurado, las vistas de obra
  y de trabajador deben ofrecer «Comprobar en Sigrid» sobre todas sus
  líneas `registrado`, y cada fila de líneas debe llevar
  `data-sigrid-estado`.

## B · Estado «encolado»

- **R27** (evento). CUANDO `/api/aprobar/encolar` encola en asíncrono, su
  respuesta debe incluir los `registro_ids` encolados.
- **R28** (evento). CUANDO se llama a `POST /api/aprobar/estado` con 1–5000
  `registro_ids`, sv4 debe responder, sin escribir, el recuento por
  `sigrid_estado` y `pendientes` (las que siguen en `encolado`); fuera de
  ese rango, 422.
- **R29** (evento). CUANDO el modal encola en asíncrono, no debe recargar la
  página: debe sondear R28 cada 3 s hasta 120 s, y con 0 pendientes mostrar
  el resumen (registradas, omitidas, conflicto, error) y recargar al
  cerrar; agotado el plazo, decir cuántas siguen en cola.
- **R30** (estado). MIENTRAS una vista cargada tenga filas `encolado`, debe
  mostrar un aviso que sondee R28 cada 15 s (máx. 30 min) y, al llegar el
  resultado, ofrezca «Actualizar» sin recargar sola. El tooltip de
  `encolado` no debe pedir «recarga en unos segundos».

## C · Las 35 líneas de septiembre

- **R31** (evento). CUANDO, desplegados sv5 y sv4, corra la primera pasada
  de R18, las 35 líneas de PT26/00314 (explore §4.1) deben quedar en
  `borrado_sigrid`. Verificación: MANUAL (humano), design §9.

## No regresión

- **R32** (ubicuo). Siguen en verde las suites de F-002, F-004, F-017 y
  F-023; desaprobar no borra nada en Sigrid; ningún camino nuevo escribe en
  Sigrid; sv5 sigue sin PostgreSQL (F-002 R11).

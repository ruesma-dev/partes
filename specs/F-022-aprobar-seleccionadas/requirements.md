<!-- specs/F-022-aprobar-seleccionadas/requirements.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Requisitos (EARS)

Origen: petición del humano (2026-09-30) y correo de Juan Romero («RV:
CAPTURAS»): «opción de seleccionar varias líneas y aprobarlas, por si quiero
dejar alguna pendiente», descrito también como «las visibles». Esta spec cubre
**las dos cosas**: lo marcado con casilla y lo que queda visible tras filtrar.
Servicio: **solo sv4** (portal). sv5 no cambia (design §1). Se apoya en F-024
(exclusiones R22/R23, «Reaprobar», sondeo del modal) sin duplicarlo.
Diagnóstico de hoy, diseño y decisiones: `design.md` (§0, §2 y §8).

Vocabulario: «tabla» = `#lines-table` de la vista de obra («Líneas del
periodo») o de persona («Registros horarios»); «visible» = fila sin la clase
`filtered-day` (filtro por casillas de la matriz o por días del calendario) y
sin `display:none` (filtros por columna); «selección» = la selección común de
filas (casillas y Ctrl/Shift+clic); «ámbito» = la vista de la que salen los
ids (obra + periodo + modo, o persona). Tests: `test_f022_rN_*`, sin red ni
BBDD (SQLite en memoria y dobles de sv5, como F-024). La parte JS se verifica
con `node --check`, comprobaciones estáticas en pytest y la lista MANUAL de
`design.md` §9 (el proyecto no tiene arnés de tests JS).

## A · Selección en la tabla (vistas de obra y de persona)

- **R1** (ubicuo). Cada fila de la tabla debe llevar, dentro de su celda
  Fecha, una casilla `input.sel-linea` con el `data-registro-id` de la fila,
  también en las filas congeladas o ya registradas (DA6).
- **R2** (evento). CUANDO se marca o desmarca una casilla, la fila debe
  entrar o salir de la selección común, y CUANDO una fila entra o sale de la
  selección por Ctrl/Shift+clic, su casilla debe reflejarlo (DA3).
- **R3** (evento). CUANDO se pulsa «Seleccionar visibles», deben quedar
  seleccionadas todas las filas visibles y ninguna fila oculta debe añadirse;
  CUANDO se pulsa «Quitar selección», la selección debe quedar vacía.
- **R4** (ubicuo). El rango de Shift+clic debe seleccionar solo filas
  visibles (hoy incluye las ocultas por filtros).
- **R5** (ubicuo). Los filtros por columna y la ordenación deben ignorar la
  casilla (no leer su `value` como texto de la celda Fecha).
- **R6** (estado). MIENTRAS haya selección, el contador debe mostrar
  «N seleccionadas» y, si alguna está oculta por filtros, «(M ocultas: no se
  aprueban)».

## B · Qué aprueba el botón de cabecera

- **R7** (estado). En las dos vistas, el botón de cabecera debe:
  MIENTRAS haya selección, llamarse «Aprobar seleccionadas (N)» y aprobar las
  filas **seleccionadas y visibles**; sin selección y con algún filtro activo,
  «Aprobar visibles (N)» y aprobar las visibles; sin selección ni filtros,
  «Aprobar todo (N)» y aprobar todas las filas de la tabla (DA1, DA2).
- **R8** (no deseado). SI el conjunto a aprobar tiene 0 filas, ENTONCES el
  botón debe quedar deshabilitado con un `title` que diga por qué (nada
  visible, o todas las seleccionadas ocultas).
- **R9** (evento). CUANDO se filtra por casillas de la matriz (obra) o por
  días del calendario (persona) y no hay selección, el botón debe aprobar
  solo las filas que ese filtro deja visibles; quitar el filtro no debe
  vaciar la selección.
- **R10** (evento). CUANDO se aprueba desde el botón de cabecera, la
  petición a `/api/aprobar/preflight`, `/encolar` y `/ejecutar` —también la
  repetición con `incluir_borradas` (F-024 R25) y la de pisar conflictos—
  debe llevar `registro_ids` (los del conjunto) y `ambito`: en obra
  `{vista:"obra", obra_key, period, mode}`, en persona `{vista:"trabajador",
  worker_key}`.
- **R11** (ubicuo). El modal de confirmación debe decir el alcance:
  «N seleccionadas», «N visibles (filtros activos)» o «todas (N)», de las M
  filas de la tabla.
- **R12** (ubicuo). Los botones por línea («Aprobar», «Reaprobar», «↻»,
  «Revisar») deben aprobar solo su línea aunque esté seleccionada, sin
  `ambito`, como hoy (DA9).

## C · Validación en el servidor (sv4)

- **R13** (evento). CUANDO preflight, encolar o ejecutar reciben `ambito`,
  sv4 debe resolver los ids de esa vista —obra: los de
  `registro_ids_de_obra(obra_key, period, mode)`; persona: los de
  `registro_ids_de_trabajador(worker_key)`, que son las filas que pinta su
  tabla (DA12)— y seguir solo con los `registro_ids` pedidos.
- **R14** (no deseado). SI con `ambito` algún id pedido no está entre los de
  la vista (otra obra, otro periodo, otra persona, papelera o inexistente),
  ENTONCES sv4 debe responder 422 `{ok:false, error, fuera_de_ambito: n}`
  sin llamar a sv5, sin publicar y sin marcar ninguna línea (DA7).
- **R15** (no deseado). SI `ambito` trae una `vista` desconocida o le falta
  su clave, o `registro_ids` viene vacío o con más de 5000 ids distintos,
  ENTONCES sv4 debe responder 422 sin llamar a sv5 (DA11).
- **R16** (ubicuo). Tras validar el ámbito, las exclusiones de F-024 deben
  aplicarse sin cambios sobre lo pedido (`registrado` siempre fuera,
  `borrado_sigrid` salvo `incluir_borradas`, `encolado` viaja) y `excluidas`
  debe contar solo líneas pedidas.
- **R17** (no deseado). SI las líneas que viajarían a sv5 son de más de una
  obra (clave de obra de la línea), ENTONCES sv4 debe responder 422
  `{ok:false, error, obras:[{codigo, nombre, lineas}]}` sin llamar a sv5,
  **con o sin `ambito`** (DA8: hoy se escribirían en la obra de la primera).
- **R18** (ubicuo). Una petición sin `ambito` (botón por línea, o JS antiguo
  en caché que envía `obra_key`) debe comportarse como hoy, salvo R17.

## D · Lo que cuenta y lo que cambia

- **R19** (ubicuo). El payload a sv5 (preflight, ejecutar y el de la cola)
  debe llevar solo las líneas pedidas que pasan R16, y los conflictos, los
  avisos de calendario y el bloqueo por Sesame deben calcularse solo sobre
  ellas: un DNI con calendario no fiable que no está en la selección no
  debe bloquear.
- **R20** (evento). CUANDO se encola un subconjunto de la vista, solo esas
  líneas deben pasar a `encolado` y aparecer en `registro_ids` de la
  respuesta; el resto de líneas de la vista debe conservar exactos su
  `sigrid_estado` y su `sigrid_motivo` (quedan pendientes, sin cambios).
- **R21** (ubicuo). El payload que reciben sv5 y la cola debe conservar su
  forma actual (`obra`, `lineas`, `pisar_claves`, `usuario`): `ambito` no
  sale de sv4 y sv5 no necesita cambios.

## E · No regresión

- **R22** (ubicuo). Siguen en verde las suites de F-002, F-003, F-004,
  F-017 y F-024 de sv4 (adaptando con nota escrita solo lo que cambie por
  R17 o por la clave nueva `obras`, design §4); no se crean endpoints nuevos
  (el inventario de `test_f016` no cambia); `node --check` pasa sobre
  `static/app.js` y las dos plantillas parsean en Jinja2.

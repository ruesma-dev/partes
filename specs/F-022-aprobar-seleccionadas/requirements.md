<!-- specs/F-022-aprobar-seleccionadas/requirements.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Requisitos (EARS)

Origen: petición del humano (2026-09-30) y correo de Juan Romero («RV:
CAPTURAS»): «opción de seleccionar varias líneas y aprobarlas, por si quiero
dejar alguna pendiente», descrito también como «las visibles». Cubre **lo
marcado con casilla y lo visible tras filtrar**. Revisión 2026-10-01 (DA8 del
humano): una aprobación con líneas de **varias obras** no se rechaza, **cada
línea va al parte de SU obra**. Servicio: **solo sv4**; sv5 no cambia (design
§1). Se apoya en F-024 (exclusiones R22/R23, «Reaprobar», sondeo) sin
duplicarlo. Diagnóstico, diseño y decisiones: `design.md` §0, §2 y §8.

Vocabulario: «tabla» = `#lines-table` de la vista de obra o de persona;
«visible» = fila sin `filtered-day` (casillas de la matriz o días del
calendario) y sin `display:none` (filtros por columna); «selección» = la
selección común de filas (casillas y Ctrl/Shift+clic); «ámbito» = la vista de
la que salen los ids; «grupo» = las líneas que viajan de una misma obra
(`obra_key_for_registro`). Tests `test_f022_rN_*`, sin red ni BBDD (SQLite y
dobles de sv5, publisher y calendario). JS: `node --check`, comprobaciones
estáticas en pytest y MANUAL de `design.md` §9.

## A · Selección en la tabla (obra y persona)

- **R1** (ubicuo). Cada fila de la tabla debe llevar en su celda Fecha una
  casilla `input.sel-linea` con su `data-registro-id`, también si está
  congelada o registrada (DA6).
- **R2** (evento). CUANDO se marca o desmarca una casilla, la fila debe
  entrar o salir de la selección común, y Ctrl/Shift+clic debe reflejarse en
  la casilla (DA3).
- **R3** (evento). CUANDO se pulsa «Seleccionar visibles», deben quedar
  seleccionadas todas las filas visibles y ninguna oculta; CUANDO se pulsa
  «Quitar selección», la selección debe quedar vacía.
- **R4** (ubicuo). El rango de Shift+clic debe incluir solo filas visibles.
- **R5** (ubicuo). Filtros por columna y ordenación deben ignorar la casilla.
- **R6** (estado). MIENTRAS haya selección, un contador debe mostrar
  «N seleccionadas» y, si las hay, «(M ocultas: no se aprueban)».

## B · Qué aprueba el botón de cabecera

- **R7** (estado). MIENTRAS haya selección, el botón debe decir «Aprobar
  seleccionadas (N)» y aprobar las seleccionadas **visibles**; sin selección
  y con algún filtro, «Aprobar visibles (N)» y las visibles; sin selección
  ni filtros, «Aprobar todo (N)» y toda la tabla (DA1, DA2).
- **R8** (no deseado). SI el conjunto tiene 0 filas, ENTONCES el botón debe
  quedar deshabilitado con un `title` que diga por qué.
- **R9** (evento). CUANDO un filtro de matriz (obra) o de calendario
  (persona) está activo y no hay selección, el botón debe aprobar solo las
  filas visibles; quitar el filtro no debe vaciar la selección.
- **R10** (evento). CUANDO se aprueba desde el botón de cabecera, toda
  petición a `/api/aprobar/preflight`, `/encolar` y `/ejecutar` (también
  las repeticiones con `incluir_borradas` y con claves que pisar) debe
  llevar `registro_ids` y `ambito`: obra `{vista:"obra", obra_key, period,
  mode}`, persona `{vista:"trabajador", worker_key}`.
- **R11** (ubicuo). El modal debe decir el alcance («N seleccionadas», «N
  visibles (filtros activos)» o «todas (N)») sobre las M filas de la tabla.
- **R12** (ubicuo). Los botones por línea deben aprobar solo su línea aunque
  esté seleccionada, sin `ambito`, como hoy (DA9).

## C · Validación en el servidor (sv4)

- **R13** (evento). CUANDO llega `ambito`, sv4 debe resolver los ids de la
  vista (obra: `registro_ids_de_obra(obra_key, period, mode)`; persona:
  `registro_ids_de_trabajador(worker_key)`, las filas de su tabla) y seguir
  solo con los `registro_ids` pedidos.
- **R14** (no deseado). SI con `ambito` algún id no es de la vista,
  ENTONCES 422 `{ok:false, error, fuera_de_ambito: n}` sin llamar a sv5, sin
  publicar y sin marcar ninguna línea (DA7).
- **R15** (no deseado). SI `ambito` trae `vista` desconocida o sin su clave,
  o `registro_ids` está vacío o pasa de 5000 distintos, ENTONCES 422 sin
  llamar a sv5 (DA11).
- **R16** (ubicuo). Las exclusiones de F-024 (`registrado` siempre,
  `borrado_sigrid` salvo `incluir_borradas`) deben aplicarse sin cambios y
  `excluidas` debe contar solo líneas pedidas. Sin `ambito` (botón por
  línea, JS antiguo con `obra_key`), sv4 debe seguir como hoy salvo §D.

## D · Reparto por obra (sv4)

- **R17** (ubicuo). sv4 debe agrupar las líneas que viajan por obra y
  enviar a sv5 **una petición por grupo**, con la `obra` del grupo y solo
  sus líneas; ninguna línea debe viajar con la obra de otro grupo. No se
  agrupa por mes: sv5 ya reparte cada petición por mes natural (DA8).
- **R18** (no deseado). SI hay más de `APROBACION_MAX_OBRAS` grupos (10),
  ENTONCES 422 con el desglose por obra y sin llamar a sv5 (DA15).
- **R19** (ubicuo). Preflight, encolar y ejecutar deben devolver
  `grupos: [{clave, obra, registro_ids, …}]` en orden de clave, y los campos
  planos de hoy agregados; con un solo grupo, los planos idénticos a hoy.
- **R20** (no deseado). SI el preflight de un grupo falla, ENTONCES ese
  grupo debe salir con `ok:false` y su `error` y los demás seguir; el plano
  `ok` es `true` si algún grupo pudo evaluarse.
- **R21** (ubicuo). El bloqueo por Sesame y los avisos de calendario deben
  calcularse **por grupo**; ejecutar y encolar no deben enviar un grupo
  bloqueado sin `forzar_sin_sesame` (lo dejan `bloqueado_sesame`, sin
  tocar sus líneas); SI todos lo están, ENTONCES 422 con `sesame_bloqueo`
  como hoy.
- **R22** (ubicuo). Las claves que pisar deben ir como `<grupo>::<clave>` y
  cada grupo recibir solo las suyas (la clave de sv5 no lleva obra); SI
  llegan claves sin grupo con más de un grupo, ENTONCES 422.
- **R23** (evento). CUANDO se encola, sv4 debe publicar una petición por
  grupo no bloqueado y marcar `encolado` cada grupo tras publicarlo; la
  respuesta debe traer `peticiones`, `registro_ids` (todos los encolados) y
  por grupo `estado`, `peticion_id` y `error`.
- **R24** (no deseado). SI publicar un grupo falla, ENTONCES ese grupo debe
  quedar `error_cola` sin cambiar sus líneas y los demás seguir; SI fallan
  todos, ENTONCES 502 sin ninguna línea marcada.
- **R25** (evento). CUANDO se ejecuta en síncrono (pisar, override de
  Sesame o sin colas), sv4 debe ejecutar los grupos uno a uno y trazar cada
  uno con sus ids: un grupo con `ok:false` deja en `error` solo sus líneas
  (F-002 R14). El plano `ok` es `true` solo si todos van bien, con
  `parcial: true` si unos sí y otros no (DA16: no hay «todo o nada»).

## E · Modal y resultado (navegador)

- **R26** (ubicuo). El modal de preflight debe mostrar una sección por obra
  (líneas, partes, conflictos, avisos, bloqueo o error) y un total; los
  grupos con error o bloqueados deben decir «no se registrará» y por qué.
- **R27** (evento). CUANDO se confirma, deben ir por `ejecutar` los grupos
  con claves marcadas o bloqueados con la casilla de Sesame, y por
  `encolar` el resto evaluado; los grupos con error de preflight no se
  envían.
- **R28** (evento). CUANDO llega el resultado, el modal debe mostrarlo por
  obra (síncrono) o sondear `POST /api/aprobar/estado` por grupo cada 3 s
  hasta 120 s (F-024 R29), y listar las obras que quedaron sin registrar
  con su motivo, más el total.

## F · Lo que cuenta y lo que cambia

- **R29** (ubicuo). Cada payload a sv5 debe llevar solo líneas pedidas que
  pasan R16, y conflictos, avisos y bloqueo deben contar solo esas: un DNI
  sin calendario fiable fuera de la selección no debe bloquear.
- **R30** (evento). CUANDO se aprueba un subconjunto, solo esas líneas
  deben cambiar de estado; el resto de la vista debe conservar exactos su
  `sigrid_estado` y su `sigrid_motivo`.
- **R31** (ubicuo). Cada payload a sv5 y a la cola debe conservar la forma
  de hoy (`obra`, `lineas`, `pisar_claves`, `usuario`); ni `ambito` ni el
  grupo salen de sv4. La idempotencia sigue siendo la `synckey` por línea.

## G · No regresión

- **R32** (ubicuo). Siguen en verde las suites de F-002, F-003, F-004,
  F-017 y F-024 de sv4 (adaptando con nota escrita solo lo inventariado en
  T1); no hay endpoints nuevos; `node --check` pasa y las dos plantillas
  parsean en Jinja2.

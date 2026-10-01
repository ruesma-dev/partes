<!-- specs/F-022-aprobar-seleccionadas/requirements.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Requisitos (EARS)

Origen: humano (2026-09-30) y correo de Juan Romero («RV: CAPTURAS»):
«seleccionar varias líneas y aprobarlas, por si quiero dejar alguna
pendiente», también «las visibles». Cubre **lo marcado y lo visible tras
filtrar**. Aprobada el 2026-10-01 con: **cada línea va al parte de SU obra**
(reparto por obra, DA8), rigor `critico` y un **listado** de lo que se va a
aprobar en el modal, al estilo del portal de dedicación (DA19). Servicio:
**solo sv4**; sv5 no cambia. Se apoya en F-024 sin duplicarlo. Diseño y
decisiones: `design.md`.

Vocabulario: «tabla» = `#lines-table` de la vista de obra o de persona;
«visible» = fila sin `filtered-day` (matriz o calendario) ni `display:none`
(filtros por columna); «selección» = la común de filas (casillas y
Ctrl/Shift+clic); «ámbito» = la vista de la que salen los ids; «grupo» = las
líneas que viajan de una misma obra (`obra_key_for_registro`). Tests
`test_f022_rN_*` sin red ni BBDD (SQLite y dobles de sv5, publisher y
calendario). JS: `node --check`, estáticos en pytest y MANUAL (design §9).

## A · Selección en la tabla (obra y persona)

- **R1** (ubicuo). Cada fila debe llevar en su celda Fecha una casilla
  `input.sel-linea` con su `data-registro-id`, también si está congelada.
- **R2** (evento). CUANDO se marca o desmarca una casilla, la fila debe
  entrar o salir de la selección común, y Ctrl/Shift+clic debe reflejarse en
  la casilla.
- **R3** (evento). CUANDO se pulsa «Seleccionar visibles», deben quedar
  seleccionadas las visibles y ninguna oculta; «Quitar selección» la vacía.
- **R4** (ubicuo). Shift+clic debe seleccionar solo filas visibles; filtros
  y ordenación deben ignorar la casilla.
- **R5** (estado). MIENTRAS haya selección, un contador debe mostrar
  «N seleccionadas» y, si las hay, «(M ocultas: no se aprueban)».

## B · Qué aprueba el botón de cabecera

- **R6** (estado). Con selección, «Aprobar seleccionadas (N)» aprueba las
  seleccionadas **visibles**; sin selección y con filtros (también los de
  matriz o calendario), «Aprobar visibles (N)» las visibles; sin nada,
  «Aprobar todo (N)» toda la tabla. Quitar un filtro no vacía la selección.
- **R7** (no deseado). SI el conjunto tiene 0 filas, ENTONCES el botón debe
  quedar deshabilitado con un `title` que diga por qué.
- **R8** (evento). CUANDO se aprueba desde la cabecera, toda petición a
  `/api/aprobar/preflight`, `/encolar` y `/ejecutar` debe llevar
  `registro_ids` y `ambito` (obra `{vista:"obra", obra_key, period, mode}`,
  persona `{vista:"trabajador", worker_key}`), también al repetir.
- **R9** (ubicuo). Los botones por línea deben aprobar solo su línea aunque
  esté seleccionada, sin `ambito`, como hoy.

## C · Validación en el servidor (sv4)

- **R10** (evento). CUANDO llega `ambito`, sv4 debe resolver los ids de la
  vista (obra: `registro_ids_de_obra`; persona: `registro_ids_de_trabajador`,
  las filas de su tabla) y seguir solo con los pedidos.
- **R11** (no deseado). SI con `ambito` algún id no es de la vista, ENTONCES
  422 `{ok:false, error, fuera_de_ambito: n}` sin llamar a sv5, publicar ni
  marcar nada.
- **R12** (no deseado). SI `ambito` trae `vista` desconocida o sin su clave,
  o `registro_ids` está vacío o pasa de 5000, ENTONCES 422 sin llamar a sv5.
- **R13** (ubicuo). Las exclusiones de F-024 (`registrado` siempre,
  `borrado_sigrid` salvo `incluir_borradas`) no cambian y `excluidas` cuenta
  solo lo pedido. Sin `ambito`, sv4 sigue como hoy salvo §D.

## D · Reparto por obra (sv4)

- **R14** (ubicuo). sv4 debe enviar a sv5 **una petición por grupo**, con la
  `obra` del grupo y solo sus líneas; ninguna línea viaja con otra obra. No
  se agrupa por mes (sv5 ya parte por mes natural).
- **R15** (no deseado). SI hay más de `APROBACION_MAX_OBRAS` grupos (10),
  ENTONCES 422 con el desglose por obra, sin llamar a sv5.
- **R16** (ubicuo). Preflight, encolar y ejecutar deben devolver `grupos`
  en orden de clave y los campos planos de hoy agregados; con un grupo, los
  planos idénticos a hoy.
- **R17** (no deseado). SI el preflight de un grupo falla, ENTONCES ese
  grupo sale con `ok:false` y `error` y los demás siguen; el plano `ok` es
  `true` si algún grupo pudo evaluarse.
- **R18** (ubicuo). Bloqueo por Sesame y avisos de calendario deben ir **por
  grupo**; un grupo bloqueado sin `forzar_sin_sesame` no se envía
  (`bloqueado_sesame`, líneas intactas); SI lo están todos, ENTONCES 422 con
  `sesame_bloqueo` como hoy.
- **R19** (ubicuo). Las claves que pisar deben ir como `<grupo>::<clave>` y
  cada grupo recibir solo las suyas; SI llegan sin grupo con más de uno,
  ENTONCES 422.
- **R20** (evento). CUANDO se encola, sv4 debe publicar una petición por
  grupo no bloqueado y marcar `encolado` cada grupo tras publicarlo, y
  responder `peticiones`, `registro_ids` y por grupo `estado`,
  `peticion_id` y `error`.
- **R21** (no deseado). SI publicar un grupo falla, ENTONCES queda
  `error_cola` sin cambiar sus líneas y los demás siguen; SI fallan todos,
  ENTONCES 502 sin marcas.
- **R22** (evento). CUANDO se ejecuta en síncrono (pisar, override o sin
  colas), los grupos van uno a uno y cada uno se traza con sus ids; uno con
  `ok:false` deja en `error` solo sus líneas; plano `ok` solo si todos van
  bien, con `parcial: true` si no (sin «todo o nada»).

## E · Listado en el modal (DA19)

- **R23** (ubicuo). El preflight debe devolver por grupo un `listado`
  construido **en el servidor** con la respuesta de sv5 (no lo deduce el
  navegador): una fila por línea pedida con `registro_id`, fecha,
  trabajador, tipo (ordinaria/extra/incidencia), código de hora, horas que
  se escribirán, partida, recurso, `estado` y `motivo`.
- **R24** (ubicuo). `estado` debe ser `conflicto` si la línea está en algún
  conflicto; `omitida` o `ya_registrada` según la acción de sv5 (con su
  motivo); si se escribe, `nuevo` sin intento previo y `reaprobacion` si
  venía de `borrado_sigrid`, `error`, `omitido`, `conflicto` o `encolado`
  (motivo «antes: …»); `no_se_registra` con el error si el grupo falló.
- **R25** (ubicuo). Cada grupo y el conjunto deben traer `totales`: líneas
  por estado, horas ordinarias y extra e incidencias que se escribirán.
- **R26** (ubicuo). El preflight debe devolver `excluidas_detalle` (fecha,
  trabajador, obra, horas, motivo: ya registrada con su parte, o borrada en
  Sigrid y cómo incluirla); el modal las lista aparte, junto a las M
  marcadas ocultas que no se enviaron (dato del navegador).
- **R27** (ubicuo). El modal debe mostrar el alcance («N seleccionadas»,
  «N visibles», «todas (N)» de M), el total general y una sección por obra
  con su resumen siempre visible, partes, conflictos, bloqueo o error, y su
  tabla del listado ordenada por fecha y trabajador.
- **R28** (estado). MIENTRAS el listado pase de 40 filas, las secciones
  deben abrirse plegadas, con la tabla en un área con scroll y cabecera
  fija; conflictos, errores y bloqueos deben verse sin desplegar.

## F · Confirmación y resultado (navegador)

- **R29** (evento). CUANDO se confirma, van por `ejecutar` los grupos con
  claves marcadas o bloqueados con la casilla de Sesame, y por `encolar` el
  resto evaluado; los grupos con error de preflight no se envían.
- **R30** (evento). CUANDO llega el resultado, el modal debe mostrarlo por
  obra (síncrono) o sondear `POST /api/aprobar/estado` por grupo cada 3 s
  hasta 120 s (F-024 R29), y listar las obras sin registrar con su motivo.

## G · Lo que cuenta, lo que cambia y no regresión

- **R31** (ubicuo). Cada payload a sv5 debe llevar solo líneas pedidas que
  pasan R13, y conflictos, avisos y bloqueo deben contar solo esas.
- **R32** (evento). CUANDO se aprueba un subconjunto, solo esas líneas
  cambian de estado; el resto conserva `sigrid_estado` y `sigrid_motivo`.
- **R33** (ubicuo). Cada payload a sv5 y a la cola conserva su forma
  (`obra`, `lineas`, `pisar_claves`, `usuario`); ni `ambito`, ni grupo, ni
  listado salen de sv4. La idempotencia sigue siendo la `synckey`.
- **R34** (ubicuo). Siguen en verde las suites de F-002, F-003, F-004,
  F-017 y F-024 de sv4 (adaptando con nota solo lo inventariado en T1); no
  hay endpoints nuevos; `node --check` y Jinja2 pasan.

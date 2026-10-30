<!-- progress/current.md -->
# Trabajo en curso

## F-047 · EN CURSO (implementer; desbloqueada 2026-10-31): parte nuevo en espera hasta que sv3 reparta sus horas

**Desbloqueo (2026-10-31)**: el humano eligió la opción A del bloqueo (literal: «a» a «¿A y el ajuste
aprobado?»): DA3 → B (solo el motivo `nuevo` en R16 y R17) y desviación de design §4 (`joinedload` +
`estado_seguimiento` sobre `r.document`, 0 sentencias nuevas). Registrado en `design.md` §4 y §11,
`requirements.md` R16–R17 y `tasks.md` T6. F-047 vuelve a `in_progress`. Lo que sigue es el
registro del bloqueo, conservado como historia.

DA11–DA13 = A decididas por el humano el 2026-10-30 (literal: «ok» a «F-047: A, A, A. Lanzo el
implementer.»), registradas en `design.md` §11; DA13 aplicada al texto de R19. Rama
`feature/F-047-parte-nuevo-en-espera`, worktree `partes-wt-f047`. Informe parcial (trazas RED de
T1–T6): `progress/impl_F-047.md`.
- **Hecho y commiteado (T1–T5, en verde)**: ORM (comentario, dos copias), sv3 completo (pedido en
  `save_parte`, marca tras conciliar, `build_app`), sv4 `motivo_espera` + `motivos_espera`, contrato
  raíz R24–R25. Suite sv3 completa: 2371 passed.
- **T6 sin commitear en el worktree** (R15–R17): guarda en `approve_document` (repositorio y ruta),
  exclusión `recalculando` en `lineas_para_registro`, texto en `_motivo_sin_lineas`, 50 tests F-047
  sv4 en verde. Rompe **4 tests existentes** (DA8 ⇒ `blocked`):
  1. **Choque de diseño (decisión del humano)** — `test_f046_aplicar.py`: `r33_aplicar_reajusta_en_sigrid_y_registra`,
     `r34_sin_respuesta_sigue_aplicando_y_se_reintenta`, `r33_encolar_aplica_por_http_y_encola_las_lineas`.
     En «Aprobar» con «Aplicar» (F-046 R33), `_aplicar_reparto` reajusta en Sigrid, **pide el recálculo
     seguido** de los partes del día (`_pedir_recalculo_seguido` escribe un pedido uuid4 ⇒ `pendiente`)
     y, en la MISMA petición, `lineas_para_registro` registra esas líneas. Con DA3-A (excluir los partes
     en espera de los dos motivos) esas líneas salen `recalculando` y no se registra nada. La
     revalidación no lo vio. Opciones:
     - **A (recomendada)**: DA3 → «solo el motivo `nuevo`» en la exclusión de la aprobación en bloque
       (R17) y en `approve_document` (R16) — es la alternativa B que ya listaba DA3. El recálculo de
       F-042/F-043 (uuid4) sigue como en F-043 DA12 y F-046 no cambia.
     - B: mantener los dos motivos, pero calcular la espera ANTES de aplicar los repartos (o eximir los
       partes cuyo pedido escribió esta misma petición); toca el flujo de F-046 en `app.py`.
     - C: mantener DA3-A tal cual y cambiar F-046 R33 (deja de registrar en el mismo clic): contra DA8.
  2. **Mecánico (propuesta de desviación, ya probada)** — `test_f062_inicio_con_ciz.py::test_f062_r5_sin_consultas_nuevas`
     fija en 5 las sentencias de `lineas_para_registro`; la consulta extra de `motivos_espera` (design §4)
     la sube a 6. En el worktree ya está la alternativa: `joinedload(ParteRegistroOrm.document)` en el
     SELECT de líneas que ya existe y el estado con `estado_seguimiento` sobre `r.document`
     (0 sentencias nuevas): F-062 vuelve a verde. Falta adaptar mi test
     `test_f047_r17_una_sola_pregunta_por_la_espera` (espía `motivos_espera`) a contar sentencias.
- Con la decisión: aplicar A/B/C en T6, completar T6 y seguir con T7–T14. La mutación la lanza el líder.

## F-047 · spec revalidada 2026-10-30 (spec-author; DA11–DA13 = A el mismo día): parte nuevo en espera hasta que sv3 reparta sus horas

Orden del humano (2026-10-30): «vamos con f47». Rama `feature/F-047-parte-nuevo-en-espera`,
worktree `partes-wt-f047`, con `dev` 75816f2 fusionado (795a546). La spec del 2026-10-14
(DA1–DA10 aprobadas) se ha contrastado con el código actual de sv3 y sv4: **13 cambios
mecánicos** aplicados (mismo comportamiento; lista en `tasks.md` «Revalidación 2026-10-30»)
y **3 decisiones abiertas nuevas**, todas con recomendación A (`design.md` §11):
- **DA11** matriz «Horas por día» de la obra (F-049): no se marca la espera (A) o sí (B, choca con DA8).
- **DA12** parte sin obra o sin fecha (F-054): espera como todos (A) o sin pedido (B).
- **DA13** candado de F-046 (hasta 300 s): R19 sin cifra cerrada (A) o tal cual (B).
La causa (commit antes de conciliar) sigue cierta; la cifra de 20–40 s no se ha vuelto a medir
(M3 la mide). Detalle en `progress/explore_F-047_revalidacion.md`. El implementer NO empieza
hasta que el humano decida DA11–DA13.

## F-056 · CERRADA y ACTIVADA 2026-10-30 (review APPROVED pasada 2, rigor crítico; 14 equivalentes aceptados por el humano; desplegada sv5 → sv4; M2 OK en local, `progress/m2_F-056.md`; M3 OK; `FRANQUICIA_CAMPO_EXT=10` en sv5 `ca-sv5-transfer--0000004`; M2 (g) no se hace, cubierta por tests; cerrada por el humano: «entoces cierra feature»): franquicia de extras

Spec en `specs/F-056-franquicia-de-extras/` (rama `feature/F-056-franquicia-de-extras`,
worktree `partes-wt-f056`, desde `dev` 560d753); resumen para el líder en
`progress/spec_F-056.md`. Toca sv5 (cálculo contra Sigrid, alta y edición de la línea `HE*`
negativa, exclusión en los choques) y sv4 (tabla `empleado_franquicia`, aviso en el modal de
aprobar, `franquicia_ajuste`, aplicar al terminar el registro); sv3 solo la copia del ORM.
**Decididas por el humano** (2026-10-23, literal: «a a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo» ⇒ DA1–DA20 = A; `design.md` §7) (las más de fondo: DA2 periodo = mes de nómina 16 → 15, DA3 extras netas `HE*` de
Sigrid, DA4 una línea en la obra de más horas, DA8 recalcular editando, DA12 sin bloqueo de
servidor, DA20 una feature con corte tras T7). M1 (solo lectura) hecha por el spec-author:
`design.md` §2 H5. M2–M4 son del humano (§10).

**Arranque (2026-10-27).** Rama puesta al día con `git merge dev` (39aef7b: trae F-058…F-064). La
spec es del 2026-10-23: el implementer comprueba antes de T1 que sigue encajando con lo fusionado
después (sobre todo F-060/F-062 en sv5 y F-053 «pisar sin borrar»); si no, `blocked` y se consulta.

**Implementación (implementer, 2026-10-27)** — detalle y trazas RED en `progress/impl_F-056.md`.
- Encaje comprobado antes de T1: el diseño sigue valiendo tras F-058…F-064. `RegistroPipeline._choques`
  delega en `pisado.choques` (R31 cubre el registro con un solo cambio); `ReajustePipeline._choques`
  igual que en la spec; `_crear_parte` sin cambios; F-060/F-062 (`partes:<id>:ciz`) no chocan con
  `partes:franquicia:<id>` (`registro_de_synckey` devuelve None). Guardianes de raíz en 7 tablas ⇒ 9.
- Bloque sv5 (T1–T7) HECHO: suite sv5 1344 passed. Decisiones: `inicio`/`fin`/`fecha_int` como
  `YYYYMMDD` (como `hmores.fec`); `preparar` recibe una extra con `horas = -1` solo para que las
  reglas den código, precio y cuenta (la cantidad real es A, calculada dentro del lock); la
  escritura va por `escribir` (una sentencia) y decide la relectura (R29); `tex` en recálculo no
  cambia (el `UPDATE` de F-046 solo toca `can` y `tot`, como manda la spec).
- **CORTADO TRAS T7 A LA ESPERA DE DA1** (orden del líder, 2026-10-27): el humano valora definir
  la franquicia (quién la tiene y su X) en un campo nuevo de Sigrid en vez de en la tabla
  `empleado_franquicia`; eso cambiaría T8, T9, T14 y parte de T10–T13. El bloque sv5 vale tal cual
  (recibe X en la petición). T8 llegó a commitearse (95c9817: ORM de las dos tablas + guardianes a
  nueve) antes del aviso y se revirtió en 4e43d80; queda recuperable si DA1 sigue en A.
  Nada de sv4 en la rama. Siguiente paso: decisión del humano sobre DA1 y, con ella, T8–T20.

**Enmienda de la spec (spec-author, 2026-10-27): DA1 = C por el humano.** Literal: «para saber que
trabajadores son franquiciados y cual es el valor de la franquicia habra que crear un campo en
sigrid que lo defina» y «va a ir en recursos. la fecha no hace falta, se aplica en los partes que se
registren si esta activo (valor distinto de 0 o null). el campo lo rellena adminen sigrid.» X pasa a
un campo nuevo de `res` (nombre en `FRANQUICIA_CAMPO_RES` de sv5, aún sin crear); solo sv5 lo lee
(endpoint nuevo `/api/franquicia/recursos`); caen `empleado_franquicia` y la pantalla (DA19);
`franquicia_ajuste` se queda; `tex` sin cifras. Tareas renumeradas: T8–T11 enmiendan sv5, T12–T18
sv4, T19–T22 cierre. Resumen en `progress/spec_F-056.md`.
**Decisiones abiertas para el humano** (`design.md` §7, recomendación A): DA2/DA17/DA20 enmendadas,
DA21 solo sv5 lee el campo, DA22 vale la X de Sigrid al aplicar, DA23 fallo de configuración = no
se aplica y se avisa, DA24 valores raros = `invalida`, DA25 se mantiene `franquicia_ajuste`, DA26
`tex` sin cifras, DA27 franquicia del recurso. Hasta su aprobación, el implementer NO sigue.

**Bloqueo de tipos numéricos (2026-10-27) resuelto por el líder: manda design.md §4, 9 tipos.** Implementer reanuda en T8.
- T8 HECHO (dominio y puro). Desviación menor: `CAMPO_RE` acaba en `\Z` y no en `$` (en Python `$`
  admite un salto de línea final tras el nombre; misma regla, sin ese hueco).
- T9 HECHO (settings y cliente). `CAMPO_RE` se importa dentro de `valores_campo_res`: `franquicia` ->
  `pisado` -> cliente forman ciclo.
- T10 HECHO (pipeline). Decisiones: un recurso pedido que no esta en `res` es `invalida` (nunca
  X = 0); en `comprobar`/`ejecutar` un fallo al leer el TIPO es `no_disponible` => `no_editable`
  (R42), mientras que `franquicias()` lo propaga (design 6: 502 en `/recursos`).
- T11 HECHO (API, `/health`, cableado en `main.py`): bloque sv5 cerrado, suite sv5 1458 passed.
- T12 HECHO: `franquicia_ajuste` (24 columnas, `franquicia` Float NULL) en las dos copias del ORM
  (byte-idénticas) y guardianes de la raíz a OCHO tablas.
- T13 HECHO (sv4 puro). Disparador nuevo según DA7 (A): una línea del DÍA DE AJUSTE de un recurso
  con franquicia `activa` (o `invalida`, solo informa); un ajuste vivo sale con cualquier línea
  del periodo (R10). Con el calendario no fiable (R6) sale sin día y con motivo.
- T14 HECHO (repositorio y cliente). Transiciones: ajustar (sin fila o desde rechazado) y
  recalcular (desde aplicado/decidido/error) -> decidido; no_ajustar (sin fila) -> rechazado;
  el resto, 409. La identidad del trabajador en el periodo es su recurso + su DNI (R12).
- T15 HECHO (preflight y decisiones). Orden en `ejecutar`/`encolar`: se VALIDAN las franquicias
  (422 formato/ámbito/clave; 409 varios recursos o `ajustar` sin día ni obra) antes de nada, luego
  los repartos de F-046, luego se GUARDAN las decisiones (CAS, 409 si cambió) y luego las líneas.
  Las claves válidas salen de las líneas pedidas (también las ya registradas, nuevo
  `recurso_fechas_de`). Un fallo propio del aviso en el preflight sale como `aviso`, no 500.
  Suite sv4: 3113 passed, 1 skipped.
- T16 HECHO (aplicar y contexto de la vista). `aplicar` solo desde `decidido`/`error` (409 si no,
  sin sv5); 404 si no existe; sin respuesta de sv5 => `error` sin pisar E/A/X (se reintenta, R19).
  La vista (solo modo nómina) lleva `franquicia` con X usada, X actual (UNA llamada a `/recursos`)
  y la acción que admite cada fila: aplicar (decidido/error), recalcular (aplicado), ajustar
  (rechazado, o sin fila con franquicia activa).
  **HUECO DE LA SPEC (pendiente de decisión):** R20 pide «Ajustar» y «Recalcular» en la vista, pero
  la spec solo define `POST /api/franquicia/{id}/aplicar`; no hay ruta para DECIDIR desde la vista
  (y sin fila no hay id). No se improvisa: T17 hace el modal y «Aplicar» de la vista; los botones
  «Ajustar»/«Recalcular» de la vista quedan a la espera de la decisión del humano.
- T17 HECHO (portal). Modal: aviso (`franquiciasHtml`), «Registrar» deshabilitado hasta decidir
  (`vigilarDecisionesFranquicia`), cada decisión viaja UNA vez con la llamada que lleva sus líneas
  (`franquiciasPara`; para eso cada candidato lleva ahora `registro_ids`), y `aplicarFranquicias`
  aplica al terminar el registro (síncrono: ya; cola: cuando el sondeo acaba) avisando si la X
  usada difiere de la del aviso (DA22). Vista: tabla del ajuste y botón «Aplicar» (decidido/error).
- T18 HECHO: contrato raíz `tests/test_f056_contrato_franquicia.py` (5 passed; sensibilidad
  comprobada mandando la X a propósito). Guardianes: F-017 pasa a 19 `_actor(request)` (aplicar,
  R21); F-043 sin recargas nuevas (la vista usa el «Actualizar» de siempre).
  `bash harness/init.sh` ENTORNO LISTO (cobertura 98,6 %, 999/1013). Informe: `progress/impl_F-056.md`.

**F-056 BLOQUEADA (2026-10-27, implementer) — pregunta para el humano.** R20 pide en la vista de
trabajador «Ajustar» (`rechazado`, o sin fila con franquicia `activa`) y «Recalcular» (`aplicado`),
pero la spec solo define `POST /api/franquicia/{id}/aplicar` (design §5): no hay ruta para DECIDIR
desde la vista y, sin fila, ni siquiera hay `id`. No se ha improvisado. Opciones:
**A** (recomendada) `POST /api/franquicia/decidir {recurso_ide, periodo, decision}` con la misma
validación y CAS de `decidir_ajuste` (la clave debe tener líneas del trabajador), y luego `aplicar`;
**B** que `aplicar` acepte una `decision` opcional; **C** dejar «Ajustar»/«Recalcular» solo en el
modal de aprobar (cambia R20 y DA11). Todo lo demás de T8–T18 está hecho y en verde.

**Decisión del humano (2026-10-27), literal: «a»** (a la opción A tal como se le presentó: «Una
llamada nueva, "decidir", con trabajador, periodo y decisión. Tiene las mismas comprobaciones que la
decisión del modal (que ese trabajador tenga líneas en el periodo y que nadie lo haya cambiado
entretanto) y después aplica.»). **Enmienda de la spec hecha (spec-author, 2026-10-27)**: DA28 en
`design.md` §7 (B y C descartadas); R20 enmendado, R45 (`POST /api/franquicia/decidir`, solo
`ajustar`/`recalcular`, 422 formato/decisión/sin líneas del recurso en el periodo, 409 CAS o
transición, sin sv5) y R46 (la vista aplica tras decidir); R16 lista las transiciones de T14; tarea
nueva **T17b** (sv4) sin renumerar. Topes: requirements 150/150, design 248/250. Resumen en
`progress/spec_F-056.md`. F-056 sigue `blocked`: la reanuda el líder (siguiente: T17b y T19–T22).

**DESBLOQUEADA (2026-10-27, líder → implementer).** Decisión del humano, literal: «a» (opción A: ruta
nueva «decidir» y luego aplicar). Tras enseñarle la enmienda (R45, R46, DA28, T17b), literal: «si».
F-056 vuelve a `in_progress`.
- T17b HECHO: `fq._decision` (compartida con `validar_decisiones`), `DECISIONES_VISTA` y
  `fq.decision_vista`; `_plan_franquicia` extraído de `_planes_franquicia` (lo usan modal y vista);
  `POST /api/franquicia/decidir` (503/422/409, sin sv5, `{ok, ajuste}`); `decidir_ajuste` SIN cambios;
  botones «Ajustar»/«Recalcular» en la vista y `decidirDesdeVista` (decidir → aplicar, sin recarga
  nueva: «Actualizar» de siempre). Guardián F-017 a 20 `_actor(request)`. Pendiente: T19–T22 (no
  son del implementer).
- FUERA DEL ALCANCE DE F-056 (2026-10-28; decisión del humano, literal: «a»): la campaña de mutación
  completa (HEAD 6336320) salió NO VÁLIDA porque la línea base de un worker falló en
  `test_f019_bandeja.py::test_f019_r13_otro_contenido_sube_la_version[prueba]`. Es un test de F-019,
  no de F-056, que comparaba dos horas reales (`actualizado_at_utc` > la anterior); bajo carga, los
  dos `_marcar` caían en el mismo tic. Causa confirmada congelando el reloj de `parte_repository`
  (falla `assert '2026-10-28T08:00:00+00:00' > '2026-10-28T08:00:00+00:00'`). Arreglo en el propio
  test: reloj controlado que avanza 1 s por `now()`, sin tocar producción ni debilitar aserciones.
  Se arregla aquí porque bloquea la mutación de F-056. Fichero 20/20 en verde; suite sv4 sin caché
  3175 passed, 1 skipped. Mismo patrón, NO arreglado: `test_f019_portal.py:342`
  (`retirado_at_utc > enviado_at_utc`). Siguiente: el líder relanza la campaña; luego supervivientes.
- MUTACIÓN ANALIZADA (2026-10-29, implementer): campaña válida 3ba3403 (513 mutantes: 403 muertos,
  102 supervivientes y 8 timeouts). De los supervivientes, 88 los mata un test nuevo; los 14 restantes
  son CANDIDATOS a equivalente (#3, 10, 17, 19, 31, 79, 80, 84, 86, 87, 89, 90, 92, 95) y los acepta
  o no el humano. Ninguno de los 8 timeouts cuelga; dos (t1, t3) llevan test nuevo. Commits 138dc9f,
  8f465d3, ca0545b, 7487f85, e3da705 (tests, sin tocar producción) y 9ae3fa5 (informe). Detalle y
  verificación a mano en `progress/mutacion_F-056.md`. La campaña no se relanzó.
- T19 HECHO (2026-10-29): `ARCHITECTURE.md` (semántica 7 a ocho tablas, semántica 21 nueva) y
  `partes-proyecto.md` (§5 a ocho tablas, §5.5 quater, `FRANQUICIA_CAMPO_RES`), en 21bdadf;
  `azure-apps/partes.md` en 58bce5e (commit local, sin push). Siguiente: T20 (el humano decide sobre
  los equivalentes) y T21–T22, que no son del implementer.
- CAMBIO DE ALCANCE EN CURSO (2026-10-29, líder): el campo es extendido (`defext` tip 33 cod '10',
  valores en `conext`), no una columna de `res` (riesgo R-e). La enmienda está pendiente del humano.
  El aviso llegó con los tests de sv5 (ca0545b) y T19 (21bdadf, `azure-apps` 58bce5e) YA commiteados:
  se dejan tal cual, pero describen `res.<campo>` y pueden cambiar con la enmienda.
- **ENMIENDA DE LA SPEC HECHA (spec-author, 2026-10-29): DA29–DA31 = A.** Opciones como las presentó el
  líder: «DA29: Del valor numérico del campo extendido en `conext`, filtrando por recurso y por el tipo 33.
  Si no hay fila, el valor está vacío o vale 0, ese recurso no tiene franquicia. Sigue leyéndolo solo
  sv5.» · «DA30: El ajuste pasa a ser el código del campo extendido (`10`), en vez del nombre de una
  columna. […] Con el ajuste vacío sigue apagada.» (B, por el nombre, descartada) · «DA31: Sigrid guarda
  el valor como entero, así que la franquicia va en horas completas. […]». Humano, literal: «da29,
  recuerda coger el ide del recurso filtrado por empresa, el mismo dni de recurso puede estar en 2
  empresas. lo demas ok». Spec: R47 (solo tip 33; el `cod` `10` de tip 42 nunca), R48 (solo por el
  `res.ide` de la empresa de la obra, nunca por DNI), R1–R3/R38/R39 enmendados, DA29–DA31 en §7, §4 sv5
  reescrito (T23), sv4 solo textos (T24), T25 rehace T19, T26 mutación de lo cambiado. Más de una fila
  por recurso ⇒ `invalida` (recomendación del spec-author; el humano puede pedir otra cosa). Topes
  150/150 y 250/250. Resumen: `progress/spec_F-056.md`. Siguiente: el líder la enseña al humano.
- **ENMIENDA DA32 (spec-author, 2026-10-29)** por la observación 6 del reviewer. Opción presentada:
  «A: arreglarlo ya, eligiendo la obra solo con las líneas del recurso del ajuste. Es un cambio pequeño en
  sv4, con su test y la mutación de esas líneas. […] B: cerrar ya y dejarlo como feature futura.» Humano,
  literal: «sobre la 6, la A». R7 (la obra solo de las líneas del recurso del ajuste) y R5 (el día es de
  la persona) enmendados; DA32 en `design.md` §7; tarea **T27** (sv4: `fq.lineas_del_recurso` y
  `_propuesta`; test del caso del reviewer y mutación) antes de T20–T22. **Abierto para el humano**: el día
  de ajuste NO se recorta al recurso (usa DNI y el `candef` de la primera línea de cualquier recurso de la
  persona; recortarlo podría mover el día en el borde del `candef`): no decidido por el spec-author.
- **APROBADA (2026-10-29, humano, literal):** a DA29–DA31, «da29, recuerda coger el ide del recurso
  filtrado por empresa, el mismo dni de recurso puede estar en 2 empresas. lo demas ok»; tras ver la
  enmienda (R47, R48, `FRANQUICIA_CAMPO_EXT`, T23–T26): «si».
- T23, T24 y T25 HECHAS (implementer, 2026-10-29). T23 (62cc269): sv5 lee el campo extendido:
  `COD_EXT_RE`, `motivo_definicion`, `lectura_de`, `definicion_campo_ext`, `valores_campo_ext` y
  `FRANQUICIA_CAMPO_EXT`; fase RED con traza; tests de R47 y R48; suite de sv5 con 1485 passed.
  T24 (d66d605): textos de sv4 y de la raíz (las dos copias del ORM siguen idénticas) y tests de R48
  en sv4. T25 (d2f6fd6; `azure-apps` e32f089, local y sin push): documentación del campo extendido.
  La lista de ficheros de producción para T26 está en `progress/impl_F-056.md`. Siguiente: T26
  (líder), luego T20–T22.
- **DÍA DE AJUSTE DECIDIDO (2026-10-29, humano):** a la observación 6, «sobre la 6, la A»; al punto
  abierto de DA32 («A (recomiendo): Dejar el día como está: es de la persona, como ya decidimos en
  DA6. Solo cambia la obra.»), literal: «a». `_dia_ajuste` NO cambia.
- T27 HECHA (implementer, 2026-10-29, 17cefc3): `fq.lineas_del_recurso` (pura) y `_propuesta` da a
  `elegir_obra` solo las líneas del recurso del ajuste; `_dia_ajuste`, `varios_recursos` y
  `lineas_trabajador_periodo` sin cambios. Fase RED con traza: el preflight y `decidir` proponían la
  obra 0200 del otro recurso. Ficheros de producción: sv4 `application/services/franquicia.py` e
  `interface_adapters/web/app.py`. Observaciones 1, 2, 4, 5 y 7 de la review en su propio commit;
  `azure-apps` con commit local sin push. Siguiente: la mutación de T27 (líder).

## F-064 · DONE y DESPLEGADA 2026-10-27 en sv4 `ca-sv4-front--r20261027074233` (06:44:16Z, Healthy, sin Traceback ni ERROR) (review APPROVED pasada 2; pendiente: M1 y M2 del humano): el filtro del portal se mantiene durante la sesión de cada usuario

Spec en `specs/F-064-filtro-en-sesion/` (rama `feature/F-064-filtro-en-sesion`, worktree
`partes-wt-f064`, sale de `dev` ec7111d). Rigor estándar. **Solo sv4**: `identidad.py` (clave
pura), `app.py` (global de Jinja), `base.html` (`data-filtros-usuario`), las tres listas
(«Limpiar» ⇒ `?search=`) y `static/app.js` (IIFE `FiltrosSesion` + manejador de días). Sin
esquema, endpoints ni colas; `azure-apps/partes.md` no cambia.

**Aprobación del humano (2026-10-26, literal)**: «ok a f64» ⇒ DA1–DA7 = A (la recomendación de `design.md` §9).

**Corrección al encargo**: «Actualizar» con `VISTA_CLAVE` es de **F-043** (R21, DA10), no de F-022.

**Decididas por el humano** («ok a f64», todas = A; `design.md` §9):
DA1 qué entra (A: columnas de todas las tablas, días, casilla «sin código de hora extra» y
`search`/`pendientes` de las tres listas; sin mes ni modo de los detalles) · DA2 dónde y qué es
«sesión» (A: `localStorage` con clave por usuario —hash del actor de Easy Auth— y caducidad de 8 h
sin actividad; B: `sessionStorage` por pestaña; C: servidor) · DA3 ámbito (A: por pantalla
concreta, cada obra/trabajador los suyos, días además por periodo) · DA4 limpieza (A: «Limpiar»
guarda el vacío, aviso «Filtros recuperados» con «Quitar filtros», caducidad y barrido) · DA5
«Actualizar» de F-043 (A: no se toca, F-064 repone antes) · DA6 selección de líneas (A: nunca se
guarda; con filtro repuesto solo se aprueba lo visible) · DA7 sin identidad desplegado (A: no se
guarda nada).

- [x] **M0 hecha por el líder (2026-10-26, solo lectura)**: `login.cookieExpiration` ⇒ `null` (sin configurar: defecto de Easy Auth, 8 h) ⇒ la caducidad de 8 h de DA2 se queda. Receta original: `az containerapp auth show -n ca-sv4-front -g
  rg-partes-dev --query login.cookieExpiration`; si no es 8 h (o vacío = 8 h por defecto),
  `SESION_MS` toma ese valor. Anotarlo aquí.
- [ ] M1 (local, `design.md` §8) y M2 tras desplegar sv4 (dos usuarios de Entra, mismo navegador).

**Solape con F-061** (`partes-wt-f061`, para la fusión): `static/app.js` (F-061 ≈ l. 1457–1561 y
2753; F-064 ≈ l. 82, 893–990 y 2829–2846), `partes_list.html` (l. 66 frente a l. 34), `app.py`
(rutas frente a junto a `_actor`) y `docs/ARCHITECTURE.md` (semántica 8 frente a punto 11). Trozos
distintos; tras F-061, `_irTrasBorrar` a `/partes` vuelve a la búsqueda guardada (se mira en M1).

**Implementación (implementer, 2026-10-26)** — tarea en curso y decisiones; detalle en
`progress/impl_F-064.md`.
- T1 hecha (b85b574): `tests/test_f064_clave_usuario.py` y `tests/test_f064_filtros_js.py` en
  ROJO (92 fallan por `clave_filtros`/`FiltrosSesion` ausentes; los 6 guardianes de huella de
  R22/R23 pasan a propósito: fijan el texto de `dev`).
- T2 hecha: `clave_filtros` (identidad.py), global `clave_filtros_de` (app.py, tras `_actor`) y
  `<body data-filtros-usuario>`; tests de R1–R3 y los de F-017 en verde sin tocarlos.
- T3 hecha: IIFE global `FiltrosSesion` tras `avisarCambioLineas` con constantes y puras
  (API `puras`); tests puros en verde. Nota: el `init.sh` previo a T1 dio un rojo transitorio en
  sv4 (`clave_filtros_de` indefinido) por editar `base.html` mientras corría; no es del arnés.
- T4 hecha: `_setupDaySelection` devuelve `{claves, disponibles, seleccionar, limpiar}` y
  `wireDayFilters` el de la página o uno nulo. El DOM falso del test gana selectores con
  descendientes (`wireColumnFilters` usa `thead tr.filter-row`).
- T5 hecha: DOM de `FiltrosSesion` (leer/escribir/barrer, foto, guardar, redirigir, restaurar,
  aviso, quitarTodo) y sus líneas en el `DOMContentLoaded` principal.
  **Desviación 1** (justificada): `tests/test_f043_portal_fecha.py::_manejador_principal`
  localizaba el manejador por `{` + «// Toggle del visor de PDF.» pegados; con `redirigir()` como
  1.ª línea (R19) dejaba de encontrarlo. Se cambia SOLO el ancla (busca el `addEventListener`
  que precede al comentario); sus aserciones no cambian. Fuera de la lista de T8.
  **Decisión** (hueco de la spec, lo exige M1.2 «otro mes ⇒ sin días; de vuelta ⇒ días»): la
  foto conserva los días guardados de OTRO periodo si ahora no hay ninguno marcado, y la búsqueda
  guardada si la consulta trae otro parámetro (R19 «ni guarda»).
  `node` se lanza desde un fichero temporal: con `node -e` el programa pasa del límite de Windows.
- T6 hecha: «Limpiar» de las tres listas ⇒ `?search=`; parseo Jinja2 de las tres y de `base.html` OK.
- T7 hecha: `docs/ARCHITECTURE.md` punto 11, párrafo «Filtros por usuario (F-064)».
- T8 hecha: `git diff --stat dev` = la lista de T8 + `tests/test_f043_portal_fecha.py` (desviación 1).
  Nada de sv1/sv2/sv3/sv5, `infra/`, `orm_models.py` ni `azure-apps/`.
- [x] T9 (mutación, lanzada por el líder el 2026-10-26, 4 workers, 1875 s): 4 mutantes, 4 muertos, 0 supervivientes (`progress/mutacion_F-064.md`). Solo alcanza el Python (`identidad.py`); el JS no se muta.
- T10 hecha: `bash harness/init.sh` ⇒ ENTORNO LISTO (sv4 2984 passed; COBERTURA 100 % 7/7).
- Review pasada 1 APPROVED con 6 observaciones; el humano pidió «arregla» para la 1, la 2 y la 4
  (hechas en 6be5c0b, ec7297d y 430274e) y aprobó la automejora del reviewer (dev 755f5f6,
  encargo en `arnes-base` 6eb331d). Review pasada 2: APPROVED (`progress/review_F-064.md`).
- Pendiente: T11/M1 (pasos en `design.md` §8 y resumidos en `impl_F-064.md`) y
  T12/M2 tras desplegar. Informe: `progress/impl_F-064.md`.

## F-061 · DONE y DESPLEGADA 2026-10-27 en sv4 `ca-sv4-front--r20261027074233` (06:44:16Z, Healthy, sin Traceback ni ERROR), junto con F-064 (review APPROVED pasada 2; M2 hecha: 30 borrados; pendiente: M1 del humano): un parte que se queda sin líneas no puede seguir activo

**Dónde está la spec.** La escribió el spec-author el 2026-10-26 en el worktree
`partes-wt-f061`, rama `feature/F-061-parte-vacio-tras-borrar-lineas`, sacada de `dev`
843ff13:
- La versión 1 está en el commit `02da480`. Su `design.md` §9 guarda la consulta M0.
- La versión 2, enmendada, está en `specs/F-061-parte-vacio-tras-borrar-lineas/`. Tiene R1–R20
  (`requirements.md`, 125 líneas), `design.md` (250 líneas) y las tareas T0–T15.

**Alcance.** Toca **solo sv4**. No toca sv3, ni Sigrid, ni el DDL, ni la lista cerrada de
duplicación.

**Decisión del humano (2026-10-26), literal**: «f61 al borrar todas la slineas de un parte se
deb borrar el parte. el parte como entidad no hace falta que vaya a paperlera porque es
confuso. habra una logica que borre el parte en si, al quedarse sin lineas». A las preguntas
del líder eligió «Oculto y luego borrado» y, para los existentes, «Lo mismo que la regla».

**Causa real** (`design.md` §2):
- `soft_delete_registro` no mira si el parte se queda sin líneas vivas.
- `soft_delete_worker` sí lo mira, pero sin bloqueo, y manda el parte a la papelera de
  partes.
- `vaciar_papelera` borra las líneas sueltas sin mirar su parte.
- `restore_document` devuelve activo y vacío un parte que se vació por borrado.
- El borrado en bloque del portal lanza N peticiones a la vez y provoca una carrera.

**Decididas por el humano:**
- **DA1.** El parte que se queda sin líneas vivas se **retira**: `is_active=false`, sin
  `deleted_at_utc` y con la marca `sin-lineas` en `deleted_by`.
  - No sale en `/partes` ni en la papelera de partes, y libera su sha256.
  - Se aplica al borrar líneas, al borrar una persona y al deshacer una celda.
  - Borrar una obra y «Borrar parte» no cambian.
  - Sus líneas siguen en la papelera de líneas (`list_papelera` ya las incluye).
- **DA2.** Restaurar una de esas líneas devuelve el parte.
  - Si ya hay otro parte activo con el mismo sha256, el portal responde 409 sin escribir.
  - `restore_document` sobre un parte sin líneas vivas devuelve también sus líneas.
- **DA3.** Al vaciar la papelera, el parte retirado que no conserva ninguna fila se borra
  **físicamente**; también al «Eliminar» su última fila. Es el único borrado físico nuevo y
  lo decidió el humano.
- **DA4.** Para los existentes, el script `limpiar_partes_vacios.py`, que aplica la regla:
  - Sin argumentos saca un informe de solo lectura.
  - Con `--ejecutar --esperados N`, que lanza el humano, borra los partes sin filas y retira
    los que tienen filas.
  - Excluye los aprobados, los que tienen líneas que viven fuera y los de PT26/00373, 00375 y
    00376.

**Abiertas, que valida el humano** (la recomendación es A en todas):
- **DA5.** `/partes` cuenta solo las líneas vivas y añade la insignia «Sin líneas».
- **DA6.** No se toca la deduplicación de sv3: el parte retirado ya no bloquea. Solo queda el
  parte que **nace** vacío, que se quita con «Borrar parte».
- **DA7.** Marca `sin-lineas` en `deleted_by` en vez de una columna nueva. Así se distingue
  del parte desactivado por el reemplazo de sv3, que deja `deleted_by` en NULL.
- **DA8.** Rigor `estandar`.

**M0 · HECHA por el líder el 2026-10-26**, en solo lectura sobre la base `partes` de
producción:

| Categoría | Partes | Fechas | `approved` | `vive_fuera` | `protegido` |
|---|---|---|---|---|---|
| `sin_filas_leidos` | 29 | 2026-07-15 a 2026-10-22 | f | f | f |
| `sin_filas_nada_leido` | 1 | 2026-07-16 | f | f | f |
| `todas_en_papelera` | 0 | | | | |

`restaurables_que_chocarian` = 0. Según la regla, los 30 se borran.

**Aprobación del humano (2026-10-26, literal)**: «f61 ok» ⇒ DA5–DA8 = A (la recomendación). F-062 ya está `done` y desplegada: F-061 pasa a `in_progress` (rama puesta al día con `git merge dev`).

**Pendiente (ya no).** Que el humano valide DA5–DA8. Después, T1 y siguientes. La limpieza (M2) la
autoriza el humano de forma literal.

**Implementer (2026-10-26).** T1–T13 hechas (un commit por tarea); `init.sh` en verde.
Informe en `progress/impl_F-061.md`. Mutación (lanzada por el líder: 20 evaluados, 16
muertos y 4 supervivientes, con 4 workers):
- #2, #3 y #4 eran huecos y ya los matan tests nuevos.
- #1 (`.limit(1)` → `.limit(2)` en `_borrar_retirados_sin_filas`) es un **equivalente
  aceptado por el humano** (2026-10-26, literal: «acepto»). Demostración:
  `python progress/equivalentes_F-061.py`.

Pendiente: T14 (M1) y T15 (M2).

**Arreglo de la observación 1 de la review, hecho el 2026-10-26** (commit `229c30c`). El humano
dijo «si». Un parte retirado y aprobado ya nunca se borra físicamente: está probado con test,
con su fase RED en `progress/impl_F-061.md`. Además, el humano aceptó el equivalente #1
(«acepto»).

**PUERTA TAMAÑO**: el líder recortó `progress/review_F-061.md` a 139 líneas (`a3dba3c`); tests y
cobertura del 96,9 % en verde. `azure-apps`: commit local `86640b4` (solo `partes.md`).
**Review pasada 2 (2026-10-26): APPROVED** (`progress/review_F-061.md`). Observaciones 2–4 fuera
por decisión del humano.

**M1 · humano, tras desplegar sv4** (`design.md` §9; ningún agente lanza `redeploy_partes.ps1`).
En el portal, parte manual de prueba de la obra 0404, un día sin nada en Sigrid, con dos
líneas, y sin aprobar nada:
1. Borrar una línea ⇒ el parte sigue en `/partes`.
2. Borrar la otra ⇒ aviso «El parte se ha quedado sin líneas y se ha retirado; sus líneas
   siguen en la papelera.» y salto a `/partes`. El parte no sale en `/partes` ni en «Partes
   borrados»; sus dos líneas sí, en «Líneas sueltas borradas».
3. Restaurar una ⇒ el parte vuelve con ella.
4. Borrarla otra vez y «Vaciar papelera». El líder comprueba, en solo lectura sobre la base
   `partes` (nunca a nivel de servidor):
   ```sql
   BEGIN TRANSACTION READ ONLY;
   SELECT count(*) FROM parte_documents WHERE id = '<document_id del parte de prueba>';
   ROLLBACK;
   ```
   ⇒ `0`. Nada registrado en Sigrid; PT26/00373, 00375 y 00376 intactos.

**M2 HECHA (2026-10-27, líder, con autorización literal del humano: «lanza limpieza de partes vacios»)**:
informe 09:43Z ⇒ 30 vacíos, 30 candidatos, 0 excluidos (29 `sin_filas_leidos` + 1
`sin_filas_nada_leido`, igual que la M0); `--ejecutar --esperados 30` a las 09:45Z ⇒ **borrados 30,
retirados 0, saltados 0**; informe repetido a las 09:46Z ⇒ **0** vacíos. Credenciales del Key Vault al
entorno del proceso (sin abrir el `.env`); informes en `services/partes-front/logs/` (ignorado).

**M2 · receta original** (la lanzaba el humano).
Desde `services/partes-front`, con el `.env` de sv4:
1. `../../.venv/Scripts/python.exe limpiar_partes_vacios.py` ⇒ informe en
   `services/partes-front/logs/limpieza_partes_vacios_<AAAAMMDD-HHMM>.md` y `.csv` (solo
   lee; la M0 esperaba 30 `borrar` y 0 excluidos).
2. Leído el informe: `../../.venv/Scripts/python.exe limpiar_partes_vacios.py --ejecutar
   --esperados <N>`, con N = «Candidatos no excluidos» del informe. Si no coincide, sale con
   código 2 sin escribir.
3. Se repite la consulta M0 (`design.md` §9 del commit `02da480`) ⇒ 0 candidatos no
   excluidos. Los agregados, a este fichero.

Desviaciones y decisiones del implementer (justificadas):
- **`tests/test_f017_endpoints_firmados.py` tocado (3 líneas).** R1 cambia la respuesta de
  `POST /api/registro/{id}/delete` y la ruta llama a `borrar_linea` (design §4.3). El test de
  F-017 comparaba la respuesta con `{"ok": True}` exacto y espiaba `soft_delete_registro`. Se
  adapta: comprueba `["ok"] is True` y espía `borrar_linea`. Lo que vigila (que el actor llega
  a `deleted_by`) no cambia. La spec no lo listaba; no hay otra forma de cumplir R1.
- **`partes_borrados` solo aparece si es > 0** (como `EXCLUIDA_REPARTO`). Así el resultado
  de `vaciar_papelera` no cambia cuando no hay retirados que borrar, y
  `test_f010_r11_…` y `test_f019_r16_vaciar_la_papelera_respeta_dedicacion`, que comparan el
  dict exacto, siguen verdes sin tocarlos (verificación de T5).
- **Bloqueos además de los de la spec:** `restore_registro` y `restore_document` también
  bloquean el parte (`_bloquear_documentos`), para que restaurar no se cruce con un borrado de
  la última línea. `_deshacer_creadas` bloquea los partes de las creadas antes de marcarlas.


## F-062 · DONE y DESPLEGADA 2026-10-26 (sv5 r20261026140625 13:07:34Z, sv4 r20261026140755 13:09:17Z; `MOVER_CIZ=true` en los dos; arranque sano; M1–M5 OK; M6 a repetir cuando se aprueben incidencias). El inicio de una incidencia escribe CI* y CIZ el mismo día

Spec en `specs/F-062-ciz-el-mismo-dia-del-inicio/` (rama `feature/F-062-ciz-el-mismo-dia-del-inicio`,
worktree `partes-wt-f062`, sale de `dev` f313407). Rigor crítico. Servicios: **sv5** escribe el
CI* y su CIZ hermano (synckey `partes:<id>:ciz`) en UNA sentencia de dos filas y lo encuentra
para moverlo con la mecánica de F-060; **sv4** marca `ciz_mismo_dia` en el `inicio` y manda su
tramo delante. Sin esquema ni colas nuevas. Sustituye a DA6 de F-060.

**Aprobación del humano (2026-10-25, literal)**: «f62 ok a todo» ⇒ **DA1–DA11 = A**. F-063 ya
está `done`: F-062 pasa a `in_progress` el 2026-10-26 (rama puesta al día con `git merge dev`;
conflictos solo en `BACKLOG.md`, regenerado, `features.json` y este fichero).

**Enmienda tras la aprobación (2026-10-25)**: `MOVER_CIZ` ya está ENCENDIDO en producción (sv5
`ca-sv5-transfer--0000003` 12:08:43Z, sv4 `ca-sv4-front--0000002` 12:09:28Z; `dev` 463869d). Con
DA1 = A, F-062 se activa al desplegarse: sv5 y luego sv4, con M1–M5 hechas ANTES de desplegar
sv4. Comprobado contra R4/R8: sv5 nuevo con sv4 viejo = F-060 (R8, no llega `ciz_mismo_dia`); el
orden inverso también. Quitar solo F-062 = volver sv4 a su revisión anterior y dejar sv5 nuevo;
NO volver sv5 a la imagen de F-060 con hermanos escritos (no lee `:ciz` y el siguiente `fin`
escribiría otro CIZ). Vuelta atrás completa: `MOVER_CIZ=false` en sv4 y luego en sv5
(`design.md` §4). Añadida la lectura del líder de 315 pares CI* + CIZ manuales (`requirements.md`):
el hermano toma `pos` = la del CI* + `PASO_POS` (64) y no imita la `pos` de la pantalla de
Sigrid; su `ide` es el siguiente al del CI* (§5.4). Sin DA nueva.

**Decisiones (aprobadas, todas A)** (`design.md` §12):
DA1 interruptor (A: el mismo `MOVER_CIZ`; encender sv5→sv4, apagar sv4→sv5) · DA2 escritura
(A: una sentencia, dos filas) · DA3 synckey y qué guarda sv4 (A: `partes:<id>:ciz`, sin columna
nueva) · DA4 cómo lo encuentra el día siguiente (A: sv5 deriva la synckey; sin `movida_de`) ·
DA5 inicio con la racha ya escrita delante o con su fin en la misma aprobación (A: sin hermano)
· DA6 rachas abiertas al encender (A: el siguiente fin crea su CIZ, nada retroactivo) · DA7
hermano en parte cerrado (A: `ciz_en_parte_cerrado`; B: cortar la racha como los 12 cortes de
Administración) · DA8 desaprobar/papelera/`borrado_sigrid` (A: nada se mueve) · DA9 recurso sin
CIZ (A: solo CI* + WARNING) · DA10 cuenta del hermano (A: la del CIZ) · DA11 impacto en
F-019/F-024/F-034/F-046/F-053/avisos/modal (aceptar §7).

- [x] **M0 hecha por el líder (2026-10-25, solo lectura)**: (a) `partes:%:%` ⇒ n = 0; (b) rachas abiertas heredadas ⇒ 0 (también 0 desde 20261001). Receta original:: comandos exactos en `design.md` §9;
  si (a) da `n > 0` (alguna synckey `partes:%:%`), PARA y `blocked`.
- [x] **T12 · mutación (lanzada por el líder: 84 mutantes, 9 supervivientes analizados; equivalentes 1, 4 y 5 aceptados por el humano)**: **Aceptación del humano (2026-10-26, literal)**: «acepto» (equivalentes #1 `racha_incidencia.py:262`, #4 `registro_pipeline.py:533` y #5 `registro_pipeline.py:547`; demostración en `progress/equivalentes_F-062.py`). desde la raíz
  del worktree, `python -m harness.mutacion --feature F-062` ⇒ `progress/mutacion_F-062.md`;
  el implementer analiza cada superviviente (test o justificación). Cobertura de líneas
  cambiadas: la da `bash harness/init.sh` (ver `progress/impl_F-062.md`).
- [x] **M1–M5 hechas por el líder el 2026-10-26 (petición literal del humano: «las verificaciones hazlas tu»): M1 OK, M2 OK, M3 OK, M4 OK, M5 OK** (meses 2025/01, 03, 05→06, 08 y 10; cada limpieza solo sobre su parte, `estado` ⇒ NO existe en los seis; `partes:%:ciz` n = 0 antes y después; PT26/00373, 00375 y 00376 idénticos byte a byte). Informe: `progress/m1_m5_F-062.md`. Falta solo la mirada de Administración a la «Vista calendario».
- [x] **M1–M5 · preparación (humano, local; solo escribe en la obra 0404, modo pruebas)**.
  Con F-062 ya fusionada en `dev` y ANTES de desplegar sv4 (`MOVER_CIZ` ya está encendido en
  producción: desplegar sv4 = activar F-062, `design.md` §4). Consolas, lecturas **L**, **S**
  y **V** y recurso 2717792: exactamente las de «M1–M3 · preparación» del bloque de F-060
  (más abajo), con F-062 en el repo principal. Consola 1 (sv5):
  `$env:OBRA_PRUEBAS_FORZAR = 'true'; $env:MOVER_CIZ = 'true'; python main.py`; consola 2:
  `Invoke-RestMethod http://localhost:8005/health` ⇒ `modo_pruebas: True` (**si no, PARA**);
  sv4: `$env:MOVER_CIZ = 'true'; python main.py`. Meses `<M1>`, `<M2>`, `<M3a>` (de 31 días)
  y `<M3b>` (el siguiente), `<M4>`, `<M5>`: los elige el humano, cada uno con `estado` ⇒
  `NO existe parte` de la 0404 y **nunca 2026/06–2026/11** (PT26/00373, 00375 y 00376 se
  conservan). Antes de empezar, con S (sin `reside` ni fechas):
  ```powershell
  $q = @{ database = 'ruesma'; max_rows = 10; parameters = @('partes:%:ciz');
    sql = 'SELECT COUNT(*) AS n FROM hmores WHERE synckey LIKE ?' } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q
  ```
  ⇒ `n = 0` (si no, **PARA**). Y tras crear los partes locales de cada M, con S y los ids
  locales `<id…>` (`parameters = @('partes:<id1>', 'partes:<id2>', …)`, `sql = 'SELECT
  COUNT(*) AS n FROM hmores WHERE synckey IN (?, ?, …)'`) ⇒ `n = 0` (colisión con
  producción, como en F-060: si no, **PARA**).
- [x] **M1 · un día (`<M1>`)**. «+ Nuevo parte»: trabajador 2717792, **V** el día 1; otro con
  **8 h** el día 2. Aprobar el 1 ⇒ V (`verificar`, `<M1>`) ⇒ **CIV y CIZ el 01**; S
  (`<M1>01`–`<M1>31`) ⇒ synckeys `partes:<id1>` y `partes:<id1>:ciz`, `pos` seguidas (la del
  CIZ = la del CIV + 64) e `ide` consecutivos; consola 1: `[registro] ciz mismo dia
  ide=<IZ> hmoide=<P> fecha=<M1>01 registro_id=<id1>`; L ⇒ el 1 `registrado` con
  `sigrid_hmores_ide` = `ide` del CIV. Aprobar el 2 ⇒ HL de 8 h el 02; el CIZ sigue el 01.
  **Limpieza** (V con `<M1>`):
  ```powershell
  python .\prueba_escritura_sigrid.py limpiar
  python .\prueba_escritura_sigrid.py limpiar --ejecutar
  python .\prueba_escritura_sigrid.py estado
  ```
  El DRY-RUN va sobre el ide del parte de `<M1>` (si sale otro, **PARA** y no lances el
  `--ejecutar`); `estado` ⇒ `NO existe parte <AAAA>/<MM> de obra 0404`.
- [x] **M2 · día a día (`<M2>`)**. V los días 1–4 y 8 h el 5; aprobar de uno en uno, V y S
  tras cada uno: 1 ⇒ CIV + CIZ el 01 (anotar el `ide` del CIZ, **IZ**); 2 ⇒ IZ con `fec` 02 y
  synckey `partes:<id2>` (consola 1: `ciz movido ide=<IZ> hmoide=<P>-><P>
  fecha=<M2>01-><M2>02 synckey=partes:<id1>:ciz->partes:<id2>`); 3 y 4 ⇒ IZ al 03 y al 04
  (`registro_id=<id2>-><id3>` y `<id3>-><id4>`); 5 ⇒ HL el 05 y el CIZ sigue el 04. L ⇒ 1
  y 4 `registrado` (el 1 con el `ide` del CIV), 2 y 3 `omitido` `fin_movido`, 5 `registrado`.
  Administración mira la «Vista calendario» de la 0404 (CIV el 1, fin el 4). **Limpieza**:
  los tres comandos de M1 con V en `<M2>`.
- [x] **M3 · cambio de mes (`<M3a>` 31, `<M3b>` 1)**. V el 31 de `<M3a>` y el 1 de `<M3b>`;
  aprobar el 31 ⇒ CIV + CIZ el 31 (S ⇒ IZ y su `hmoide` **Pa**); aprobar el 1 ⇒ IZ con `fec`
  `<M3b>01` y otro `hmoide` (**Pb**, parte nuevo de `<M3b>`); V de `<M3a>` ⇒ solo el CIV del
  31; L ⇒ el 31 sigue `registrado`. **Limpieza**: los tres comandos de M1 con V en `<M3b>` y
  luego en `<M3a>` (cada DRY-RUN sobre el ide de su parte; si no, **PARA**).
- [x] **M4 · todo de una vez (`<M4>`)**. V los días 1–4 ⇒ marcar las cuatro ⇒ «Aprobar
  seleccionadas» ⇒ «Registrar». V ⇒ exactamente CIV el 01 y CIZ el 04; S ⇒ synckey del CIZ
  `partes:<id4>` y **ninguna** `…:ciz`; L ⇒ 2 y 3 `omitido` con `dia intermedio de la
  incidencia: solo se registran el inicio y el fin`. **Limpieza**: los tres comandos con `<M4>`.
- [x] **M5 · desordenado (`<M5>`)**. V los días 1–3; aprobar el **2** ⇒ CIZ el 02 (synckey
  `partes:<id2>`); aprobar el **1** ⇒ solo CIV el 01 (consola 1: `[registro]
  ciz_mismo_dia_omitido registro_id=<id1> motivo=posterior`; el modal puede avisar
  `racha_desordenada`); aprobar el **3** ⇒ el CIZ pasa al 03 (`registro_id=<id2>-><id3>`).
  **Limpieza**: los tres comandos con `<M5>`. Al terminar, Ctrl+C en las consolas 1 y 2 y
  cerrarlas; `git checkout -- prueba_escritura_sigrid.py`.
- [x] **Desplegada por el humano el 2026-10-26**: sv5 `ca-sv5-transfer--r20261026140625` (creada 13:07:34Z) y luego sv4 `ca-sv4-front--r20261026140755` (13:09:17Z), las dos Healthy al 100 %, `MOVER_CIZ=true` leído en las dos. Log Analytics: Uvicorn arriba, sv4 «esquema inicializado (185 sentencias complementarias)», sin Traceback ni ERROR.
- [x] **Despliegue (lo pide el humano)**: **sv5 y luego sv4**, sin tocar variables
  (`MOVER_CIZ` ya está a `true` en los dos). Quitar solo F-062: volver sv4 a su revisión
  anterior y dejar sv5 nuevo; **NO** volver sv5 a la imagen de F-060 con hermanos escritos.
  Vuelta atrás completa: `MOVER_CIZ=false` en sv4 y LUEGO en sv5:
  ```powershell
  az containerapp update -n ca-sv4-front -g rg-partes-dev --set-env-vars MOVER_CIZ=false
  az containerapp update -n ca-sv5-transfer -g rg-partes-dev --set-env-vars MOVER_CIZ=false
  ```
- [ ] **M6 · primera lectura del líder (2026-10-26, solo lectura, recién desplegado)**: M4 de F-060 ⇒ `grupos = 0` (OK); `partes:%:ciz` ⇒ `n = 0` (aún no se ha aprobado ninguna incidencia con sv4 nuevo). Repetir cuando se aprueben incidencias: esperado `n > 0` y `grupos = 0` (script de solo lectura del líder en su scratchpad, `m6_f062.ps1`).
- [ ] **M6 (humano, producción, solo lectura, tras desplegar sv5 → sv4)**. Anotar
  `<AAAAMMDD>` (día del despliegue de sv4). La M4 de F-060 (bloque de F-060, más abajo) ⇒
  `grupos = 0`, y:
  ```powershell
  $q = @{ database = 'ruesma'; max_rows = 10; parameters = @('partes:%:ciz', <AAAAMMDD>);
    sql = 'SELECT COUNT(*) AS n FROM hmores WHERE synckey LIKE ? AND fec >= ?' } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q
  ```
  ⇒ `n > 0` cuando se aprueben incidencias (inicios con su CIZ el mismo día).
- **Implementer (2026-10-26, `partes-wt-f062`)**: terminado (`progress/impl_F-062.md`). Tareas hechas: T1–T8 (sv5 completo), T9–T11 (azure-apps a9d3b5b, local), T13 (comandos de M1–M6 abajo), T14 (`init.sh` verde, cobertura 135/135). T12 (mutación del líder: 84/75/9; 6 huecos cerrados con test en a7e22ed y 3 equivalentes propuestos, pendientes de aceptación del humano: `progress/mutacion_F-062.md`). Review 1 (CHANGES_REQUESTED) corregida: RM5 en `progress/equivalentes_F-062.py` (66ce1a3), `equivalentes_F-060.py` reparado (430412f) y los workers en «Evidencias». Equivalentes 1, 4 y 5 aceptados por el humano («acepto», 2026-10-26). Review pasada 2: APPROVED. Pendientes: M1–M5 (el humano pide el 2026-10-26 que las haga el líder: «las verificaciones hazlas tu»), despliegue y M6. Desviaciones y
  decisiones: se anotan aquí y en `progress/impl_F-062.md`.
## F-063 · DONE y DESPLEGADA 2026-10-26 (sv2 r20261026094916, creada 08:51:31Z, junto con F-058; arranque sano: relectura ACTIVA gemini-4-argon, comprueba_obra=True, timeout 5 s; pendiente M2/M4 de F-058): consulta de obra de sv2 que use el índice

**Aprobación del humano (2026-10-25, literal)**: «f63 ok a todo» ⇒ DA1–DA5 = A (la
recomendación de `design.md` §10). Implementer en marcha en el worktree `partes-wt-f063`.

- [x] T1–T7 y T11 (implementer, 2026-10-26; un commit por tarea, fase RED con traza; informe
  `progress/impl_F-063.md`). `bash harness/init.sh` en verde (cobertura 100 % de 43 líneas).
- [x] **T8 · mutación (lanzada por el líder 2026-10-26; analizada por el implementer)**: 20
  evaluados, 16 muertos, 4 supervivientes en `sigrid_lookup_client.py` (`:70` ×2
  `_RANGO_VARIANTES`, `:86` ×2 `and`→`or`). Análisis en `progress/mutacion_F-063.md`: el de
  `range(161, …)` es equivalente (U+00A0 tiene clave vacía); los otros tres, muertos con
  `test_f063_r5_tabla_de_variantes_solo_del_rango_y_alfanumerica` (comprobado aplicando cada
  mutante a mano, sin relanzar la campaña). 19 de 20 muertos, 1 equivalente.
  **Equivalente aceptado por el humano (2026-10-26, literal)**: «si» (`range(161, 0x0180)`; U+00A0 tiene clave vacía).
- [x] **T9 · M-EQ OK (líder, 2026-10-26, dos pasadas)**: censo 924 obras, 843 claves, 19 con blanco o guion, 663 con ceros a la izquierda, 0 fuera de `[0-9A-Za-z -]`; lotes de 500 con `VALUES`: 924 comprobadas, `fallos=0`, `trampa_vuelve=True`; vieja = nueva en 7 de 7.
- [x] **T10 · M-T aceptada (DA3 enmendada, «a»; registrada en `progress/impl_F-063.md` y `design.md` §10). Antes: M-T NO PASA la puerta DA3 (líder, 2026-10-26)**: 60/60 aciertos, 0 errores, pero mediana 1.163 ms, p95 1.730, máx 4.809 (2.ª pasada: 1.076 / 1.223 / 1.589), candidatos máx 822. Diagnóstico (solo lectura, `httpx` desde local, 8 llamadas por caso): con conexión NUEVA por llamada (lo que hace `_post_sql_read` desde F-058) `SELECT 1` 1.145 ms, obra 692 1.146 ms, obra 0 1.073 ms; con la conexión REUTILIZADA 88 / 92 / 122 ms. El segundo largo es abrir la conexión TLS desde local, no la consulta; dentro de Azure se espera mucho menor, sin medir. `blocked`: decide el humano. **Decisión del humano (2026-10-26, literal)**: «a» ⇒ la puerta DA3 se da por cumplida midiendo solo la consulta (conexión reutilizada: mediana 92 ms, obra 0 122 ms); los tiempos reales se vigilan en producción con la M4 de F-058 tras desplegar; reutilizar la conexión en sv2 (opción B) queda para otra feature si la M4 lo pide. Receta: Script fuera del repo
  (`design.md` §9), probado en seco con dobles:
  `C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-partes\4823be6f-e68f-4ae1-886d-e1c67c71a605\scratchpad\verificar_f063.py`
  (importa del worktree `partes-wt-f063`; solo imprime agregados, ni códigos ni claves). Con el
  `.venv` de la raíz (trae `httpx`) y las credenciales solo en el proceso:
  ```powershell
  $env:SIGRID_API_FUNCTION_KEY = az keyvault secret show --vault-name kv-partes-pt7m3 -n SIGRID-API-FUNCTION-KEY --query value -o tsv
  $env:SIGRID_API_BASE_URL = az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query "properties.template.containers[0].env[?name=='SIGRID_API_BASE_URL'].value | [0]" -o tsv
  $env:SIGRID_API_DATABASE = 'ruesma'
  $script = 'C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-partes\4823be6f-e68f-4ae1-886d-e1c67c71a605\scratchpad\verificar_f063.py'
  python $script meq
  python $script mt
  ```
  `meq`: censo (obras, claves, con blancos o guiones, con ceros, fuera de `[0-9A-Za-z -]` por
  categoría Unicode, con carácter de clave múltiple), lotes de 500 por `ide` con `VALUES` (una a
  una si sigrid-api lo rechaza) ⇒ `fallos=0 trampa_vuelve=True`, y vieja = nueva en 7 de 7 (la
  vieja tarda ~15 s cada una). `mt`: calentamiento + 60 consultas con `ComprobadorObra` (tope
  5 s) ⇒ `aciertos=60 errores=0`, mediana ≤ 500 ms y máximo ≤ 2000 ms (DA3), con p95 y
  candidatos máximos. Cualquier fallo ⇒ `blocked`. Copiar la salida a `progress/impl_F-063.md`.
- [ ] T12 (humano): tras el APPROVED y la fusión, pedir el despliegue de sv2 y seguir con M2/M4
  de F-058.

**Desviaciones respecto a la spec (implementer, justificadas)**:
- `docs/ARCHITECTURE.md`: la consulta de F-058 está en el **punto 20**, no en el 18 que cita la
  spec (el 18 es F-054); se actualizó el 20.
- Tabla de variantes: la base es **cualquier letra o dígito único**, no solo ASCII (`design.md`
  §5.2 decía ASCII). Lo pide R5 al pie de la letra: `µ` (U+00B5) tiene la clave `Μ` griega y
  sin esto un código con `µ` no casaría con su patrón. Las clases de las bases ASCII son las
  mismas; dentro de `[...]` siguen yendo solo letras y dígitos.
- Emulador de `LIKE` de los tests por programación dinámica, no con `re` (§7 decía
  `re.fullmatch`): compilar miles de clases Unicode con `re.IGNORECASE` llevaba el corpus a
  12 s; ahora el fichero entero tarda ~3 s. Misma semántica (CI, AS), con sus propios tests.
- T2: los tests de R9/R12 no pueden correr hasta T3 (el fichero importa `patron_like`); en T2
  se verificó la identidad de `clave_obra`/`es_vacio` a mano y los tests de F-058 en verde.
- `tests/test_f058_obra_sigrid.py`: el docstring de
  `test_f058_r7_existe_obra_pide_el_max_rows_del_cliente` sigue diciendo «el `TOP 1` acota la
  respuesta»; no se toca porque §7 limita el cambio a las aserciones de
  `test_f058_r7_existe_obra_parametrizada`. Lo decide el reviewer.
- `azure-apps`: commit local a5f739e (solo `partes.md`); allí había un `datamart_seg_anual.md`
  modificado ajeno a F-063, sin tocar.

Spec en `specs/F-063-consulta-obra-rapida/` (rama `feature/F-063-consulta-obra-rapida`,
worktree `partes-wt-f063`, sale de `dev` bbc3172). Petición del humano: «1a». Solo sv2 (más
`docs/ARCHITECTURE.md` y `azure-apps/partes.md`). Rigor estándar (solo lecturas; sin motivo
para subirlo). sv2 sigue sin desplegarse hasta cerrar F-063.

- **Estrategia**: `SELECT DISTINCT con.cod FROM obr JOIN con ON obr.ide = con.ide WHERE
  con.cod LIKE ?` con el patrón `%c1%c2%…%cn%` (cada carácter con su clase de variantes:
  minúscula, acentuadas, `ª º ¹ ² ³`; escapes de `% _ [`) y filtro exacto en Python con la
  misma `clave_obra`. Superconjunto garantizado: no se pierden guiones, espacios, ceros ni
  letras. Prototipo del spec-author (fuera del repo): 20.000 códigos aleatorios, cero fallos.
- `es_vacio`/`clave_obra` pasan a `domain/models/clave_obra.py` (sin cambios): puerto,
  `ComprobadorObra`, su log, pipeline, `Settings` y tope de 5 s intactos; de los tests de F-058
  solo cambian dos aserciones del SQL.
- Verificación del líder antes de desplegar (solo lectura, `ruesma`): **M-EQ** exhaustiva
  (cada obra casa con el patrón de su clave, en lotes por `ide`, con par trampa; vieja = nueva
  en ≤ 7 claves) y **M-T** (60 consultas reales: 60/60, 0 errores, puerta DA3).

**Decisiones (aprobadas: A en todas, «f63 ok a todo»)** (`design.md` §10):

| DA | Tema | Recomendación |
|---|---|---|
| DA1 | Estrategia | **A** `LIKE` con `%` entre caracteres + filtro exacto en Python (B `IN` con ceros pierde `06-92`; C `IN` + `LIKE` de respaldo, dos consultas) |
| DA2 | Dónde vive la clave | **A** `clave_obra` al dominio y filtra el cliente (B: el puerto devuelve candidatos; más cambio en F-058) |
| DA3 | Puerta de tiempos M-T | **A** mediana ≤ 0,5 s, máximo ≤ 2 s, 0 errores, 60/60 (B: solo < 5 s) |
| DA4 | Equivalencia M-EQ | **A** exhaustiva por `ide` + 7 claves contra la consulta vieja (B: solo la muestra de M-T) |
| DA5 | `OBRA_EXISTE_TIMEOUT_S` | **A** sigue en 5 s y se revisa con M4 de F-058 (B: bajarlo ya) |

## F-058 · DONE y DESPLEGADA 2026-10-26 (sv2 r20261026094916, 08:51:31Z, con la consulta de obra de F-063; pendiente M2–M4 tras desplegar): relectura de la cabecera con Gemini y prompt de cabecera en sv2

Spec en `specs/F-058-relectura-cabecera-gemini/` (rama `feature/F-058-relectura-cabecera-gemini`,
worktree `partes-wt-f058`), aprobada entera (DA1 enmendada, DA2–DA8 = A, DA9 = A, DA10 = B,
DA11 = A, DA12 = A; «a a todo»). Orden de implementar del humano (2026-10-25): «lazna f58».
Rigor estándar; solo sv2. La rama se puso al día con `git merge dev` (9b1a7e3; conflictos solo
en `BACKLOG.md`, regenerado, y en este fichero). Informe: `progress/impl_F-058.md`.

- [x] T1, T2 (prompt), T4–T15 (código, tests, docs; azure-apps commit local 7470cf2, sin push)
  y T22 (`bash harness/init.sh` en verde). Un commit por tarea, fase RED con traza.
- [x] T16 (mutación lanzada por el líder: 20 de 63, 1 superviviente `settings.py:100`
  `gt=0`→`gt=1`, muerto con un test nuevo de 0.5 y 1; ver `progress/mutacion_F-058.md`).
- [x] T3 (MB, líder: sin regresión, `progress/banco_F-058.md`). Quedan T17–T21 (MANUAL, abajo).
- Aviso: `dev` avanzó a 776f923 después del merge (solo `progress/`, `BACKLOG.md` y
  `features.json`; entre ello «F-059: M4 OK, 6 partes reprocesados, obra y fecha leídas»).

**Encaje con F-038 y F-059 (llegaron a `dev` después de escribir la spec; decisiones del
implementer, justificadas)**:
- `existe_obra` NO pasa `max_rows=2` (`design.md` §4.3): F-038 (R13, guardián
  `tests/test_f038_lectores_sigrid.py`) prohíbe en todo lector un `max_rows` literal bajo el
  tope, y `docs/ARCHITECTURE.md` fija que toda lectura pide `SIGRID_API_MAX_ROWS`. La consulta
  es `SELECT TOP 1`, así que el `max_rows` no cambia el resultado: se pide el del cliente.
- Sin parámetro `exigir_completo`: desde F-038 `_post_sql_read` ya trata `truncated: true` como
  error en TODA lectura (incluido `fetch_tipos_hora`), que es lo que R9 pide para la de obra.
- `OBRA_EXISTE_TIMEOUT_S` es independiente de `SIGRID_API_TIMEOUT_S` (rango (0, 200] de
  F-038): se pasa por llamada solo a `existe_obra`; el catálogo auxhor sigue con el suyo.
- F-059 (página como imagen): la relectura aplica la MISMA regla por proveedor que la primaria
  (`PAGINA_COMO_IMAGEN_PROVEEDORES`): con la configuración de hoy (`openai`) Gemini recibe el
  PDF original, que es con lo que se midió el 6 de 6 de la spec. `meta.adjunto_ia` sigue siendo
  de la primaria (R16 fija las claves de `meta.relectura_cabecera`); lo enviado en la relectura
  queda en `debug.relectura_cabecera` (`<proveedor>_request.attachment`).
- El punto de `docs/ARCHITECTURE.md` es el **20** (el 18 es F-054 y el 19, F-059).
- Otras menores: `model_name` del proveedor de relectura que no está instanciado (`KeyError`)
  cuenta como fallo de la relectura (R14: `error`, `model` null), no tumba; `consulta_obra_ms`
  solo apunta las consultas hechas (una obra con clave vacía, p. ej. `" - "`, no consulta).

**MANUAL pendiente (comandos exactos; ninguna escribe en Sigrid ni en `partes`)**:
- [x] **T3 · MB hecha (2026-10-25)**: (a) 12/12, (b) 4/4, (c) 6/6, (d) 42/42 sin errores; detalle en `progress/banco_F-058.md`. Receta: (líder, banco del prompt sobre el commit c67c253): el `lanzar.ps1` del banco
  del líder con `-Repo C:\Users\pgris\PycharmProjects\partes-wt-f058`, sin relectura:
  (a) `-Paginas paginas_sincab -Runs 2 openai:gpt-6.1-sol` ⇒ cuántas de 12 traen obra y fecha
  (antes 0; no es puerta); (b) `-Paginas paginas_control openai:gpt-6.1-sol` ⇒ como
  `control.jsonl`; (c) `-Paginas paginas_sincab gemini:gemini-4-argon` ⇒ 6 de 6; (d) batería de
  F-051 (3 pasadas, `corregir.py`) ⇒ 42 de 42. Si (b), (c) o (d) empeoran: `blocked`, decide el
  humano (DA9). Resultado en `progress/banco_F-058.md`.
- [x] **T16 · mutación** (líder): `python -m harness.mutacion --feature F-058`; análisis del
  único superviviente hecho en `progress/mutacion_F-058.md` y en el informe.
- [x] **T17 · M0 OK (líder, 2026-10-25)**: `ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon`, claves por `secretRef`, `SIGRID_API_DATABASE=ruesma`. Receta:
  ```powershell
  az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query "properties.template.containers[0].env[?starts_with(name,'GEMINI_') || starts_with(name,'ENABLE_GEMINI') || starts_with(name,'SIGRID_API_')]" -o table
  ```
  ⇒ `ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon`, `GEMINI_API_KEY` y
  `SIGRID_API_FUNCTION_KEY` por `secretRef`, `SIGRID_API_DATABASE=ruesma`. Si falta algo, decide
  el humano.
- [ ] **T18 · M1 FALLA (líder, 2026-10-25)**: obra y fecha True en las 8 páginas (6 sincab + 2 control, sin relectura: ya lo resuelve el prompt), filas iguales, pero las 8 `[obra-sigrid]` salen `resultado=error error=ReadTimeout` (5,6–6,2 s con tope 5 s). Medido aparte en sigrid-api (solo lectura): `_SQL_EXISTE_OBRA` tarda 12–16 s (sigrid-api SÍ acepta `CROSS APPLY`/`COLLATE`); `SELECT 1` 79 ms; `con.cod IN (variantes con ceros)` 110–124 ms; `con.cod LIKE '%692'` 101 ms; `OPTION (FORCE ORDER)` no lo arregla (13 s). Desplegar así: toda consulta de obra = «no se sabe», ~6 s más por parte y ~13 s de consulta en el SQL de Sigrid por parte. **No desplegar sv2 hasta que decida el humano.** Receta original: Entorno con los SDK de IA
  (el `.venv` de la raíz no los trae), las claves del KV solo en el proceso:
  ```powershell
  python -m venv $env:TEMP\venv-sv2-f058
  & $env:TEMP\venv-sv2-f058\Scripts\pip install -r C:\Users\pgris\PycharmProjects\partes-wt-f058\infra\manifests\sv2\requirements.txt
  cd C:\Users\pgris\PycharmProjects\partes-wt-f058\services\partes-api
  $env:IA_PROVIDER = 'openai'; $env:ENABLE_OPENAI = 'true'; $env:OPENAI_MODEL = 'gpt-6.1-sol'; $env:OPENAI_TIMEOUT_S = '180'
  $env:ENABLE_GEMINI = 'true'; $env:GEMINI_MODEL = 'gemini-4-argon'; $env:ENABLE_CLAUDE = 'false'
  $env:OPENAI_API_KEY = az keyvault secret show --vault-name kv-partes-pt7m3 -n OPENAI-API-KEY --query value -o tsv
  $env:GEMINI_API_KEY = az keyvault secret show --vault-name kv-partes-pt7m3 -n GEMINI-API-KEY --query value -o tsv
  $env:SIGRID_API_FUNCTION_KEY = az keyvault secret show --vault-name kv-partes-pt7m3 -n SIGRID-API-FUNCTION-KEY --query value -o tsv
  $env:SIGRID_API_BASE_URL = az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query "properties.template.containers[0].env[?name=='SIGRID_API_BASE_URL'].value | [0]" -o tsv
  $env:SIGRID_API_DATABASE = 'ruesma'
  @'
  import logging, sys, time
  from pathlib import Path
  from application.pipelines.extract_parte_pipeline import ExtractParteRequest
  from config.settings import Settings
  from interface_adapters.api.app import build_app
  logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
  for n in ("application.services.obra_sigrid", "application.pipelines.extract_parte_pipeline", "interface_adapters.api.app"):
      logging.getLogger(n).setLevel(logging.INFO)
  pipeline = build_app(Settings(_env_file=None)).state.pipeline
  for carpeta in sys.argv[1:]:
      for pdf in sorted(Path(carpeta).glob("*.pdf")):
          t0 = time.perf_counter()
          s = pipeline.run(ExtractParteRequest(filename=pdf.name, mime_type="application/pdf", file_bytes=pdf.read_bytes(), document_id=pdf.stem))
          r, c = s["meta"].get("relectura_cabecera") or {}, s["data"]["cabecera"]
          print("RESUMEN", Path(carpeta).name, pdf.stem, "motivo=%s resultado=%s obra=%s fecha=%s filas=%d ms=%s s=%.1f" % (r.get("motivo", "-"), r.get("resultado", "-"), bool(c.get("obra_numero")), bool(c.get("fecha")), len(s["data"]["empleados"]), r.get("consulta_obra_ms", "-"), time.perf_counter() - t0))
  '@ | & $env:TEMP\venv-sv2-f058\Scripts\python - <CARPETA_paginas_sincab> <CARPETA_paginas_control>
  ```
  ⇒ las 6 de `paginas_sincab` con `obra=True fecha=True` (por relectura o ya por el prompt),
  `filas` iguales a las de la primaria, `paginas_control` sin `motivo` (sin relectura), ninguna
  línea `[obra-sigrid] ... resultado=error`; los `ms=` de esas líneas son los primeros tiempos
  (anotarlos en `progress/impl_F-058.md`). Los nombres de fichero del banco no deben llevar
  nombres ni DNIs (se imprimen).
- [ ] **T19 · M2** (humano, tras desplegar sv2; solo lectura en la base `partes` de Azure, con
  el cliente PostgreSQL habitual; `<FECHA_DESPLIEGUE>` = AAAA-MM-DD HH:MM UTC):
  ```sql
  BEGIN TRANSACTION READ ONLY;
  SELECT j->>'motivo' AS motivo, j->>'resultado' AS resultado, count(*)
  FROM (SELECT raw_extraction_json::jsonb->'meta'->'relectura_cabecera' AS j
        FROM parte_documents WHERE created_at_utc >= '<FECHA_DESPLIEGUE>') s
  GROUP BY 1, 2 ORDER BY 1, 2;
  ROLLBACK;
  ```
  ⇒ la fila `NULL, NULL` son los que no releyeron; el resto, por motivo y resultado.
- [ ] **T20 · M4** (humano o líder, tras desplegar; tiempos de la consulta de obra):
  ```powershell
  $WS = az containerapp env show -n cae-partes-dev -g rg-partes-dev --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
  az monitor log-analytics query -w $WS --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv2-extraccion' and Log_s has '[obra-sigrid]' | extend ms = toint(extract('ms=([0-9]+)', 1, Log_s)), res = extract('resultado=([a-z_]+)', 1, Log_s) | summarize n=count(), p50=percentile(ms,50), p95=percentile(ms,95), max_ms=max(ms) by bin(TimeGenerated, 1d), res" -o table
  az monitor log-analytics query -w $WS --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv2-extraccion' and Log_s has '[sv2][relectura]' and Log_s has 'resultado=' | extend res = extract('resultado=([a-z_]+)', 1, Log_s), motivo = extract('motivo=([a-z_]+)', 1, Log_s) | summarize n=count() by bin(TimeGenerated, 1d), motivo, res" -o table
  ```
  ⇒ consultas, mediana, p95, máximo y `error` por día, y relecturas por motivo y resultado; con
  eso el humano cierra DA12 (tope de 5 s).
- [ ] **T21 · M3** (humano, DA8 = A): los 6 documentos ya guardados sin obra ni fecha se corrigen
  a mano en el portal (ningún agente escribe). Según `dev` 0833170, F-059 M4 ya los reprocesó con
  obra y fecha: comprobar si queda alguno.

## F-060 · DONE y DESPLEGADA 2026-10-25 (sv5 r20261025093550, sv4 r20261025093906; `MOVER_CIZ` sin definir en los dos = apagado; arranque sano en Log Analytics, sin Traceback). Antes de encender: visto bueno de Administración a DA3 y DA6 y M1–M3. Racha de incidencia con CIZ móvil

Spec en `specs/F-060-racha-incidencia-ciz-movil/` (rama `feature/F-060-racha-incidencia-ciz-movil`,
worktree `partes-wt-f060`). Rigor crítico. Servicios: sv4 decide el rol con el histórico de
`partes` y manda `racha_registro_ids`; sv5 busca el CIZ de la racha por synckey y lo mueve con
un `UPDATE` (nunca `DELETE`), con `MOVER_CIZ` apagado por defecto. Sin esquema.

**Aprobación del humano (2026-10-23, literal)**: «a en todo, lanza implementer y spec de la
sigueinte feature» ⇒ DA1–DA11 = A. DA3 y DA6 siguen pendientes del visto bueno de
Administración para ENCENDER `MOVER_CIZ` (no para implementar). M0 hecha por el líder (2 CIZ
de partes en 2026/10, 0 enlazados, 0 recursos-mes con más de uno).

**Review pasada 1: CHANGES_REQUESTED** (`progress/review_F-060.md`). El líder llevó al humano
la divergencia de R26 (con `MOVER_CIZ` apagado, sv4 ya usaba la regla nueva: aprobando día a
día con días posteriores ya ingeridos salían más CIZ que en dev 0926857) con las opciones A
(aceptarla), B (sv4 vuelve a mirar adelante) y C (el mismo `MOVER_CIZ` gobierna sv4: apagado,
el `_rol_incidencia` de dev 0926857 tal cual, sin `racha_registro_ids` ni `avisos_racha`; se
enciende en los dos), y la propuesta de que la papelera de los días saltados del tramo de la
racha viaje en `racha_registro_ids`.
**Decisión del humano (2026-10-24, literal)**: «c y si a 2» ⇒ **DA12 = C** y **DA13 = sí**.
Spec enmendada por el spec-author (R9, R26, R26 bis, R28–R30 siempre, R31, R32; `design.md`
§3.1, §4, §8–§12; `tasks.md` T16–T24). Orden: encender `MOVER_CIZ` en sv5 y luego en sv4;
apagar en sv4 y luego en sv5 (apagar los dos = vuelta atrás completa; lo ya movido no se
deshace). T23 (campaña de mutación de nuevo, el código de producción cambia tras la de T13)
la lanza el líder: decidir con el humano su coste (la de T13 fueron ~377 min con 4 workers).

- [x] T1–T7 (sv5) hechas, un commit por tarea, fase RED con traza (se pegan en `impl_F-060.md`).
- [x] T8–T11 (sv4) y T12 (docs; azure-apps commit local c914caa, sin push) hechas.
- [x] T15: `bash harness/init.sh` en verde (resultado en `impl_F-060.md`).
- [x] T13: campaña de mutación lanzada por el líder (4 workers, 16 supervivientes, 1 timeout)
  y analizada por el implementer sin relanzarla: 10 muertos con test nuevo (verificados a
  mano), 6 equivalentes aceptados por el humano (2026-10-24, «acepto»), timeout detectado.
  Detalle en `progress/mutacion_F-060.md`; demostraciones en `progress/equivalentes_F-060.py`.
- [x] **Enmienda (implementer, 2026-10-24)**: T16 (`MOVER_CIZ` en sv4; apagado = rol de dev
  0926857 tal cual), T17 (DA13), T18 (sv5 extremo a extremo de R26), T19 (docs; azure-apps
  commit local 44886eb, sin push), T20–T22 (papeleo) y T24 (`init.sh` en verde). Detalle en
  `progress/impl_F-060.md`. **Pendiente**: T23 (líder) y T14 (humano, abajo).
- [ ] T14: M1–M3 (humano, local, modo pruebas) y M4 (abajo, con comando exacto).

**Decisiones y desviaciones (justificadas)**:
- `decidir_fin` recibe `partes: Mapping[int, ParteSigrid]` (código y estado) y
  `nombre_estado` en vez de `estados: Mapping[int, int|None]`: el motivo de R17 tiene que
  nombrar el código y el estado del parte, y el de R18 (F-053) el código. Un parte que no se
  pudo leer cuenta como cerrado (no se escribe a ciegas).
- Un CIZ de la racha con fecha = D no es anterior ni posterior: `crear`, y el paso 7 lo
  omite como `incidencia_en_sigrid` (no puede llegar: R9 excluye el día D).
- `LineaSigrid.tex/pos` entraron en el commit de T1 (los necesita la regla pura de R19).
- R23 en carrera por el parte de ORIGEN cerrado: la relectura de F-034 solo lee los partes
  del periodo de D, así que sale `no_escrita` (con su ERROR) y no `parte_no_abierto`.
  Aceptado: «sale omitida con los motivos de F-034 y nada más cambia».
- T8: `colapsar` recibe `LineaRol` (con `racha_registro_ids`) en vez de una tupla de 5: dos
  `fin` son de la misma racha si son del mismo día o uno está en la racha del otro (R7);
  con solo persona y clave, dos rachas distintas de la misma letra en una aprobación se
  colapsarían en una.
- T8: una línea de la papelera solo entra en `racha_registro_ids` si es incidencia de la
  MISMA clave y está `registrado` o `encolado` (su synckey puede seguir en Sigrid).
- T9: `GrupoObra` gana el campo `avisos_racha` en T9 (no en T10): sin él,
  `GrupoObra(**g)` revienta en cuanto el grupo lleva la clave.
- T10: el CAS de `fin_movido` exige `sigrid_estado = 'registrado'` y el mismo
  `sigrid_hmores_ide`; sin CAS, silencio si X ya está `omitido` con ese mismo motivo
  (reentrega) y WARNING `fin_movido_sin_cas` (sin datos personales) en otro caso, también
  si X no existe. `movida_de` igual a D no hace nada.
- T11: estilo `.ap-racha-avisos` en `static/styles.css` (el mismo que `.ap-incid-avisos`).
- T16: apagado, sv4 calcula el rol con `_rol_incidencia_anterior` DESPUÉS del bucle de las
  líneas (dev 0926857 lo hacía dentro): mismas consultas, sin escrituras entre medias, mismo
  resultado. La copia se comprobó con `diff` contra `git show 0926857` (solo nombre y una
  línea del docstring).

- [x] **M1–M3 hechas el 2026-10-25: M1 OK, M2 OK, M3 OK** (meses 2026/01, 2026/03→04 y 2026/12; limpiado con `estado` ⇒ NO existe; PT26/00373, 00375 y 00376 intactos). Informe: `progress/m1_m3_F-060.md`. Falta solo la mirada de Administración a la «Vista calendario».
- [x] **M1–M3 · preparación (humano, local; solo escribe en la obra 0404, modo pruebas)**.
  Desde el repo principal con F-060 en `dev` (los `.env` locales viven ahí, no en el
  worktree). El sv4 local usa el PostgreSQL LOCAL (`PG_HOST` local) y llama al sv5 local
  (`TRANSFER_BASE_URL` a `127.0.0.1:8005`), sin colas. Recurso: el gruista de pruebas
  2717792 de `prueba_escritura_sigrid.py`. Meses (los elige el humano): `<M1>`, `<M3>` y dos
  seguidos `<M2a>` (de 31 días) y `<M2b>`. Ninguno 10/2026 (PT26/00373 guarda las líneas
  `PRUEBA-IA` de F-046 que el humano decidió conservar; `limpiar` las borraría); cada uno
  sin parte de la 0404 (`estado` ⇒ `NO existe parte`) y sin líneas locales del 2717792 en
  ese mes ni en el anterior (lectura L ⇒ nada; la ventana de F-060 las vería).
  Consola 1, sv5:
  ```powershell
  cd C:\Users\pgris\PycharmProjects\partes\services\partes-transfer
  ..\..\.venv\Scripts\Activate.ps1
  $env:OBRA_PRUEBAS_FORZAR = 'true'; $env:MOVER_CIZ = 'true'; python main.py
  ```
  Consola 2: `Invoke-RestMethod http://localhost:8005/health` ⇒ `modo_pruebas: True`,
  `obra_pruebas: 0404`, `database: ruesma` (**si `modo_pruebas` no es `True`, PARA**). sv4:
  ```powershell
  cd C:\Users\pgris\PycharmProjects\partes\services\partes-front
  ..\..\.venv\Scripts\Activate.ps1
  $env:MOVER_CIZ = 'true'; python main.py
  ```
  Portal en `http://127.0.0.1:8014` (Ctrl+F5). Consola 3 (`.venv` activado), lecturas:
  **L** (base `partes` LOCAL), desde `services\partes-front`, con `<DESDE>`/`<HASTA>` AAAAMMDD:
  ```powershell
  @'
  from sqlalchemy import create_engine, text
  from config.settings import Settings
  with create_engine(Settings().database_url).connect() as c:
      for f in c.execute(text("SELECT id, fecha_int, incidencia_codigo, horas, sigrid_estado, sigrid_hmores_ide, sigrid_motivo FROM parte_registros WHERE (recurso_ide = 2717792 OR empleado_reside = 2717792) AND fecha_int BETWEEN :d AND :h AND deleted_at_utc IS NULL ORDER BY fecha_int, id"), {"d": <DESDE>, "h": <HASTA>}):
          print(tuple(f))
  '@ | python -
  ```
  **S** (Sigrid, `ruesma`, solo lectura; `$env:SIGRID_API_BASE_URL` y `$KEY` como en M4):
  ```powershell
  $q = @{ database = 'ruesma'; max_rows = 50; parameters = @(2717792, <DESDE>, <HASTA>);
    sql = "SELECT h.ide, h.hmoide, h.fec, a.cod AS hora, h.can, h.pos, h.synckey FROM hmores h JOIN auxhor a ON a.ide = h.horide WHERE h.reside = ? AND h.fec BETWEEN ? AND ? AND h.synckey LIKE 'partes:%' ORDER BY h.fec, h.ide" } | ConvertTo-Json
  (Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q).rows | ConvertTo-Json -Compress
  ```
  **V** (`verificar`/`estado`/`limpiar`): en `services\partes-transfer\prueba_escritura_sigrid.py`,
  `ANO, MES = <AAAA>, <MM>` (cambio local, no se commitea) y
  `python .\prueba_escritura_sigrid.py verificar` (o `estado`).
- [x] **M1 · día a día (`<M1>`)**. En «+ Nuevo parte» (`/nuevo`): una obra cualquiera (sv5
  en pruebas escribe en la 0404), trabajador 2717792, incidencia **V**, días 1, 2, 3 y 4 ⇒
  «Crear parte»; otro con **8 h** ordinarias el día 5. En la vista del trabajador, «Aprobar»
  la línea del día 1 ⇒ «Registrar»; luego la del 2, la del 3, la del 4 y la del 5, de una en
  una. Tras cada una, V (`verificar`, ANO/MES de `<M1>`) y S (`<M1>01`–`<M1>31`):
  - día 1 ⇒ 1 línea: CIV el 01, `can` 0.
  - día 2 ⇒ CIV el 01 y **CIZ el 02**; anotar con S su `ide` (**IZ**) y su `pos`.
  - día 3 ⇒ 2 líneas: CIV el 01 y CIZ el **03** con el MISMO `pos`; S ⇒ IZ con `fec` 03 y
    `synckey` `partes:<id del día 3>`; consola 1: `[registro] ciz movido ide=<IZ>
    hmoide=<P>-><P> fecha=<M1>02-><M1>03 registro_id=<id 2>-><id 3>`.
  - día 4 ⇒ igual con el **04** (IZ, `registro_id=<id 3>-><id 4>`).
  - día 5 ⇒ 3 líneas: CIV el 01, CIZ (IZ) el 04 y HLGR de 8 h el 05: el CIZ no se mueve.
  L (`<M1>01`–`<M1>31`) ⇒ días 1, 4 y 5 `registrado` (el 4 con `sigrid_hmores_ide` = IZ); 2
  y 3 `omitido` con `fin_movido: el fin de la incidencia (CIZ, linea <IZ>) paso al dia
  <AAAA-MM>-03` (y `-04`). Administración mira la «Vista calendario» de la 0404 (CIV el 1,
  fin el 4). **Limpieza** (V con `<M1>`):
  ```powershell
  python .\prueba_escritura_sigrid.py limpiar
  python .\prueba_escritura_sigrid.py limpiar --ejecutar
  python .\prueba_escritura_sigrid.py estado
  ```
  El DRY-RUN imprime los `DELETE` sobre el ide del parte de `<M1>` (si sale otro, **PARA** y
  no lances el `--ejecutar`); `estado` ⇒ `NO existe parte <AAAA>/<MM> de obra 0404`.
- [x] **M2 · cambio de mes (`<M2a>` 30 y 31, `<M2b>` 1)**. «+ Nuevo parte» con V los días 30
  y 31 de `<M2a>` y 1 de `<M2b>`; aprobar el 30, luego el 31 y luego el 1. Esperado: tras el
  31, V de `<M2a>` ⇒ CIV el 30 y CIZ el 31 (S ⇒ su `ide` IZ y su `hmoide` **Pa**); tras el 1,
  V de `<M2a>` ⇒ solo el CIV del 30; V de `<M2b>` ⇒ un parte nuevo con el CIZ el 01; S
  (`<M2a>30`–`<M2b>01`) ⇒ el MISMO IZ con `fec` `<M2b>01` y otro `hmoide` (**Pb**); consola 1:
  `ciz movido ide=<IZ> hmoide=<Pa>-><Pb> fecha=<M2a>31-><M2b>01`. L ⇒ el 31 `omitido`
  `fin_movido`. **Limpieza**: los tres comandos de M1 con V en `<M2b>` y después en `<M2a>`
  (cada DRY-RUN, sobre el ide de su parte; si no, **PARA**); `estado` ⇒ `NO existe` en los dos.
- [x] **M3 · todo de una vez (`<M3>`)**. «+ Nuevo parte» con V los días 1–4; en la vista del
  trabajador, marcar las cuatro líneas ⇒ «Aprobar seleccionadas» ⇒ «Registrar». Esperado: V
  de `<M3>` ⇒ CIV el 01 y CIZ el 04 (2 líneas); L ⇒ 1 y 4 `registrado`; 2 y 3 `omitido` con
  `dia intermedio de la incidencia: solo se registran el inicio y el fin`; consola 1 sin
  `ciz movido`. **Limpieza**: los tres comandos de M1 con V en `<M3>`. Al terminar, Ctrl+C
  en las consolas 1 y 2 y cerrarlas (llevan `OBRA_PRUEBAS_FORZAR` y `MOVER_CIZ`); deshacer
  el cambio de `ANO, MES` con `git checkout -- prueba_escritura_sigrid.py`.

- [ ] **M4 (humano, producción, solo lectura, tras desplegar sv5 → sv4 y encender)**.
  Encendido (lo lanza el humano, con el visto bueno de Administración a DA3/DA6), **primero
  sv5 y LUEGO sv4**:
  ```powershell
  az containerapp update -n ca-sv5-transfer -g rg-partes-dev --set-env-vars MOVER_CIZ=true
  az containerapp update -n ca-sv4-front -g rg-partes-dev --set-env-vars MOVER_CIZ=true
  ```
  Anotar `<AAAAMMDD>` (día del encendido) y `<ISO UTC>` (instante). Con `$KEY` sacada del
  Key Vault (nunca en un fichero):
  ```powershell
  $q = @{ database = 'ruesma'; max_rows = 200; parameters = @('CIZ', 'partes:%', <AAAAMMDD>);
    sql = 'SELECT COUNT(*) AS grupos FROM (SELECT h.reside, h.ano, h.mes FROM hmores h JOIN auxhor a ON a.ide = h.horide WHERE a.cod = ? AND h.synckey LIKE ? AND h.fec >= ? GROUP BY h.reside, h.ano, h.mes HAVING COUNT(*) > 1) x' } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q
  ```
  Esperado: `grupos = 0` (ningún recurso-mes nuevo con dos CIZ de partes). En la base `partes`:
  ```sql
  SELECT COUNT(*) FROM parte_registros
  WHERE sigrid_motivo LIKE 'fin_movido:%' AND sigrid_registrado_at_utc >= '<ISO UTC>';
  ```
  Esperado: > 0 cuando se hayan aprobado rachas de varios días. **Vuelta atrás completa**
  (para lo que se apruebe desde entonces; lo ya movido no se deshace), **primero sv4 y LUEGO
  sv5** (apagar solo sv5 deja sv4 con la regla nueva: un CIZ por día aprobado de la racha):
  ```powershell
  az containerapp update -n ca-sv4-front -g rg-partes-dev --set-env-vars MOVER_CIZ=false
  az containerapp update -n ca-sv5-transfer -g rg-partes-dev --set-env-vars MOVER_CIZ=false
  ```
## F-038 · DONE y DESPLEGADA 2026-10-24 (sv2–sv5, revisión r20261024215445). M2 OK: `[sigrid-lookup] Instanciado … timeout_s=30.0 max_rows=500000` (sv4) y `[sigrid-write] Instanciado … timeout_s=60.0 max_rows=500000` (sv5), leído en Log Analytics. Pendiente solo M1 (no bloquea): límite de filas de Sigrid a 500.000 y `truncated` siempre error

**Aprobación del humano (2026-10-24, literal)**: «sigrid lee 500k, hay que cambiar donde este ese
limite de 100 ya mismo. se supone que estaba arreglado» y «si» a la propuesta del líder ⇒ DA1 = B
(500.000), DA2–DA7 = A. En paralelo con F-060 (excepción expresa a «una feature en curso»).

- **Hecho (implementer, 2026-10-24)**: T1–T8, un commit por tarea, fase RED con trazas. sv2–sv5
  piden `SIGRID_API_MAX_ROWS` (opcional, 500.000, 1–500.000) en toda lectura no paginada; sv5 ya no
  pide 1.000 fijo (lo urgente: `lineas_existentes`, `horas_de_recursos`, `recursos_por_dni`).
  `truncated` es error también en sv2 (el catálogo cae a caché/vacío) y en
  `prueba_escritura_sigrid.py`. `SIGRID_API_TIMEOUT_S` en (0, 200] en los cuatro. Guardián de raíz
  `tests/test_f038_lectores_sigrid.py`. Borrado `consulta_reshor_recursos.py` (DA6; el historial
  NO se purga). Informe: `progress/impl_F-038.md`. azure-apps: commit local c581115 (sin push).
- **Decisión anotada**: el umbral de R13 (guardián) es 500.000, no el 200.000 escrito en la spec:
  con DA1 = B un literal menor sería un límite por debajo del acordado.
- **T9 hecha**: campaña del líder (26 generados, 20 evaluados, 3 supervivientes, que mueren con el
  test del límite inferior del timeout añadido); detalle en `progress/mutacion_F-038.md`.
- **Review pasada 1**: CHANGES_REQUESTED solo por papeleo (este bloque, T9/T12, workers).
- **Pendiente**: review pasada 2, merge a `dev`, despliegue sv2–sv5 (humano), M2 (humano).
- [x] **M0 hecha por el líder (2026-10-24, solo lectura)**: `SIGRID_API_TIMEOUT_S` = 30 en sv4 y 60 en sv5; sv2 y sv3 sin la variable (defecto 30); `SIGRID_API_MAX_ROWS` en ninguna. Todo dentro de (0, 200]: el despliegue no se cae por DA4.
- [ ] **M2 · T11 (humano, tras desplegar sv2–sv5 con `.\infra\redeploy_partes.ps1`; solo lectura)**:

  ```
  az containerapp logs show -n ca-sv5-transfer -g rg-partes-dev --tail 80
  az containerapp logs show -n ca-sv4-front -g rg-partes-dev --tail 80
  ```
  Esperado: en la línea `Instanciado` del cliente de Sigrid, `max_rows=500000` en las dos, con
  `timeout_s=60` en sv5 y `timeout_s=30` en sv4.
- [ ] **M1 · T10 (humano o líder, cuando se quiera; NO BLOQUEA; solo lectura)**: tamaños reales, sin
  nombres. Desde `services/partes-persistencia` (con su `.env`):

  ```
  ../../.venv/Scripts/python.exe -c "from config.settings import Settings as S; from infrastructure.sigrid.sigrid_api_client import SigridApiClient as C; s=S(); c=C(base_url=s.sigrid_api_base_url, function_key=s.sigrid_api_function_key, database=s.sigrid_api_database, timeout_s=120); print(c._post_sql_read(sql='<SQL>', parameters=[], label='m1', max_rows=10))"
  ```
  con cada `<SQL>`:
  (a) `SELECT TOP 5 obride, COUNT(*) AS n FROM obrparpar GROUP BY obride ORDER BY COUNT(*) DESC`
  (partidas de las obras más grandes);
  (b) `SELECT TOP 5 hmoide, COUNT(*) AS n FROM hmores GROUP BY hmoide ORDER BY COUNT(*) DESC`
  (líneas del parte más grande: cota de `lineas_existentes`);
  (c) `SELECT MAX(n) AS m FROM (SELECT reside, COUNT(*) AS n FROM reshor GROUP BY reside) q`
  (horas por recurso: cota de `horas_de_recursos`).
  Salen `ide` y cuentas, nunca nombres. Anotar en `progress/impl_F-038.md`.

## F-059 · DONE 2026-10-23 (review APPROVED pasada 2; pendiente desplegar sv2 y M4): la IA no lee bien el PDF con /Rotate, sv2 le manda la página ya derecha

**Aprobación del humano (2026-10-23), literal**: a la pregunta del líder «¿A en las cuatro? Si me
dices que sí, lanzo el implementer» sobre DA1–DA4 respondió «a». DA1 = A (solo OpenAI, lista
configurable), DA2 = A (imagen incrustada girada), DA3 = A (`PAGINA_COMO_IMAGEN` encendido por
defecto), DA4 = A (`OPENAI_IMAGE_DETAIL=high`). Anotada en `design.md` §7.

- **T1–T7 y T11 hechas** (implementer, 2026-10-23; un commit por tarea, fase RED con trazas):
  sv2 144 passed (112 nuevos), cobertura 99,4 % de 165 líneas cambiadas, `init.sh` en verde.
  Informe: `progress/impl_F-059.md`. azure-apps: commit local 7cc2e66 (sin push).
- **T8 hecha** (implementer, 2026-10-23): campaña del líder 20 evaluados, 17 muertos, 3
  supervivientes. [16] y [20] eran huecos reales: 4 tests nuevos (borde exacto de 1 pt; INFO
  de wiring con `caplog`), comprobados aplicando el mutante a mano. [19] es equivalente
  (frontera del 2 % inalcanzable en float). Sin cambios de producción. Detalle en
  `progress/mutacion_F-059.md`; sv2 148 passed.
- **Review pasada 1 (2026-10-23): CHANGES_REQUESTED** solo por C4 (la M4 sin comando exacto).
  Corregido (implementer, 2026-10-23): M4 abajo con su SELECT literal; además, observación 1:
  R12/R13 fijan el final del sha12 (`sha256=<12>:`) y el mutante `sha256[:13]` muere (5 failed).
- **Pendiente**: T10 (M4 tras desplegar sv2, humano) y la review pasada 2 (T9 hecha, banco).
- [x] **M4 OK (2026-10-25)**: reprocesados los 6 partes sin obra (doc002836 y doc021390) ⇒ 6 `convertida`, 0 `error`, obra (0678/0692) y fecha leídas en los 6; partes nuevos 0ef28361, b7599bcb, f1e8900d, e8ff17d2, fc892aaf y 7b26d9df. Receta original:
- [x] **M4 · T10 (humano, tras desplegar; solo lectura)**. Despliegue, lo lanza el humano:
  `.\infra\redeploy_partes.ps1 -Solo sv2`. Anotar el instante UTC del despliegue (ISO,
  p. ej. `2026-10-24T08:00:00`) y, cuando hayan entrado partes escaneados, en la base `partes`:

  ```sql
  SELECT id, created_at_utc,
         raw_extraction_json::jsonb #>> '{meta,adjunto_ia,conversion}' AS conversion,
         raw_extraction_json::jsonb #>> '{meta,adjunto_ia,motivo}' AS motivo
  FROM parte_documents
  WHERE created_at_utc >= '<instante del despliegue, ISO UTC>'
  ORDER BY created_at_utc DESC LIMIT 20;
  ```
  (`raw_extraction_json` es `Text`, de ahí el `::jsonb`; `created_at_utc` es varchar ISO y se
  compara con una cadena ISO). Esperado: las páginas escaneadas, `conversion = convertida`
  (motivo vacío); las fotos `no_aplica` / `no_es_pdf`; **ninguna fila `error`**. Si sale
  `error` o la lectura empeora, vuelta atrás: `az containerapp update -n ca-sv2-extraccion
  -g rg-partes-dev --set-env-vars PAGINA_COMO_IMAGEN=false`.
- Decisiones y desviaciones (justificadas en el informe): (1) con `PAGINA_COMO_IMAGEN=false`
  `app.py` no crea el conversor (además de pasar `frozenset()`), para que la traza diga
  `interruptor` y no `proveedor_fuera_de_lista`; (2) el `.venv` de la raíz NO tiene `openai`,
  `anthropic` ni `google-genai` (la spec solo contaba con que faltaba Pillow): los tests de
  R22 y del cableado importan los clientes con dobles de esos SDK
  (`tests/f059_sdk_falsos.py`), que solo se registran si el SDK real no se puede importar.
  No se instaló nada más que Pillow. Si se prefiere instalar los SDK en el `.venv`, los
  dobles dejan de activarse solos.

Spec en `specs/F-059-pagina-como-imagen-derecha/` (rama `feature/F-059-pagina-como-imagen-derecha`,
worktree `partes-wt-f059`); resumen en `progress/spec_F-059.md`. Solo sv2: la página escaneada
(una imagen JPEG a página completa) viaja como imagen derecha; lo demás y los fallos, como PDF.
Diagnóstico corregido por el humano el 2026-10-23: el PDF viene bien orientado (el `/Rotate` lo
endereza en cualquier visor); el fallo es de lectura de OpenAI con `input_file`.

Decisiones que tiene que validar el humano (`design.md` §7, recomendada A en las cuatro):
DA1 proveedores (solo OpenAI por defecto), DA2 conversión (imagen incrustada, sin render),
DA3 interruptor (encendido por defecto, sin tocar el entorno de Azure), DA4 `detail=high` en
toda imagen de OpenAI (también fotos del móvil). F-058 no se toca: queda como red de seguridad.

## F-054 · DONE 2026-10-23 (review APPROVED pasada 1; sv3 desplegado r20261023153823; M2 descartada): un parte sin obra o sin fecha va siempre a revisión

**2026-10-23, decisión del humano sobre la M2** (literal): «hay que corregir solo los que salen
en obra sin identificar». La M2 no se hace. M1 repetida ese día (solo lectura): 7 activos no
aprobados sin bandera, los 6 sin obra de los escaneos del 21 y 23/10 y uno del 14/10 con obra y
sin fecha (fuera de lo que pide corregir). Los 6 se releerán tras desplegar F-059 (papelera en
el portal y correo devuelto a la bandeja de entrada sin leer), o se corrigen a mano.

Rama `feature/F-054-sin-obra-o-fecha-a-revision` (worktree `partes-wt-f054`), **rebasada sobre
`dev` 38f273a**: conflictos solo en `harness/features.json`, `BACKLOG.md` y este fichero; se
quedó la versión de `dev` (su entrada de F-054 es idéntica a la de la rama, comprobado) y
`BACKLOG.md` se regeneró con `python harness/backlog.py`. Aprobación del humano: 2026-10-21
(«apruebo F-054 y la DA5») y 2026-10-23 («si, lanza f54 y la spec de relectura con gemini»).
Contexto nuevo del líder (2026-10-23): 4 páginas más del escaneo de hoy con la cabecera a null;
la causa en sv2 es F-058, el alcance de F-054 no cambia.

- **T1–T5 hechas** (un commit por tarea, fase RED con trazas) y `bash harness/init.sh` en
  verde (sv3: 2.305 passed; cobertura 100 % de 13 líneas cambiadas). Informe:
  `progress/impl_F-054.md`. **T6 hecha** (mutación lanzada por el líder el 2026-10-23: 5
  mutantes, 5 muertos, 0 supervivientes; `progress/mutacion_F-054.md`). **Review APPROVED
  (pasada 1, `progress/review_F-054.md`)**; fusionada en `dev` el 2026-10-23. Falta:
  desplegar sv3 y, con autorización expresa, la M2 (repetir antes la M1).
- Desviaciones (justificadas en el informe): 4 tests de más para fronteras y formato del
  WARNING; la semántica 18 va en presente («se corrige una sola vez a mano») porque la M2
  aún no se ha hecho; sv3 tiene 2.271 tests en `dev`, no los 2.254 de la spec.
- **M2 NO ejecutada**: necesita autorización expresa del humano para esa escritura concreta
  y el despliegue de sv3 antes (comando exacto en `design.md` §8 y en el informe). M1 daba 3
  documentos; con las 4 páginas del 23/10 podrían ser 7: repetir M1 justo antes.

## F-014 · retirada del backlog (decisión del humano 2026-10-21)

El humano, literal: «la peticion la hago yo, quitalo de la feature». La petición a RRHH
(candef 9 para MO/0006, 0007, 0008, 0031, 0366, 0405, 0456 y DNI de MO/0037) la gestiona él
directamente; F-014 sale de `harness/features.json`. Su texto y la línea base de agosto
siguen en la rama `feature/F-014-candef-9-sigrid` (`progress/peticion_F-014.md`), sin
fusionar, por si se quiere la comprobación posterior en solo lectura (V1–V3). A 2026-10-21
Sigrid sigue sin el cambio. La regla de F-015 ya está activa en producción (mapa por defecto
`8:40,9:42`): con candef 9 da 9 h de lunes a jueves y 6 h el último laborable, y lo que pase
de ahí es extra (medido en la base `partes` desde agosto: candef 9 lunes 9 ord., viernes 6
ord. + 3 extra; candef 8 de lunes a viernes 8).

## F-053 · done (2026-10-21, APPROVED pasada 1), pendiente de M2 en local y desplegar sv5 y sv4: pisar sin borrar (el pisado de sv5 pone a 0)

Spec en `specs/F-053-pisar-sin-borrar/` (rama `feature/F-053-pisar-sin-borrar`, worktree
`partes-wt-f053`, **rebasada sobre `dev` 12e1f23**, que ya trae F-034 fusionada: la
precondición de `tasks.md` se cumple y F-034 llegó con la forma que la spec supone
—`_guarda_parte_abierto`, R4 en `stmt_insert_linea`, relectura y `parte_abierto.py`—).
Informe de spec en `progress/spec_F-053.md`.

**Decisión del humano del 2026-10-21**, literal: «Lanza la siguiente luego despliego», dada
tras presentarle la spec con sus DA y la recomendación A en todas ⇒ **DA1–DA12 APROBADAS con
la opción A** (`design.md` §12). **M1 ejecutada por el líder el 2026-10-20** (solo lectura,
resultados en `design.md` §9): DA1 A confirmada (ninguna línea con venta) y DA4 A relevante
(5.096 líneas enlazadas sin synckey en 2026 que hoy el pisado podría borrar).

**Implementer (2026-10-21)**: T1–T13 y T15 hechas, un commit por tarea (T14 es MANUAL,
abajo); `bash harness/init.sh` en verde (cobertura 100 % de 86 líneas; mutación 57/57
muertos). Detalle en `progress/impl_F-053.md`. **Siguiente: reviewer.** Desviaciones respecto a la spec, justificadas:

- `transfer_consumer.py` (design §2 lo pone en «NO se tocan»): su `_resultado_fallido` lleva
  la clave `anuladas` en vez de `borradas` y su docstring dice «pisar pone a 0». Lo exigen
  R12/DA7 («el JSON de los dos canales») y la propia enmienda que la spec lista de
  `test_f002_mutantes.py` l.157, que prueba justo `_resultado_fallido`; la lógica no cambia.
- `lineas_existentes` rellena además `hmoide` (es su parámetro, sin lectura nueva): lo pide
  el INFO de R13 (`hmoide` de cada pisada).
- `pisado.py` repite `PREFIJO_PARTES = "partes:"` y `LIMITE_MOTIVO = 255` para importar solo
  de `domain` (design §5); dos tests los atan a `PREFIJO_SYNCKEY` del cliente y a
  `parte_abierto.LIMITE_MOTIVO`. `nombrar_lineas` concuerda singular/plural: con una línea,
  los textos son los de §6 al pie de la letra. `parte_abierto.py` importa `nombrar_lineas` y
  gana la función pura `pisadas_no_anuladas` (la elección de §5.3).
- Motivos con varias líneas: `incidencia_en_sigrid` nombra todos los choques En registro
  (código del parte del primero); `linea_enlazada`, solo las enlazadas.
- Doble (§7): `tex` se queda en la fila (R3 se comprueba sobre ella); `LineaSigrid` no gana
  `tex` (R13 prohíbe registrarlo y el pipeline no lo usa). Una op desconocida en `escribir`
  es `AssertionError` (antes contaba como fila).
- sv4: los campos de cada pisada del modal van con `esc` (no lo pedía la spec; el resto del
  modal no cambia). Test de fuente de R19: ningún «se borra» afirmativo («(no se borra)» es
  el texto de §6).
- Orden de tareas: entre T2 y T8 los tests de pisado de F-002/F-021/F-031/F-034 quedan rojos
  (el pipeline y los dobles cambian antes que sus enmiendas, como ordena `tasks.md`); T10 se
  verificó con `-k "r19 or r20"` porque R21/R22, del mismo fichero, son de T11.

### F-053 · verificaciones MANUAL (humano; `design.md` §9). NO ejecutadas.

M1 la hizo el líder (§9). Todo desde el repo principal `C:\Users\pgris\PycharmProjects\partes`
con F-053 fusionada en `dev`. `registro_id` 990000531–533 son sintéticos de F-053. `<FECHA>`
(AAAAMMDD) = un día de un mes `<AAAA>/<MM>` **sin partes de la 0404** (lo dice la preflight
de M2: `partes[0].existe: False`). **No usar 10/2026**: ahí está PT26/00373 con las 4 líneas
`PRUEBA-IA` de F-046 que el humano decidió conservar, y `limpiar` las borraría. Recurso: el
gruista de pruebas 2717792 (HLGR + HEGR), como en F-034. Variante sin tocar Sigrid a mano:
la línea pisada es otra línea del portal escrita por sv5 en modo pruebas (ejemplo 6).

- **Preparación · sv5 local en modo pruebas** (solo HTTP):
  ```powershell
  cd C:\Users\pgris\PycharmProjects\partes\services\partes-transfer
  ..\..\.venv\Scripts\Activate.ps1
  $env:OBRA_PRUEBAS_FORZAR = 'true'; python main.py
  ```
  En otra consola: `Invoke-RestMethod http://localhost:8005/health` ⇒ `modo_pruebas: True`,
  `obra_pruebas: 0404`, `database: ruesma`. **Si `modo_pruebas` no es `True`, PARA.**
- [x] **HECHA por el líder el 2026-10-21, autorizada por el humano («haz las pruebas m2 en
  local»)**: sv5 local con `modo_pruebas: true`, obra 0404, base `ruesma`; mes 06/2026 (sin
  partes antes). A (990000531, 8 h) ⇒ `PT26/00376` nuevo (ide 2857943), línea IA = 411591.
  Preflight de B (990000532, 6 h) ⇒ 1 conflicto con IA (`nuestra`, no enlazada). Ejecutar
  pisando ⇒ `ok`, `anuladas: 1`, **sin clave `borradas`**, IB = 411592. Consola de sv5:
  `UPDATE hmores SET can = 0, tot = 0 WHERE ide = ? AND reside = ? AND fec = ? …` y
  `pisada a 0 ide=411591 … can_antes=8.0 origen=partes`; **0 `DELETE`**. Sigrid (lectura):
  411591 `can 0 / tot 0` (sigue ahí) y 411592 `can 6 / tot 177`, ambas `PRUEBA-IA`.
  Sin limpiar todavía (decide el humano).
- [x] **M2 · pisar pone a 0 (escritura en 0404; antes de desplegar, para que un SQL inválido
  no llegue a producción)**. (1) Línea A, 8 h:
  ```powershell
  $a = @{ registro_id = 990000531; fecha_int = <FECHA>; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($a); usuario = 'M2-F053' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/ejecutar -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  ⇒ preflight: `forzada_pruebas: True` y `partes[0].existe: False` (si no, otro mes y no
  ejecutes); ejecutar: `ok: True`, `escritas` con 990000531 y su `hmores_ide` (**IA**) y un
  `PT26/…` nuevo (**P1**).
  (2) Línea B, 6 h, mismo recurso, día y código; preflight y ejecutar pisando:
  ```powershell
  $b = @{ registro_id = 990000532; fecha_int = <FECHA>; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 6 }
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($b); usuario = 'M2-F053' } | ConvertTo-Json -Depth 5
  $pf = Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p
  $pf.conflictos | ConvertTo-Json -Depth 6
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($b); pisar_claves = @($pf.conflictos[0].clave); usuario = 'M2-F053' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/ejecutar -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: preflight ⇒ un conflicto con `lineas` = `[{ide: IA, can: 8, synckey:
  partes:990000531}]`. Ejecutar ⇒ `ok: True`, `pisadas` = `[<clave>]`, **`anuladas: 1`**, sin
  clave `borradas`, `escritas` con 990000532 (`hmores_ide` **IB**). En la consola de sv5: `[sigrid-write]
  UPDATE hmores SET can = 0, tot = 0 WHERE ide = ? …` (ningún `DELETE`) y `[registro] pisada a
  0 ide=IA hmoide=<P1> can_antes=8.0 origen=partes registro_id=990000532`. Solo lectura, con
  `ANO, MES = <AAAA>, <MM>` en `prueba_escritura_sigrid.py` (cambio local, no se commitea):
  `python prueba_escritura_sigrid.py verificar` ⇒ 2 líneas en P1: la de A con `can` 0 y `tot`
  0 (sigue ahí) y la de B con `can` 6. Después, despliegue desde `infra/`:
  `.\redeploy_partes.ps1 -Solo sv5` y `.\redeploy_partes.ps1 -Solo sv4`.
- [x] **HECHA por el líder el 2026-10-21 (solo lectura, mismo sv5 local, 06/2026)**: C
  (990000533, 4 h) ⇒ 1 conflicto solo con IB 411592 (`can 6`): IA a 0 ya no sale (R5). A
  (990000531) ⇒ `ya_registrado`, 0 conflictos (R15). Limpieza **no hecha** (pendiente del
  humano: borra con `DELETE` las `PRUEBA-IA` de la 0404 en 06/2026 y 08/2026).
- [x] **M3 · una línea a 0 ya no choca; reaprobar la pisada (solo lectura, mismo sv5 local)**:
  ```powershell
  $c = @{ registro_id = 990000533; fecha_int = <FECHA>; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 4 }
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($c); usuario = 'M3-F053' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($a); usuario = 'M3-F053' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: primera preflight ⇒ un conflicto para 990000533 con `lineas` = solo IB (la de
  6 h): IA, a 0, ya no sale (R5). Segunda ⇒ la acción de 990000531 (A, a 0) es
  `ya_registrado` y `conflictos` vacío (R15). **Limpieza** (un solo
  parte en el mes):
  ```powershell
  python prueba_escritura_sigrid.py limpiar
  python prueba_escritura_sigrid.py limpiar --ejecutar
  python prueba_escritura_sigrid.py estado
  git checkout -- prueba_escritura_sigrid.py
  ```
  **Esperado**: el DRY-RUN imprime el `DELETE` de las líneas `PRUEBA-IA` del ide de P1 (si
  sale otro ide, PARA); `estado` ⇒ `NO existe parte <AAAA>/<MM> de obra 0404`. Parar sv5
  local (Ctrl+C) y cerrar esa consola.
- [ ] **M4 · textos del portal (tras desplegar sv4; sin escritura propia)**: portal con
  **Ctrl+F5**. (1) El candado de cualquier línea `registrado` dice «… En Sigrid no se borran
  lineas: para corregirla, que Administracion la edite alli (si sobra, a 0 horas);
  «Comprobar en Sigrid» enseña la diferencia.» (DA8). (2) En la próxima aprobación real con
  conflicto, el modal dice «la linea actual se pone a 0 en Sigrid (no se borra)» y cada
  pisada «linea N · código · X h · Y € → 0 h  nueva: …»; si se pisa, el resultado dice «N
  linea(s) anteriores puestas a 0 en Sigrid (pisadas).». Sin conflictos, nada cambia.

## F-034 · done (2026-10-21, APPROVED pasada 2), pendiente de desplegar sv5 y sv4 y M2–M4: sv5 solo escribe en partes de Sigrid abiertos

Spec en `specs/F-034-escribir-solo-en-partes-abiertos/` (rama
`feature/F-034-escribir-solo-en-partes-abiertos`, worktree `partes-wt-f034`); informe de spec
en `progress/spec_F-034.md`. **Spec aprobada entera** por el humano el 2026-10-20 («Ok a las
2»): DA1–DA9 con la recomendación de `design.md` §11; DA4 = A (aquí solo la guarda y R4; «pisar
= poner a 0» en F-053, detrás de F-034). **M1 (líder, 2026-10-20, solo lectura)**: mes 9 → 16
partes en estado 1 y 37 en estado 3; mes 10 → 37 en estado 1; 358 líneas `partes:%`, todas en
2026/10 y en partes En registro; 0 periodos con más de un parte En registro (`design.md` §9).

**Implementer (2026-10-20/21)**: T1–T13 hechas, un commit por tarea; `bash harness/init.sh` en
verde (cobertura 100 % de 75 líneas; mutación 22/22 detectados). Detalle en `progress/impl_F-034.md`. Desviaciones respecto a la
spec, justificadas:

- `parte_abierto.py` importa `synckey_de` de `infrastructure.sigrid.sigrid_write_client`
  (design §5 decía «imports solo de `domain`»): sin ella `confirmar_escritas` no puede tener
  la firma de design §5 sin duplicar el prefijo `partes:`. Mismo precedente que
  `reajuste_lineas.py` y `comprobacion_lineas.py` (application/services, F-046 y F-024).
- `SigridFake` gana, además de `cerrar_al_escribir` (design §6), `cerrar_tras_sentencias`
  (cuántas sentencias de líneas pasan antes del cierre): el doble recibe la lista entera, no
  los lotes de 15 del cliente real, y sin ello no se puede probar «cierre entre lotes» (§7).
- sv4: un motivo vacío o nulo agrupa bajo la clave vacía (literal de R19, «el motivo
  entero»); sv5 siempre manda motivo en las omitidas.
- `test_f046_t22_cliente_bordes.py` no se toca: sus índices de parámetros no cambian (la
  guarda va al final); el texto nuevo lo fijan `test_f046_cliente_reajuste.py` (ampliado) y
  `test_f034_cliente_guarda.py`.

**Review pasada 1 (2026-10-21): CHANGES_REQUESTED** solo por C4 (faltaban aquí M2–M4 con
comando exacto); código, SQL, tests y mutación aprobados. Corregido abajo (sin tocar código);
M3 reformulada en algo observable, alineada en `design.md` §9. **Siguiente: reviewer
(pasada 2).**

### F-034 · verificaciones MANUAL (humano; `design.md` §9). NO ejecutadas.

Todo desde el repo principal `C:\Users\pgris\PycharmProjects\partes` con F-034 ya fusionada
en `dev` (el worktree no tiene `.venv` ni `.env`). Los `registro_id` 990000341–342 son
sintéticos de F-034 (los de F-046 son 990000001–004). `<FECHA>` y `<FECHA2>` (AAAAMMDD) = dos
días de un mismo mes `<AAAA>/<MM>` **sin partes de la 0404**: lo dice la preflight de M2
(`partes[0].existe: False` y `del_periodo` vacío); si no, otro mes. **No usar 10/2026**: ahí
está PT26/00373 con las 4 líneas `PRUEBA-IA` de F-046 que el humano decidió conservar, y
`limpiar` las borraría.

- **Preparación · sv5 local en modo pruebas** (solo HTTP: el `.env` de sv5 no trae
  `COLAS_*`, así que no consume `q-transfer`):
  ```powershell
  cd C:\Users\pgris\PycharmProjects\partes\services\partes-transfer
  ..\..\.venv\Scripts\Activate.ps1
  $env:OBRA_PRUEBAS_FORZAR = 'true'; python main.py
  ```
  En otra consola: `Invoke-RestMethod http://localhost:8005/health` ⇒ `modo_pruebas: True`,
  `obra_pruebas: 0404`, `database: ruesma`. **Si `modo_pruebas` no es `True`, PARA**: el
  `.env` local trae `OBRA_PRUEBAS_FORZAR=false` y escribiría en la obra real.
- [x] **HECHA por el líder el 2026-10-21, autorizada por el humano («haz las pruebas m2 en
  local»)**: sv5 local con `modo_pruebas: true`, obra 0404, base `ruesma`; mes 08/2026 (julio
  ya tenía PT26/00296). Preflight ⇒ `forzada_pruebas: True`, `existe: False`, escribir 1.
  Ejecutar ⇒ `ok`, **P1 = `PT26/00375`** (ide 2857940, estado 1, creado), A escrita en la
  línea 411586, `omitidas` vacía. Reajuste 8 → 6 ⇒ `ok`, `can 6`, `escrita: True`.
  `comprobar_asiento_analitico.py` ⇒ `PT26/00375 · En registro · 1 linea(s) (1 nuestras) ·
  importe con cuenta 177.00`. **P1 se conserva para la M3** (cerrarlo en Sigrid, con
  autorización expresa).
- [x] **M2 · registro con la guarda (escritura en 0404; antes de desplegar, para que un SQL
  inválido no llegue a producción)**. Línea A del gruista de pruebas (2717792, HLGR + HEGR):
  ```powershell
  $a = @{ registro_id = 990000341; fecha_int = <FECHA>; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($a); usuario = 'M2-F034' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/ejecutar -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: preflight (solo lectura) ⇒ `forzada_pruebas: True`, `partes[0].existe:
  False`; ejecutar ⇒ `ok: True`, `escritas` = `[{registro_id: 990000341, hmoide: …}]`,
  `omitidas` vacía y `partes[0].cod` = un `PT26/…` nuevo (apuntarlo: es **P1**). Es decir: el
  `INSERT` guardado es SQL válido en SQL Server y la guarda deja pasar (el parte nace En
  registro, R18). Comprobación (solo lectura), en la misma carpeta: `python
  comprobar_asiento_analitico.py --empresa 1 --obra 0404 --ano <AAAA> --mes <MM>` ⇒ `<P1> ·
  En registro · 1 linea(s) (1 nuestras)`. **Reajuste F-046** sobre A (R5: guardia y `UPDATE`
  con `UPDLOCK, HOLDLOCK`):
  ```powershell
  $r = @{ lineas = @(@{ registro_id = 990000341; antes = 8; despues = 6 }); usuario = 'M2-F034' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/reajuste/ejecutar -ContentType 'application/json' -Body $r | ConvertTo-Json -Depth 6
  ```
  ⇒ `ok: True` y en `lineas` la de 990000341 con `can: 6` y `escrita: True`. La extra nueva
  del reajuste (R6) no se prueba a mano: la fija `test_f034_r6_*`. Después, el **despliegue**
  desde `infra/`:
  `.\redeploy_partes.ps1 -Solo sv5` y `.\redeploy_partes.ps1 -Solo sv4` ⇒ revisión nueva de
  cada uno en marcha; aprobar en el portal registra como siempre (`registrado`).
- [ ] **M3 · parte cerrado (solo con autorización expresa; solo 0404)**. (1) Administración
  pasa P1 a **Cerrado** (estado 3) en Sigrid; **no** Contabilizar (Imputado crea asiento).
  (2) Con el mismo sv5 local, A otra vez más una línea B nueva:
  ```powershell
  $b = @{ registro_id = 990000342; fecha_int = <FECHA2>; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }
  $p = @{ obra = @{ codigo = '0404' }; lineas = @($a, $b); usuario = 'M3-F034' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/ejecutar -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: `ya_registradas` = `[990000341]` (R16, sin sentencia); `escritas` =
  `[{registro_id: 990000342, hmoide: …}]`; `partes[0]` con `complementario: True`,
  `cerrados` = `[<P1>]` y un `PT26/…` nuevo (**P2**) (R15). `comprobar_asiento_analitico.py`
  como en M2 ⇒ `<P1> · Cerrado · 1 linea(s)` y `<P2> · En registro · 1 linea(s)`. El
  reajuste de A en P1 cerrado (`$r` de M2 con `antes = 6; despues = 5`, a
  `/api/reajuste/comprobar`, solo lectura) ⇒ `ok: False`, veredicto `editable: False` con
  «su parte de Sigrid no esta En registro» (R17).
  **Lo que NO se verifica a mano**: el `omitido` `parte_no_abierto` y el `affected_rows = 0`
  del `INSERT` guardado solo se dan si el cierre cae en los milisegundos entre la elección
  del parte (bajo el lock) y el `commit`; con P1 ya cerrado, sv5 elige el complementario y no
  manda nada a P1. Forzarlo exigiría un `sql/write` a mano fuera de sv5, que no se propone.
  Lo fijan `test_f034_r2_*`, `r4_*`, `r9_*` (ejemplo 1) y `r11_*`, y M2 prueba que ese SQL es
  válido. (3) **Limpieza**: `limpiar` actúa sobre UN parte del mes (el primero que devuelve
  `parte_mes`) y borra su cabecera si la creó sv5 y queda vacía; por eso va dos veces. Antes,
  en `prueba_escritura_sigrid.py`, `ANO, MES = <AAAA>, <MM>` (cambio local, no se commitea):
  ```powershell
  cd C:\Users\pgris\PycharmProjects\partes\services\partes-transfer
  python prueba_escritura_sigrid.py limpiar
  python prueba_escritura_sigrid.py limpiar --ejecutar
  python prueba_escritura_sigrid.py limpiar
  python prueba_escritura_sigrid.py limpiar --ejecutar
  python prueba_escritura_sigrid.py estado
  git checkout -- prueba_escritura_sigrid.py
  ```
  **Esperado**: cada `limpiar` sin `--ejecutar` (DRY-RUN) imprime los `DELETE` sobre el ide
  de P1 o de P2 (si sale otro ide, PARA y no lances el `--ejecutar`); el `estado` final ⇒
  `NO existe parte <AAAA>/<MM> de obra 0404`. Parar sv5 local (Ctrl+C) y cerrar esa consola,
  que lleva `OBRA_PRUEBAS_FORZAR=true`.
- [ ] **M4 · modal de resultado (tras desplegar sv4; sin escritura propia)**: portal con
  **Ctrl+F5** y, en la próxima aprobación real en la que alguna línea salga omitida (p. ej.
  un encargado sin hora extra), mirar el modal de resultado. **Esperado**: «N linea(s) no
  registradas:» y debajo una fila por motivo, «<texto antes de los primeros dos puntos> ·
  <n>» (el encargado: «el recurso no tiene codigo de hora extra en Sigrid · 1»); ya no sale
  «(reglas)»; el `title` del badge `omitido` de la línea sigue con el motivo entero. Sin
  omitidas, el modal es el de siempre.

## F-050 · done (2026-10-20, APPROVED pasada 1), pendiente de despliegue de sv4 y M2–M6: misma fila para el mismo trabajador

### T11 · desbloqueada (2026-10-20)

**Decisión del humano del 2026-10-20 («si») sobre la opción B**: el suelo
`mutacion.timeout_por_mutante_s` de `harness/rigor.json` sube de 120 a 300 s (commit
`04613e6` del líder; tests de harness/mutación `110 passed`). **No se porta a `arnes-base`**:
responde al tamaño de la suite de sv4, no es una mejora genérica. El líder lanzó
`python -m harness.mutacion --feature F-050 --workers 1` (sin `--timeout`): línea base en
verde 519,6 s, timeout por mutante 1040 s; **20 evaluados: 13 muertos, 4 supervivientes
(#7, #9, #11, #16), 3 timeouts (#12, #13, #20)**, 14175,8 s. Informe en
`progress/mutacion_F-050.md`.

**T11 cerrada (implementer, 2026-10-20)**, sin relanzar la campaña: #7 y #11 equivalentes
estrictos; #9 equivalente en el dominio (centinela `10**9` frente a `10**10`); **#16 hueco
real** (alta con ficha y recurso, caso de R19/M5) ⇒ test nuevo
`test_f050_r16_con_ficha_y_recurso_hereda_de_su_rec`, RED contra el mutante y verde; los 3
timeouts reproducidos: los matan 13, 9 y 4 tests de R14/R15 de `test_f050_portal.py`, sin
bucle (contención de la máquina con `-x` y los tests de F-050 al final). Balance: 17
detectados y 3 equivalentes de 20. `bash harness/init.sh` en verde. **Siguiente: reviewer.**

**Nota de despliegue (líder, 2026-10-20)**: en Azure, `REPARTO_REAJUSTE=true` está
**encendido en sv3 desde el 2026-10-18** (paso 4 de T23 de F-046, abajo).

### Motivo del `blocked` (T11, historia)

T1–T10, T12 y T13 hechas; `bash harness/init.sh` en verde (PUERTA COBERTURA 100 % de 60
líneas cambiadas). La mutación muestreada que exige el nivel **estándar** no ha evaluado
ningún mutante: `python -m harness.mutacion --feature F-050 --workers 3` (sin `--timeout`)
sale con código 3 en la **línea base**: «la suite SIN MUTAR agotó los 600 s que se le
concedieron (el suelo `mutacion.timeout_por_mutante_s` × holgura 5), con 3 worker(s)
compitiendo por la máquina». La suite de sv4 sola tarda **569 s** (2347 tests); tres a la
vez no caben. No es un fallo de F-050 (la suite sin mutar está en verde), sino del tamaño de
la suite de sv4 frente al reloj de la campaña. La herramienta propone bajar workers o subir
el suelo; las dos cosas se salen de lo que se me pidió (`--workers 3`, sin tocar el arnés).

**Propuesta (decide el líder/humano)**:

- **A (recomendada)**: lanzar la campaña con `--workers 1` (en serie sobre el worktree, con
  la máquina libre). La línea base sola (569 s) cabe en 600 s, aunque con poco margen; el
  timeout por mutante sería ~1140 s y la campaña de 20 mutantes, unas 3–3,5 h. Si la lanza el
  líder (como en F-048), el implementer analiza después los supervivientes.
- **B**: mantener `--workers 3` y subir en `harness/rigor.json` el suelo
  `mutacion.timeout_por_mutante_s` (p. ej. de 120 a 300: 1500 s para la línea base). Es
  configuración del arnés que vale para todas las features; quizá también para `arnes-base`.
- **C**: lo que el líder prefiera; el resto de F-050 no cambia.


**Desbloqueada el 2026-10-20 por decisión del humano** (respuesta literal «apruebo») sobre la
propuesta de T2 de abajo: se corrige el DATO de los fixtures, no las aserciones. R22 queda
ampliada a «literal y, donde el fixture comparte recurso entre personas, el recurso de la
persona B» (anotado en `requirements.md` R22 y `tasks.md` T2). Lo que sigue del bloqueo es historia.

Implementer en la rama `feature/F-050-misma-fila-para-el-mismo-trabajador` (worktree
`partes-wt-f050`), rebasada sobre `dev` (`ff2ed8e`; conflictos solo en `BACKLOG.md`,
`harness/features.json` y `progress/current.md`, resueltos conservando las dos partes).
Solo sv4, sin esquema, sin Sigrid ni migración; rigor **estándar**.

**Spec aprobada entera.** DA2–DA10 el 2026-10-20 («ok a lo demás», DA10 opción a) y
**DA1 (opción A), DA1b y DA11 el 2026-10-20 («ok»)**; DA5 y DA6 ampliadas, confirmadas
con DA1. **M1 (líder, 2026-10-20, solo lectura)**: 560 líneas casadas activas, 38 filas
(obra, recurso), **1 fila que se une**, 0 fichas sin recurso, 0 casadas sin ficha ni
recurso, 0 DNIs con varios recursos en una obra, 36 recursos, 0 sin empresa, 0 DNIs en dos
empresas.

**Implementación (implementer, 2026-10-20)**: T1–T13 hechas, un commit por tarea;
detalle, fases RED y evidencias en `progress/impl_F-050.md`. Pendiente: el reviewer.

**MANUAL (humano), pendiente** (`design.md` §6; M1 ya medida por el líder). Solo lectura
salvo el despliegue y M5; los agentes no los lanzan:

- **Despliegue solo de sv4**: `.\redeploy_partes.ps1 -Solo sv4` desde `infra/`.
- **M2**: obra 0678, periodo con el 15/10: el trabajador del caso en **una** fila «8+2»,
  enlazada a `/trabajadores/rec-…`.
- **M3**: detalle de ese parte: un bloque con las dos líneas; el listado de partes cuenta
  un trabajador menos.
- **M4**: una URL antigua `/trabajadores/emp-…` y una `nom-…` redirigen (307) a la `rec-`.
- **M5 (opcional; escribe en la base `partes`, no en Sigrid)**: «+ Añadir línea» desde la
  vista de un trabajador en un parte donde ya está ⇒ su fila, casada y con su ficha
  (`empleado_line_no`, leído, `empleado_ide`, `empleado_reside`).
- **M6**: «Por persona» con la columna «Empresa»: una persona de Ruesma y de Porsan en dos
  filas con su empresa, y cada vista con la suya en la cabecera; anotar cuántas «—».

### Motivo del `blocked` (historia; T2, regla R22 / tasks.md: «otro cambio ⇒ blocked y se consulta»)

16 tests de 4 ficheros no se arreglan cambiando solo el literal de la clave, porque sus
**fixtures** dan el mismo recurso a dos personas o dos recursos a una, algo que con la
clave A (recurso primero) cambia quién es quién. No es un fallo del código: es el dato
sintético, que antes no importaba porque la clave miraba la ficha.

1. **Dos fichas en el mismo recurso 501** (f019 portal ×2 de 8, f022 aprobar ×4, f025
   vistas ×3): la persona B (ficha 88) se siembra con los helpers
   `tests/dobles.py::sembrar_parte` y `tests/test_f025_aprobacion.py::sembrar`, que fijan
   `recurso_ide=501` para cualquier ficha; con A, A y B son la misma `rec-501` (riesgo R-b
   de design §9; en Sigrid un recurso persona es de una sola persona).
2. **Una ficha con dos recursos** (f019 portal, 6 de 8): el mensual de
   `test_f019_bandeja.sembrar_mensual` es ficha 77 con recurso 602 y el fixture
   `publicado` siembra sus otras líneas (ficha 77) con el 501 fijo: con A son dos claves.
3. **Clave calculada en un helper** (f035 repositorio ×2): `_asignar` arma la clave
   `nom-…` del leído; tras la primera reasignación (sin ficha, recurso 903) la clave de
   esas líneas es `rec-903` y la segunda llamada por clave (método `worker_key`) actúa
   sobre 0 líneas (R13, comportamiento esperado).

**Propuesta (verificada: los 6 ficheros afectados dan `296 passed`; diff aplicable en
`progress/propuesta_T2_F-050.diff`)**: corregir el DATO, no ninguna aserción:

- `tests/dobles.py::sembrar_parte` y `tests/test_f025_aprobacion.py::sembrar` ganan
  `recurso_ide: int = 501` (por defecto, igual que hoy para todos los demás tests).
- Persona B (ficha 88) sembrada con `recurso_ide=502` en f019 (1 sitio), f022 (2) y f025
  vistas (1); su literal `emp-88` → `rec-502` (f022 ×1 comentario, f025 vistas ×4).
- f019 `publicado`: las líneas libre y registrada de la ficha 77 con `recurso_ide=602` (el
  del mensual) y su literal `rec-501` → `rec-602` (4 sitios).
- f035 `_asignar` gana `clave` opcional (por defecto el `nom-…` de hoy) y
  `test_f035_r12_reasignar_a_una_ficha_quita_recurso_manual` pasa `clave="rec-903"` en
  la segunda reasignación.

Alternativa: mantener los fixtures y cambiar las aserciones (perderían su intención: dejan
de distinguir a A de B). No se recomienda.

**Decide el humano**: aprobar la propuesta (amplía R22 a «literal y, donde el fixture
comparte recurso entre personas, el recurso de la persona B») o indicar otra cosa. Con el
visto bueno, el implementer aplica el diff, cierra T2 y sigue con T3–T13.



## F-051 · done (2026-10-19, APPROVED pasada 1; M1 y M2 superadas con gemini-4-argon), pendiente de despliegue: extracción fila a fila, cada número a su fila

**Decisión del humano (2026-10-19, «haz la recomendación»)**: se cierra F-051 tal cual (prompt
reforzado + red de la DA2) y sv2 pasa a `GEMINI_MODEL=gemini-4-argon` (cambio de variable en
Azure, lo lanza el humano; `infra/create_capps_partes.ps1` actualizado y documentado en
`azure-apps/partes.md`). Con Argon y el prompt de F-051: **M1** 17/10 y 18/10 de la 0686 bien
3 de 3; **M2** las 7 páginas laborables de la batería (5 obras) perfectas 3 de 3. Queda
pendiente la comparativa con Claude Opus 5.5 y OpenAI GPT-6 Luna / GPT-6.1 Sol (faltan sus
claves en el Key Vault); si alguno lee mejor, el cambio de modelo es solo de variable.
Despliegue: sv3 y sv2 (sin orden obligado, design §10) y la variable del modelo.

**Review**: APPROVED (pasada 1, `progress/review_F-051.md`).
**M1 (líder, 2026-10-19) NO superada con el modelo de producción ⇒ `blocked` (DA3).**
Batería fuera del repo (código real de sv2 y catálogo auxhor de Sigrid en lectura;
respuesta correcta leída a mano del PDF; 14 páginas: las 3 de la 0686 16–18/10, 7 de
fin de semana o festivo con tabla casi vacía y 6 laborables de 5 obras):

| Prompt · modelo | 17/10 bien | 18/10 bien | Páginas perfectas | Difíciles perfectas | $/parte real |
|---|---|---|---|---|---|
| actual · gemini-3.7-flash (2 runs) | 1/2 | 0/2 | 22/28 | 9/14 | 0,021 |
| F-051 · gemini-3.7-flash (3 runs) | **0/3** | **0/3** | 34/42 | 14/21 | 0,016 |
| actual · gemini-4-argon (2 runs) | 2/2 | 2/2 | 27/28 | 13/14 | 0,019 |
| F-051 · gemini-4-argon (3 runs) | **3/3** | **3/3** | 41/42 | 20/21 | 0,020 |

Con Flash 3.7 el refuerzo del prompt no corrige el desplazamiento (17/10 sigue en fila 1
y 2; también falla el 03/10 de la 0686, que en producción se leyó mal y nadie lo había
detectado). Gemini 4 Argon no desplaza ninguna fila con ninguno de los dos prompts; su
único fallo (0686 10/10, 1 de 5 runs) es otro: copia las horas de la columna de
partidas en «Ord.». La red de la DA2 (`tabla_dispersa`) sí mandaría a revisión los
partes que Flash lee mal (son tablas dispersas). Decide el humano (DA3): cambio de
modelo, aceptar con la red de la DA2, o esperar a la comparativa con Claude y OpenAI
(faltan sus claves en el Key Vault). M2 no se ha hecho.

**Aprobación del humano (2026-10-19, «ok apruebo»)** con las opciones recomendadas:
**DA1 = A** (campo por fila `numero_linea_horas`, antes de las horas), **DA2 = C**
(`autocomprobacion_fila` + `tabla_dispersa` en sv3 con el interruptor
`REVISAR_TABLA_DISPERSA`, defecto `true`), **DA3 = 3 de 3** ejecuciones correctas por
página en M1 (si no se alcanza: `blocked` con la tabla, sin iterar el prompt).
**Dato de la DA2 (líder, solo lectura, partes activos desde 2026-06-01)**: `tabla_dispersa`
habría marcado 8 de 108 partes laborables y 9 de 17 de fin de semana.

**Implementación (implementer, 2026-10-19)**: T1–T9 y T12 hechas, `init.sh` en verde
(cobertura 100 % de 66 líneas, mutación 17/20 muertos + 2 cazados con tests nuevos y 1
equivalente). Detalle en `progress/impl_F-051.md`. **Pendiente del líder**: M1 (T10, PDF
real de la 0686 contra el modelo de producción, 3 de 3 por página) y M2 (T11, ≥ 5
laborables); y una línea en `azure-apps/partes.md` para `REVISAR_TABLA_DISPERSA`
(desviación de `design.md` §1 por la regla de `CLAUDE.md`; texto propuesto en el informe).

**Spec (spec-author, 2026-10-19)** en `specs/F-051-extraccion-fila-a-fila/`, rama
`feature/F-051-extraccion-fila-a-fila` (worktree `partes-wt-f051`). Caso: obra 0686, 17 y
18/10/2026, Gemini subió cada cifra una fila en una tabla casi vacía (confianza 95). Toca sv2
(prompt `parte_trabajo_es`, y el esquema con DA1 = A) y, con DA2 ≠ A, sv3. Rigor `estandar`.
De paso: el `schema_hint` no lista `dni` (el esquema lo tiene desde F-030); la spec lo añade.

**Decisiones abiertas para el humano** (detalle en `design.md` §7):

- **DA1** autocomprobación: A) campo `numero_linea_horas` por fila, antes de las horas
  (recomendada); B) lista `filas_con_horas` en la raíz; C) solo prompt.
- **DA2** red de seguridad en sv3 (dueño de `review_required`): A) ninguna; B) solo
  autocomprobación incoherente; C) B + «tabla dispersa» con interruptor
  `REVISAR_TABLA_DISPERSA` (recomendada). Hay una consulta de solo lectura sobre
  `raw_extraction_json` para medir cuántos partes marcaría C antes de decidir.
- **DA3** aceptación de M1: 3 de 3 ejecuciones correctas por página; si no, `blocked` y decide
  el humano.

**Manual pendiente tras implementar**: M1 (PDF real troceado, no versionado, con el modelo de
producción) y M2 (≥ 5 partes laborables bien leídos hoy). Repetibles con otro proveedor/modelo
vía el `.env` local de sv2: es el enganche de la comparativa de modelos, que va aparte.


## F-046 · done (2026-10-18, APPROVED pasada 2), M1–M3 hechas, pendiente de despliegue y M4–M6: reajuste en Sigrid al aprobar

**Cierre (líder, 2026-10-18).** Reviewer: CHANGES_REQUESTED en la pasada 1 (solo T24 sin
marcar) y APPROVED en la pasada 2 (`progress/review_F-046.md`). **El humano acepta los 11
equivalentes E1–E7** (respuesta literal «acepto los equivalentes», 2026-10-18).

- **M2 · hecha (líder, 2026-10-17, solo lectura)**: las 50 últimas `hmores` con synckey
  `partes:` (ides 410669–410906) tienen los 6 enlaces a 0/NULL.
- **M3 · hecha (líder, 2026-10-18, autorizada por el humano)**: sv5 local del worktree con
  `OBRA_PRUEBAS_FORZAR=true`, recurso de pruebas del script, `registro_id` 990000001–004,
  octubre (los partes 2026 de la 0404 son de pruebas de `porcentajes`, «PRUEBA-PORC», y no se
  tocaron: sv5 creó el parte de pruebas **PT26/00373**, `hmo` 2855815). (a)–(g) bien,
  comprobados leyendo `hmores`: 8 / −4 → 2,5 / 1,5 con `tot = can × pre` (73,75 y 42), mismo
  ide, `pos`, marca y synckey; repetir ⇒ `ya_aplicada` sin escribir; «antes» falso ⇒ lote
  rechazado sin escribir; **(e bis)** guardia descuadrada mandada en un lote con una sentencia
  válida ⇒ SQL Server da el error de conversión `reajuste-descuadrado-411030` y revierte el
  lote entero (la válida no se aplicó); base 8 ⇒ 5,5 y extra nueva 411033 de 2,5 (HEGR, su
  `pre`, la misma cuenta, `PRUEBA-IA`); extra a 0 ⇒ `can = 0`, `tot = 0`, la línea sigue.
  **(h) por decisión del humano NO se borra**: las 4 líneas (411030–411033) quedaron a 0 con
  el propio reajuste; el parte PT26/00373 sigue existiendo, vacío de horas e importe.

**Implementación (implementer, 2026-10-14)**: T1–T21 hechas en los tres bloques (sv5, sv3 +
ORM, sv4), docs y `azure-apps/partes.md` (commit local). Interruptor `REPARTO_REAJUSTE`
apagado por defecto. Detalle, desviaciones justificadas y evidencias en `progress/impl_F-046.md`;
mutación en `progress/mutacion_F-046.md`.

**T22 · hecha (implementer, 2026-10-17)**: campaña completa de 565 mutantes (la lanzó el
humano, HEAD `6b9ceed`): 436 muertos, 115 supervivientes y 14 timeouts. Re-evaluados uno a uno
con `progress/redirigir_mutantes_F-046.py`: 104 supervivientes mueren con 89 tests nuevos
`test_f046_t22_*` y los 14 timeouts mueren (contención de la máquina, no un bucle). **554/565
muertos; 11 equivalentes (E1–E7) PENDIENTES de aceptación del humano**, cada uno con demostración
ejecutable; 0 bugs. Detalle en `progress/mutacion_F-046.md`; resumen en `progress/impl_F-046.md`.

**MANUAL (humano) · despliegue y encendido (T23), pendientes**, en este orden:

1. ~~Antes: M2 y M3 (abajo).~~ Hechas (ver «Cierre»).
2. **Despliegue sv5 → sv4 → sv3** (distinto del habitual), con el interruptor apagado, desde
   `infra/`: `.\redeploy_partes.ps1 -Solo sv5`, `.\redeploy_partes.ps1 -Solo sv4`,
   `.\redeploy_partes.ps1 -Solo sv3`.
3. **M4** (base `partes`, solo lectura): `SELECT count(*) FROM reparto_pendiente` ⇒ 0 (la tabla
   la crean sv3/sv4 al arrancar).
4. ~~Encender: `az containerapp update -n ca-sv3-persistencia -g rg-partes-dev --set-env-vars REPARTO_REAJUSTE=true`.~~
   **Hecho**: `REPARTO_REAJUSTE=true` encendido en sv3 en Azure desde el 2026-10-18 (dato del
   líder, anotado el 2026-10-20).
5. **M5**: `SELECT estado, count(*) FROM reparto_pendiente GROUP BY estado`; Log Analytics de
   `ca-sv3-persistencia` con `Log_s has 'reparto'` (líneas «reparto propuesto» y
   «reajuste: propuestos=…»).
6. **M6** (escritura en producción, la autoriza y la hace el humano en el portal): el 14/10
   (0678/0704) con «Aplicar» ⇒ en Sigrid 0678 ordinaria 2,5 y extra 1,5; en `partes`, tras la
   pasada siguiente, el reparto `materializado` y los mismos valores.
7. ~~Aceptar o rechazar los 11 mutantes equivalentes E1–E7.~~ Aceptados el 2026-10-18.

**MANUAL (humano) del bloque sv5, pendientes** (design §9; M1 ya hecha por el líder):

- **M2** (solo lectura, `POST /api/sql/read` de sigrid-api, base `ruesma`):
  `SELECT TOP 50 ide, dvaproide, dvfproide, hdereside, emprccide, empdpreide, empabside FROM hmores WHERE synckey LIKE 'partes:%' ORDER BY ide DESC`
  ⇒ todo 0 o NULL (si no, DA17 deja esas líneas sin reajuste).
- **M3** (escritura en la obra de pruebas): sv5 local con `OBRA_PRUEBAS_FORZAR=true`,
  `registro_id` sintéticos ≥ 990000001 y el recurso de pruebas del script; `ANO`/`MES` de
  `prueba_escritura_sigrid.py` = mes de la prueba. (a) `POST /api/registro/ejecutar` 8 h y
  extra −4; (b) `POST /api/reajuste/comprobar` 8 → 2,5 y −4 → 1,5 ⇒ `ok: true`, editables;
  (c) `POST /api/reajuste/ejecutar` ⇒ `can` 2,5 / 1,5 y `tot = can × pre`
  (`python prueba_escritura_sigrid.py verificar`); (d) repetir ⇒ `ya_aplicada: true`, sin
  escribir; (e) una línea con «antes» falso y otra buena ⇒ `ok: false` y nada escrito;
  **(e bis)** cambiar a mano `can` de una línea entre `comprobar` y `ejecutar` ⇒ la guardia
  aborta el lote con el error de conversión `reajuste-descuadrado-<ide>` (confirma que
  sigrid-api revierte la transacción); (f) base 8 sin extra ⇒ 5,5 + extra nueva 2,5 con
  `PRUEBA-IA`; (g) extra a 0 ⇒ `can = 0`, `tot = 0`, la línea sigue; (h)
  `python prueba_escritura_sigrid.py limpiar`, `limpiar --ejecutar` y `verificar` ⇒ sin
  `PRUEBA-IA`.

**Spec APROBADA por el humano el 2026-10-14** (respuesta literal «si»): DA1–DA17 recomendadas más la enmienda [E] (sin borrados en Sigrid; candef 9).

Spec en `specs/F-046-reajuste-en-sigrid-al-aprobar/` (worktree `partes-wt-f046`, rama
`feature/F-046-reajuste-en-sigrid-al-aprobar`). **Depende de F-045** (en implementación en
`partes-wt-f045`): se implementa sobre `dev` con F-045 fusionada. Prioridad 2, rigor crítico.
Toca sv3 (propuesta, materialización, candado consultivo), sv5 (`UPDATE hmores` bajo el lock)
y sv4 (aviso y decisión), más la tabla `reparto_pendiente` en las dos copias del ORM.

**Decisiones abiertas para el humano** (design §6, todas con recomendación): DA1 una feature
en tres bloques o partir en F-046/F-047; DA2 interruptor `REPARTO_REAJUSTE` en sv3; DA4 quién
materializa (sv3); DA5 reserva `nextval` para la synckey de la extra nueva (hallazgo H1: la
propuesta de F-045 §8 no lo resolvía); DA6 sentencia guardia para la atomicidad en Sigrid;
DA8 lo libre lleva el ideal mientras está pendiente («Mantener» pasa a dos pasos); DA13
bloquear aprobar el documento con un reparto vivo; DA14 `CLAUDE.md` no cambia.

**Enmienda del humano (2026-10-14), marcada «[E]» en la spec**: Sigrid no se borra nunca (solo
`UPDATE` e `INSERT`; a 0 ⇒ `can = 0`, `tot = 0`; R47) y casos de candef 9 con la jornada de
sv3 (viernes J = 6, R9a–R9c, R46). M1 hecha por el líder: `ALLOWED_WRITE_PREFIXES` = `INSERT`,
`UPDATE`, `DELETE` (el `DELETE` no se usa).

**Antes de encender nada**, MANUAL (humano): M2 enlaces de nuestras
líneas `hmores` a 0; M3 prueba de escritura en modo pruebas (0404, `PRUEBA-IA`) y limpieza
con `prueba_escritura_sigrid.py`. Despliegue en orden **sv5 → sv4 → sv3** con el interruptor
apagado (design §7 R-e, §9).

## F-048 · done (2026-10-16, APPROVED pasada 2): ordinarias + extras leídas en laborable siguen la regla de jornada

**PARADA 1 superada (2026-10-15).** El humano aprueba la implementación con TODAS las
decisiones DA1–DA10 tal como las recomienda `design.md` §6 (A en DA2: sumar en la
ingesta; DA3; DA4 sin umbral; DA6 sin retroactivo; rigor crítico). Aclaración literal
del humano sobre DA2: «lo que no quiero es que salgan 3 líneas en el front por ejemplo
en el caso 4+2. es decir por día solo hay una fila de extras y otra de ordinarias». La
opción A lo cumple (4+2 ⇒ `normal` 8 + `extra_auto` −2); se añade un test explícito de
que los casos 1, 2 y 4+2 dejan EXACTAMENTE dos líneas activas (una `normal` y una
`extra_auto`).

**Excepción a «una sola feature en curso» (decidida por el humano):** F-046 sigue
`in_progress` en su rama (`partes-wt-f046`) con una campaña de mutación en marcha que no
se perturba. F-048 trabaja sobre `dev` actual (dc03468), SIN F-046 ni F-047 (T0 no se
puede hacer aún). **Riesgo anotado**: al fusionar habrá conflictos en las dos copias de
`orm_models.py` (F-046 añade una tabla) y en `save_parte` (F-047 cambia su firma); se
resuelven al fusionar. La mutación de F-048 espera a que termine la de F-046.

**DESBLOQUEADA (2026-10-15): el humano elige la opción A (literal «en f48 opcion A») y
pide continuar («continua la implementacion»).** Enmienda en design §5 y T1. Al aplicar
A apareció un séptimo guardián, `tests/test_f015_r29_guardian_cinco_tablas.py::
test_f015_r29_la_lista_de_parte_registros_sigue_siendo_de_56` (cuenta la longitud de la
lista; solo falla cuando la lista crece, por eso no salió en el bloqueo): mismo cambio
de 56 a 57, dentro de la decisión A. Igual con los dos guardianes de F-019
(`test_f019_r29_sv3_…_56_columnas` en sv3 y `test_f019_r29_sv4_…_56_columnas` en sv4),
que el `grep` del bloqueo no cazó (aserción `== 56` sin la palabra «columnas» en la
línea): nueve tests en total, solo cuentas y lista. La campaña de F-046 murió; la mutación de F-048
la lanzará el líder (hay campañas de otros proyectos en la máquina).

**Implementación (implementer, 2026-10-16)**: T1–T7 hechas, T9 y T10 abajo; T0 aplazada
(dev sin F-046/F-047). **T8 cerrada (2026-10-16)**: el líder lanzó la campaña
(`--workers 6`): 11 mutantes, 11 muertos, 0 supervivientes, 0 timeouts, 235,4 s
(`progress/mutacion_F-048.md`). init.sh en verde. Informe: `progress/impl_F-048.md`.
Pendiente: reviewer.

**MANUAL (humano), pendiente** — solo lectura salvo el despliegue; los agentes no:

- **M1 · antes de desplegar** (solo lectura, base `partes`): SQL de `design.md` §9
  (líneas `extra` explícitas > 0 sin congelar que se quedan como hoy; aproximada).
- **Despliegue** de sv3 y sv4 con `redeploy_partes.ps1` desde `infra/` (los dos aplican
  `ddl_complementario`; cualquier orden vale). Antes, fusionar F-046/F-047 si van juntos
  (conflictos previstos en las dos copias de `orm_models.py` y en `save_parte`).
- **M2 · columna**: `information_schema.columns` de `horas_extra_leidas` ⇒
  `double precision`, `YES`.
- **M3 · Log Analytics** (`ca-sv3-persistencia`): `Log_s has 'filas_extra_sumadas'` y
  `Log_s has 'reparto'` en el mismo documento.
- **M4 · primer caso real**: parte con extras leídas en laborable ⇒ `normal` J con la
  etiqueta «incl. X h extra leídas» y su `extra_auto` (SQL de design §9).
- **M5 · opcional, solo con autorización expresa**: reingestar partes sin congelar de M1.

Registro del bloqueo (historia): **BLOQUEADA en T1 (implementer, 2026-10-15): seis tests
existentes fuera de design §5 fallan al añadir la columna.** design §5 dice «Ningún test existente cambia … Si alguno
falla ⇒ parar y anotarlo». Al declarar `horas_extra_leidas` en las dos copias del ORM
(byte-idénticas, `cmp` sin diferencias) fallan los guardianes que fijan las columnas de
`parte_registros` en 56:

| Test | Qué afirma |
|---|---|
| `tests/test_f010_orm_models_gemelos.py::test_f010_r4_el_orm_canonico_tiene_las_tablas_y_56_columnas` | lista literal `COLUMNAS_PARTE_REGISTROS` (56) + `len == 56`; su comentario pide declararla ahí al añadir una columna |
| `tests/test_f010_orm_models_gemelos.py::test_f010_r29_parte_registros_no_gana_ni_pierde_columnas` | F-015 no toca la tabla: igual a la lista y 56 |
| `tests/test_f010_orm_models_gemelos.py::test_f019_r29_parte_registros_no_gana_ni_pierde_columnas` | F-019 no toca la tabla: igual a la lista |
| `services/partes-persistencia/tests/test_f015_r18_orm_empleado_jornada.py::test_f015_r18_parte_registros_no_gana_ni_pierde_columnas` | `len == 56` |
| `services/partes-persistencia/tests/test_f015_r21_hora_candef_intacto.py::test_f015_r21_parte_registros_sigue_teniendo_56_columnas` | `len == 56` |
| `services/partes-front/tests/test_f015_r18_orm_empleado_jornada_sv4.py::test_f015_r18_sv4_parte_registros_no_gana_ni_pierde_columnas` | `len == 56` |

Es inevitable con cualquier columna nueva (DA10): el guardián está hecho para obligar a
declararla. **Propuesta para el humano** (enmienda de design §5 y T1):

- **A (recomendada)**: añadir `"horas_extra_leidas"` tras `"horas_orig"` en
  `COLUMNAS_PARTE_REGISTROS` y pasar las cinco cuentas de 56 a 57 (textos «56» de sus
  mensajes y docstrings incluidos). La intención de los tests de F-015/F-019 («esa
  feature no tocó la tabla») se conserva: comparan con la lista vigente. Es lo que
  hicieron F-015 y F-019 con `TABLAS` al añadir sus tablas.
- B: guardar la traza fuera de `parte_registros` (otra tabla o JSON en el documento):
  contradice DA10 y complica sv4. No recomendada.

Estado del trabajo: T1 hecho salvo ese verde (dominio, dos ORM, `save_parte` y
`tests/test_f048_esquema.py` con fase RED registrada y ya en verde: 5 tests). Commit
`F-048 T1 (parcial)`. T2–T10 sin empezar. La campaña de F-046 sigue viva (7 procesos
`harness.mutacion` a las 18:10 del 2026-10-15), así que la mutación de F-048 esperaría
en cualquier caso.

### Antecedente: spec_ready

Spec escrita por el spec-author en `specs/F-048-solo-extras-en-laborable-como-jornada/`
(rama `feature/F-048-solo-extras-en-laborable-como-jornada`, worktree `partes-wt-f048`),
ya con la ampliación del humano del 2026-10-15 (filas con ordinarias Y extras: se suman).
sv3 (normalizador de la ingesta) + sv4 (ORM gemelo y etiqueta); columna nueva
`parte_registros.horas_extra_leidas`; rigor **crítico**. **Después de F-046 y F-047**
(T0 fusiona `dev`; conflictos pequeños: `orm_models.py` y `save_parte`).
Pendiente: PARADA 1 (el humano valida las DA antes de implementar).

**Decisiones abiertas que necesita validar el humano** (`design.md` §6):

- **DA2 · Mecanismo**: A (recomendado) = la ingesta suma las extras leídas > 0 de cada
  fila a su ordinaria y guarda lo leído en `horas_extra_leidas`; conciliador, F-045,
  F-037 y F-046 no cambian; casos 1 (10 ⇒ 8 + 2) y 2 (4 + 5 ⇒ 8 + 1) en dos líneas.
  B = marcar y convertir en cada pasada (reversible, umbral posible, pero el caso 2 exige
  un vínculo nuevo entre líneas que F-037 y F-046 no conocen).
- **DA3 · No laborable**: con A, mismos importes que hoy y una línea menos (4 + 5 en
  sábado ⇒ 0 + 9 `extra_auto`, hoy 0 + 4 + 5). «Como hoy» literal exigiría B.
- **DA4 · Sin umbral**: una fila solo extra que no llega a J sale con extra negativa
  (6 ⇒ 8 + (−2)), como las ordinarias; el umbral solo es posible con B.
- DA5 por fila (A ordinaria 8 + B solo extra 2 ⇒ 6,5+1,5 / 1,5+0,5); **DA6 sin
  retroactivo**: lo congelado como el caso 2 (ya en Sigrid) se propone como feature aparte
  sobre F-046 (solo `UPDATE`, extra a 0, nunca borrar); DA7 edición humana como hoy;
  DA8 extras negativas como hoy; DA9 mensuales MENC también se suman (no cambia Sigrid);
  DA10 traza en columna, rigor crítico.
- Los casos reales del 15/10 (0678) y del 02/10 (0686, registrado) no se arreglan solos
  al desplegar.

## F-049 · DONE 2026-10-23 (review APPROVED pasada 1; pendiente desplegar sv3 → sv4 y MANUAL M2–M8), APROBADA por el humano el 2026-10-20 (DA1–DA12 = A, DA13 = C): editor de celda de la matriz con ordinarias y extra siempre

**Cierre del implementer (2026-10-23)**: campaña de mutación completa (la lanzó el líder,
`--workers 1`): 164 mutantes, 162 muertos, 2 supervivientes, 0 timeouts, 44.292,9 s. Los dos
eran huecos reales y los mata un test nuevo cada uno, comprobado aplicando el mutante a mano
(`parte_repository.py:3229`, deshacer sin creadas da las afectadas;
`app.py:2245`, extra nueva sin recurso no consulta Sigrid); no se relanzó la campaña. T17
`3a2d296`; T18 informe completo en `progress/impl_F-049.md`; T19 `bash harness/init.sh` en
verde («ENTORNO LISTO»: sv4 `2583 passed, 1 skipped`, raíz `498 passed, 3 skipped`, COBERTURA
100 % de 362). **Review APPROVED (pasada 1, `progress/review_F-049.md`)**; fusionada en `dev`
el 2026-10-23. Falta: desplegar sv3 → sv4 y MANUAL M2–M8.

**Desbloqueada el 2026-10-22 por decisión del humano (opción A, respuesta literal «a»):** el
guardián de F-017 sube a 18 llamadas a `_actor(request)` y su docstring nombra la del editor de
celda (`POST /api/matriz/celda`, firma `solicitado_por`); el test entra en la lista cerrada de
design §3 (apartado c) y el `acceptance` de `features.json` lo recoge. Verificado con
`bash harness/init.sh` en verde tras `8d383e8` («ENTORNO LISTO»: sv4 `2581 passed, 1 skipped`
en 842 s; sv3 `2271 passed`; raíz `498 passed, 3 skipped`; COBERTURA 100 % de 362 líneas;
TAMAÑO design 250/250). Una primera pasada dio rojo solo por la PUERTA TAMAÑO (design.md
255 > 250): la lista cerrada se reflotó (mismo contenido; en (b), «afirma lo contrario de» →
«contradice» y el nombre nuevo abreviado como `…_marca_todo_documento_con_su_pedido`).
**Queda T17 SOLO a falta de la campaña de mutación, que lanza el líder** (no el implementer);
después T18 (informe completo con supervivientes) y T19 (portero).

Registro del bloqueo (historia): La campaña de mutación
(T17) abortó en la línea base: la suite de sv4 sin mutar tenía dos fallos, los dos guardas de
recuento de features anteriores. Uno resuelto sin tocar tests; el otro exige tocar un test
existente que **no** está en la lista cerrada de design §3 ni en el `acceptance` («tests
existentes intactos salvo los dos dobles…»), así que no se improvisa:

- `tests/test_f043_portal_fecha.py::test_f043_r19_r40_ninguna_recarga_nueva_salvo_actualizar`
  (cuenta `location.reload` = 23): **resuelto** en `4889e1e`, el editor recarga desde un solo
  sitio (`recargar()` dentro de `abrirPopupCelda`, que usa también el «Cerrar» de R37), como
  el popup de antes.
- `tests/test_f017_punto_unico.py::test_f017_todos_los_puntos_de_escritura_usan_el_helper`
  (cuenta `_actor(request)` = 17): **sigue en rojo con 18**. La llamada nueva es la de
  `POST /api/matriz/celda` (el actor firma el pedido de recálculo, `solicitado_por`, design
  §6); deshacer se dejó en una sola llamada (se calcula `actor` una vez al principio). No hay
  forma honrada de no llamar a `_actor` en una escritura nueva: saltarse el helper es lo que el
  propio test de F-017 R10/R11 prohíbe.
- Comprobado: suite entera de sv4 sin `-x` → `1 failed, 2580 passed, 1 skipped` (solo ese).

**Propuesta (recomendada)**: ampliar la lista cerrada de design §3 con ese test y pasar su
recuento a **18**, añadiendo a su docstring «y la de F-049 (`POST /api/matriz/celda`, que firma
el pedido de recálculo de la celda; deshacer reutiliza la llamada que ya hacía)», igual que se
enmendó para F-019 y F-042. Alternativa: que el POST no mande `solicitado_por` (el mensaje de
sv3 lo trae en las demás rutas; perdería la traza de quién pidió el recálculo). Con la decisión,
se retoma: test enmendado, campaña de mutación completa (`--workers` por defecto; si la base
paralela vuelve a fallar, `--workers 1`), informe y portero.

**Implementer (2026-10-21/22)**: lanzada por el humano («lanza f49»). Rama rebasada sobre `dev`
2bfeab7 (trae F-050, F-034, F-053 y F-014 retirada): conflictos solo en `harness/features.json`
(se conserva la entrada de dev, idéntica a la de la rama salvo la prioridad 4) y `BACKLOG.md`
(regenerado). Revisado `git diff ff2ed8e..dev` de sv4 y sv3: `worker_key_for_registro`,
`fila_para_alta_manual`, `_claves_de`, `_filas_reparto`, `ESTADOS_BLOQUEAN`, `data-reparto`,
`_exigir_sin_recalculo` y `marcar_terminado` de sv3 tienen la forma que supone el design §2.
T1–T16 hechas (un commit por tarea); **T17 parada** por el bloqueo de arriba (167 mutantes
en alcance). Informe parcial en `progress/impl_F-049.md`.

**Decisiones y desviaciones respecto a la spec (justificadas)**:

- `_pedir_recalculo_compartido` devuelve `(estado, pedido)` y no solo el estado (design §6):
  el INFO `[celda]` de R24 tiene que llevar el pedido.
- R14/R15 sobre la plantilla no se repiten aparte: la plantilla es siempre una de las líneas
  enviadas (R12 exige que sean exactamente las libres) y sus guardas ya corren; repetirlas
  sería código muerto (mutante equivalente).
- `nueva_extra` a 0 no crea y no es error (DA5, «una nueva a 0 no crea»); `nueva_ordinaria`
  ≤ 0 sí es 422 (R13 literal). La extra nueva admite negativos (rango −24…24 de DA10).
- Deshacer (R26): `document_ids` = partes de los snapshots **y de las creadas**; con una
  entrada que solo creó (E1) los snapshots están vacíos y su parte se quedaría sin recálculo
  (R27). `afectadas`, sobre las celdas actuales de las líneas de la entrada. Con todo
  congelado hoy, se recalcula igual el parte de la entrada.
- R20: la nueva clona también `partida` (la leída) además de `partida_*`; R21: el recurso
  para la hora extra es el de la plantilla con `empleado_reside` de respaldo (`_recurso_de`;
  la línea manual de F-050 solo lo trae ahí). Sigrid solo se consulta si se pide una nueva.
- `afectadas` va ordenada por (`obra_key`, `document_id`). El 409 de «celda vacía» de la ruta
  tiene la misma forma que el de `CeldaInvalida` (`{ok: false, error}`).
- JS: además de las puras de design §7, `abrirPopupCelda(td, cerrar)` y
  `mostrarAfectadas(pop, data)` van a dos espacios para probarlas en node; el IIFE pierde
  `patchHoras`/`crearExtra` (las rutas `PATCH` y `/extra` del servidor no cambian, R29).
- Simplificaciones para no dejar mutantes equivalentes: clave de la plantilla
  `(tipo != ORDINARIA, id)`, `validar_horas(..., nueva=False)` por defecto y `crear_extra ==
  0.0` en vez de `abs(...) < EPSILON`.
- T1: el `bash harness/init.sh` de T1 corrió a la vez que se editaba `parte_repository.py`
  (T4–T7) y sv4 cayó en `test_f050_r11_persona_de_sin_codigo_propio` (lee la fuente con
  `inspect` y los números de línea habían cambiado bajo sus pies); ese fichero, relanzado,
  57 passed. Raíz, sv1, sv2, sv3 y sv5 en verde en esa misma pasada. El portero final (T19)
  se lanza sin tocar nada.

### F-049 · verificaciones MANUAL (humano; design §10). NO ejecutadas.

Todo con F-049 fusionada en `dev`. **Despliegue** (lo lanza el humano, desde `infra/` con los
tres dot-source y el login de `infra/README_partes.md`), **sv3 antes que sv4**:

1. `.\redeploy_partes.ps1 -Solo sv3` → en su resumen, `ca-sv3-persistencia imagen=…:r<fecha
   de hoy>` y la revisión con el sufijo nuevo. Comprobar que está ACTIVA (KEDA mínimo 0: activa
   aunque no corra): `az containerapp revision list -n $($APPS['sv3']) -g $RG --query
   "[?properties.active].name" -o tsv` → solo la revisión nueva.
2. Solo entonces `.\redeploy_partes.ps1 -Solo sv4` → resumen con `ca-sv4-front` en la imagen
   nueva. Sin variables de entorno nuevas.

En el portal (Ctrl+F5), vista de una obra, matriz «Horas por día», doble clic en la celda:

- **M2**: celda con solo una extra de 10 (laborable) → filas «Extra 10» y «Ord. (nueva) 0»,
  nota de jornada → poner Ord. 8 y Extra 2, «Guardar» → recarga; tras la pasada de sv3
  (≤ 1 min, «Actualizar»), la celda dice `8+2` en **una sola fila** y en «Líneas del periodo»
  la ordinaria nueva tiene código de hora, la partida de la extra y su fila del papel.
- **M3**: celda con solo 8 → «Extra (nueva)» 2 → `8+2` estable tras la pasada.
- **M4**: pareja 8 + 2 «Extra (jornada)» → Extra 3 → `8+3` tras la pasada. Solo lectura en
  `partes`: `SELECT id, tipo_hora, horas, horas_orig, extra_auto FROM parte_registros WHERE id
  IN (<ids de la celda>);` → las dos con `horas_orig` NULL y `extra_auto` false, horas 8 y 3.
- **M5**: celda de un parte aprobado → solo lectura, sin «Guardar»; justo después de guardar
  otra celda del mismo parte (en espera), guardar otra vez → «✗ El parte se está recalculando
  (extras): espera a que termine.».
- **M6**: tras M2, «Deshacer» → la extra vuelve a 10 y la ordinaria creada pasa a la papelera.
- **M7**: un trabajador con horas el mismo día en dos obras: al abrir la celda, aviso «Este
  trabajador tiene horas ese día en otras obras (<código>)…»; al guardar, «Guardado. Este
  cambio recalcula también ese día en:» con el enlace a la otra obra; tras la pasada, la otra
  obra con su reparto nuevo (o, si estaba aprobada y `REPARTO_REAJUSTE` encendido, reparto
  pendiente de decidir).
- **M8**: en M7, solo lectura: `SELECT id, recalculo_pedido_id, recalculo_terminado_id FROM
  parte_documents WHERE id IN ('<parte de la celda>', '<parte de la otra obra>');` → mismo
  pedido en los dos y, tras la pasada, `recalculo_terminado_id` = ese pedido en los dos; en el
  log de sv3 UNA sola línea `[sv3-worker] recalculo motivo=edicion_celda document_id=<parte
  de la celda>` y una `recalculo terminado … marcado=True`.

Spec en `specs/F-049-editor-calendario-normal-y-extra/` (rama
`feature/F-049-editor-calendario-normal-y-extra`, worktree `partes-wt-f049`, rebasada sobre
dev). **sv4 y sv3** (sv3 solo `marcar_terminado`), sin esquema, sv5 ni Sigrid; rigor
**crítico** (DA9). Orden del humano: F-050 → **F-049** → F-014 → F-047; **no depende de
F-047**. Se implementa cuando F-050 esté en dev (T1 lo exige). Detalle en
`progress/spec_F-049.md`. **M1 superada el 2026-10-20** (popup de doble clic de la matriz
«Horas por día» de la vista de obra).

**Decisiones del humano (2026-10-20, citas literales en el chat con el líder)**: a la DA13,
«c»; a las demás, «apruebo las DA con los comentarios que te he hecho anteriormente» (los
comentarios: la confirmación de M1 y el caso de otras obras del mismo día). Recogidas en
design §12.

**DA13-C, otras obras del mismo día (design §8)**: la pasada de sv3 es completa y reparte por
(recurso, día) entre obras; otros días no cambian. sv4 avisa al abrir (R36) y tras guardar con
enlaces (R37) y escribe UN pedido compartido (uuid4) en los partes tocados y en los de otras
obras de ese día en una sentencia antes de publicar UN mensaje (R39); sv3 marca terminado todo
documento con ese pedido (R41: el UPDATE de `marcar_terminado` filtra solo por pedido, misma
firma; `despacho.py` y el mensaje no cambian). Compatible con F-042/F-043 y F-047 (R42). El
test `test_f043_r28_adaptador_solo_toca_su_documento` se invierte (lista cerrada, design §3).

**Para el humano al desplegar**: **sv3 antes que sv4** (`-Solo sv3`, comprobar que su revisión
nueva está activa, luego `-Solo sv4`); con sv4 nuevo y sv3 viejo los partes de otras obras
esperarían 10 min (vencido). Riesgo residual E12d: si la otra obra recibe otro pedido antes de
la pasada, espera a la de ese pedido; los datos quedan bien. M2–M8 manuales tras desplegar.

## F-045 · done (2026-10-14, APPROVED pasada 2), pendiente de M1, despliegue solo sv3 y M2: reparto ponderado de la jornada entre obras

**Cierre (2026-10-14)**: reviewer CHANGES_REQUESTED en la pasada 1 (4 cambios) y **APPROVED en la pasada 2** (`progress/review_F-045.md`). Campaña 3 de mutación: 84 mutantes, 76 muertos, 8 supervivientes equivalentes con demostración ejecutable (`progress/equivalentes_F-045.py`: 0 distintos). **El humano ACEPTÓ los 8 equivalentes el 2026-10-14** (respuesta literal «1, si»). M1 la midió el líder el 2026-10-14 (solo lectura): 5 grupos sin congeladas se reparten de nuevo (3 de varias obras, 2 de una), ninguno con congeladas.

**Desbloqueada el 2026-10-14 por decisión del humano (opción A, respuesta literal «a»);
descartadas B (sin vínculo extra↔base) y C (otro método de lectura).** Enmiendas:
design §4 (`LineaDia.extra_auto`/`base_id`; la lectura trae `horas_orig`, `extra_auto`,
`deleted_at_utc`, `line_index`, `empleado_line_no`), design §5 (se suma
`test_f037_revert.py::test_f037_r9_la_unica_clave_nueva_es_la_marca`, solo con las 5
claves nuevas), R27 y T4.

**Implementación terminada (implementer, 2026-10-14), T1–T13.** Informe:
`progress/impl_F-045.md`; mutación: `progress/mutacion_F-045.md` (82 mutantes, 73
muertos, **9 supervivientes justificados como equivalentes: pendiente de que el humano
acepte las justificaciones**, rigor crítico). R33 (candef 9, viernes J 6) añadido a
petición del humano. `azure-apps/partes.md` §3.3 con commit local en `azure-apps`.
Pendiente: reviewer.

**MANUAL (humano), pendiente**, solo lectura salvo el despliegue:

- **M1 · antes de desplegar**: SQL de `design.md` §9 en la base `partes` (grupos que
  F-045 reparte de nuevo, con y sin congeladas).
- **Despliegue solo de sv3**: `.\redeploy_partes.ps1 -Solo sv3` desde `infra/`.
- **M2 · tras desplegar**: Log Analytics de `ca-sv3-persistencia` con
  `Log_s has 'reparto'` (INFO de reparto y, si los hay, WARNING «reparto ideal», que dice
  cuántos días tocaría F-046); repetir la SQL de F-042 M1 sobre un día con dos obras sin
  aprobar y comprobar las cifras de §3.

Registro del bloqueo (historia): en T4, `test_f037_r9` (fuera de §5) afirmaba el conjunto
exacto de claves de `fetch_registros_para_recurso`, que R27 obliga a ampliar; y R25 necesitaba
enlazar la `extra_auto` congelada con su base, cosa que el `LineaDia` del design no llevaba.

## F-045 · spec_ready (2026-10-14): reparto ponderado de la jornada entre obras

Spec escrita por el spec-author en `specs/F-045-reparto-ponderado-entre-obras/`
(rama `feature/F-045-reparto-ponderado-entre-obras`, worktree `partes-wt-f045`).
Solo sv3, sin esquema ni Sigrid; rigor **crítico**. Pendiente: PARADA 1 (el humano
valida las DA antes de implementar).

**Decisiones abiertas que necesita validar el humano** (`design.md` §6 y §8):

- **DA1 · Partir en dos**: F-045 = reparto ponderado en sv3; **F-046** = reajuste
  en Sigrid de lo ya registrado con aviso al aprobar. Con solo F-045, el caso real
  (0678 ya registrada) sigue 0+8: lo arregla F-046.
- DA2 dos niveles (obra por sus horas, incluidas extras explícitas; luego líneas);
  DA3 también dentro de una misma obra; DA4 desempate (mayor resto, mayor peso, el
  que llegó antes); DA5 paso 0,5 con respaldo 0,25/0,01.
- **DA6 · Extras negativas**: se mantienen y se reparten en proporción (pregunta
  abierta del humano; alternativa: suprimirlas).
- DA7 congeladas en modo residual + WARNING de medición; DA8 incidencias sin
  cambios; **DA9 hallazgo**: las líneas en la papelera pesan hoy en el reparto (se
  sacan); DA10 concurrencia fuera.
- §8 (dirección de F-046, DA11–DA14): tabla `reparto_pendiente`, reajuste por HTTP
  síncrono a sv5 (`UPDATE hmores` nuevo, solo partes En registro), «Mantener lo
  registrado» si el parte está cerrado, candado consultivo en sv3.
- Tests existentes que cambian de cifras: lista cerrada en `design.md` §5.

## F-043 · done y DESPLEGADA (2026-10-13, sv3 r20261013185439 + sv4 r20261013185623), M1 hecha, pendiente de M2–M4: fecha del parte — rótulo, confirmación y parte «en espera»

**Despliegue (2026-10-13)**: el humano desplegó sv3 y después sv4 e hizo el push de `dev`.
Revisiones activas y sanas: `ca-sv3-persistencia--r20261013185439` y
`ca-sv4-front--r20261013185623`. **M1 hecha** (líder, solo lectura, base `partes`): las 4
columnas `recalculo_*` existen en `parte_documents`, `character varying`, nullables. El parte
de la página 1 de la 0694 vuelve a estar en el 01/10, con sus líneas ya registradas en Sigrid.

**Desbloqueada el 2026-10-13 por decisión del humano (opción A, respuesta
literal «a»).** design §6/§7 enmendado: el único test existente adaptable es
`test_f042_recalculo_fecha.py::test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo`
(su doble de DOM gana `window.confirm`, alcance, `activeElement` y las
funciones nuevas; cambian el orden de peticiones y los temporizadores; los
textos de `estadoRecalculo` no). `acceptance` ajustado en `features.json`.
Descartadas B (confirmación en otro manejador en captura) y C (sin R5). El
`getattr` de T3 queda validado por el coordinador. Lo que sigue es el
registro del bloqueo, conservado como historia.

**Implementación terminada (implementer, 2026-10-13), T1–T15.** Informe:
`progress/impl_F-043.md`; mutación: `progress/mutacion_F-043.md`.
`azure-apps/partes.md` actualizado (commit local `61d1688` en `azure-apps`).
Pendiente: reviewer.

**MANUAL (humano), pendiente** — solo lectura salvo el despliegue; las lanza
el humano, los agentes no:

- **Despliegue** (lo pide el humano), desde `infra/`, en este orden:
  `.\redeploy_partes.ps1 -Solo sv3` y después `.\redeploy_partes.ps1 -Solo sv4`
  (con sv4 antes, un sv3 viejo no marca y el parte espera hasta vencer a los
  10 min: inocuo). Si F-042 sigue sin desplegar, va en el mismo despliegue.
- **M1 · tras desplegar sv3 y sv4** (base `partes`):

  ```sql
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'parte_documents' AND column_name LIKE 'recalculo%';
  ```
  ⇒ 4 filas.
- **M2 · portal (Chrome/Edge)**, vista de obra con dos partes sin congelar:
  teclear la fecha no abre un diálogo por tecla; al salir del campo sale el
  texto con sus N trabajadores; Cancelar restaura; Aceptar ⇒ ese parte
  «recalculando…» y el otro se sigue editando, filtrando y desplazando; a
  los 1–2 min, tarjeta «Actualizar»; al pulsarla, misma posición y filtros
  con el reparto nuevo.
- **M3 · otra pestaña** con el mismo parte durante la espera ⇒ sale en espera
  (y una edición suya da «El parte se está recalculando (extras)…»).
- **M4 · base `partes`**, con el `id` del parte de M2:

  ```sql
  SELECT recalculo_pedido_id, recalculo_pedido_at_utc, recalculo_terminado_id,
         recalculo_terminado_at_utc FROM parte_documents WHERE id = '<id>';
  ```
  ⇒ `recalculo_pedido_id` = `recalculo_terminado_id`.


**Estuvo BLOCKED en T8 (implementer, 2026-10-13): la spec choca con un test
existente de F-042 que design §7 prohíbe tocar** («todos los tests
existentes; si uno se rompe ⇒ blocked, sin enmiendas previstas») y que el
`acceptance` de `features.json` exige mantener («sus tests siguen pasando sin
tocarlos»). T1–T7 hechas y en verde (commits `641c8cb`..`c5ca97f`); T8–T15
sin empezar. Nada en `static/app.js` está tocado.

El test: `services/partes-front/tests/test_f042_recalculo_fecha.py::
test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo`. Extrae
`wireFechaInput` (más `flashEl`, `setStatus`, `estadoRecalculo` y `MotivoHttp`)
y lo ejecuta en node con un DOM mínimo: llama a `inp.on.change()` y exige
(a) que la **primera** petición sea `PATCH /api/partes/doc-1/fecha`,
(b) que los temporizadores sean exactamente `["timer:1600", "timer:1800"]`
(o `["timer:1600"]` con `fallo`) y (c) no hay `window.confirm`,
`document.activeElement` ni ninguna función de F-043 en ese programa.

Lo que pide la spec para `wireFechaInput` es incompatible con eso, sea cual sea
la implementación:
- **R5**: con `change` sin foco se pide `GET …/alcance` y `window.confirm`
  **antes** del PATCH ⇒ la primera petición es el alcance (falla (a)) y
  `window.confirm` no existe en el doble (TypeError, node sale con error).
- **R18/R24 y design §4**: con `pedido`, `wireFechaInput` llama a
  `ponerEnEspera` + `vigilarRecalculo` (sondeo cada 5 s); con `fallo`, a la
  tarjeta fija ⇒ funciones no definidas en el programa extraído
  (ReferenceError) y un temporizador más (falla (b)).

La única forma de dejarlo en verde sin tocarlo sería detectar el doble
(p. ej. «si no hay `window.confirm`, guardar sin confirmar») o partir la
confirmación en otro manejador que intercepte `change` en captura y
re-dispare el evento: un apaño a medida del test o una arquitectura frágil
(orden de escuchas en el objetivo) que contradice design §4. No lo improviso.

**Opciones para el humano** (decide; el implementer no sigue sin respuesta):
- **A · Recomendada.** Enmendar design §6/§7 (como F-042 hizo con el guardián
  de F-017) para declarar adaptable ese único test: su doble de DOM gana
  `window.confirm` (acepta), respuesta del alcance, `activeElement` y las
  funciones nuevas en la lista extraída; **sus aserciones de textos de
  `estadoRecalculo` no cambian** (lo que F-042 R11 vigila de verdad), solo
  el orden de peticiones (alcance, luego PATCH) y los temporizadores del
  sondeo. Ajustar a la vez el `acceptance` «sus tests siguen pasando sin
  tocarlos» a «… salvo ese doble de DOM, enmendado».
- **B.** Dejar `wireFechaInput` como en F-042 (guarda sin confirmar) y
  poner la confirmación en un manejador aparte en fase de captura que corta
  el `change` y lo re-dispara tras aceptar; la espera y el aviso, en otro
  escuchador de la respuesta. Sin tocar el test, pero se aparta de design §4
  y depende del orden de escuchas del navegador.
- **C.** Renunciar a R5 (confirmación) en las filas: no recomendable, es la
  razón de ser de la feature.

Punto adicional para validar (no bloquea): en T3, `main_worker.py` pasa
`getattr(app.state, "recalculo_seguimiento", None)` porque el test existente
`test_f042_despacho.py::test_f042_r18_el_worker_despacha_los_dos_tipos`
simula `app.state` sin ese atributo; sin él el handler es el de F-042 (R31).


**Implementación en curso (implementer, 2026-10-13)** en el worktree
`partes-wt-f043`. Tarea en curso y decisiones: ver abajo «Bitácora del
implementer»; informe final en `progress/impl_F-043.md`.

Bitácora del implementer:
- T1–T7 hechas (esquema; adaptador y handler de sv3; estado, alcance, GET
  de estados, marca de pedido, guarda 409 y vistas de sv4). T8 estuvo
  bloqueada; T8–T15 hechas tras la opción A.
- Decisión T3: `main_worker.py` pasa
  `getattr(app.state, "recalculo_seguimiento", None)` y no el atributo a
  pelo: el test existente `test_f042_despacho.py::test_f042_r18_el_worker_despacha_los_dos_tipos`
  simula `app.state` sin ese atributo y design §7 prohíbe tocarlo; sin él,
  el handler es el de F-042 (R31).

Spec en `specs/F-043-fecha-del-parte-confirmar-y-recargar/` (rama y worktree
`partes-wt-f043`). El humano aprobó la spec el 2026-10-13 con una enmienda:
«tengo que seguir usando la plataforma para el resto de partes, solo queda en
espera el que está recalculando». Spec reescrita: **solo** el parte que sv3
recalcula queda en espera (filas marcadas y deshabilitadas; el servidor
rechaza sus ediciones con 409 salvo fecha y deshacer), el resto del portal
sigue usable y **nada recarga solo**: al terminar, una tarjeta ofrece
«Actualizar» (recarga conservando scroll y filtros). El estado lo pinta el
servidor (vale en cualquier pestaña) y vence a los 10 min. sv3 y el esquema
(4 columnas nullables en `parte_documents`) no cambian respecto a lo aprobado.

**Para el humano: revisar solo lo marcado en `design.md` §12** — DA6 y DA8
CAMBIADAS (sin recarga automática; deshacer conserva su recarga de hoy) y
DA10–DA13 NUEVAS (tarjeta «Actualizar» frente a refresco en el sitio; guarda
409 en el servidor; aprobación sin bloquear en F-043; espera pintada por el
servidor con vencimiento de 10 min). Respuesta a su pregunta: una edición a
mitad de pasada **sí se pisa** (sv3 lee, calcula y escribe después; design §9
R-a); el mismo riesgo existe hoy para cualquier parte en cada ingesta (R-g,
anterior a F-043, fuera de alcance). Punto de contacto con **F-044**: §10.

## F-042 · done y DESPLEGADA (sv3 r20261009161345, sv4 r20261009161525), M2 y M3 hechas: recalcular el reparto normal/extra al cambiar la fecha de un parte

**Cierre de verificaciones (líder, solo lectura)**: M2 vista en los logs el 2026-10-12 (sv4
pidió el recálculo a las 10:26:05 UTC y sv3 lo hizo a las 10:27:08 con `motivo=cambio_fecha`).
M3 el 2026-10-13: el humano no tiene rol de lectura de colas, así que se miró en Log Analytics
desde el 2026-10-09 14:00 UTC: en sv3, 3 líneas `recalculo`, **ninguna** `-> poison` (la escribe
`cola_cliente.py` al pasar un mensaje a la cola de poison) y ningún `ERROR`/`Traceback`. M1
queda superada: el parte del 01/10 está recalculado y registrado.

**Desbloqueada el 2026-10-09 por decisión del humano (opción A, respuesta literal «A»).**
Estuvo blocked en T4: el guardián
`services/partes-front/tests/test_f017_punto_unico.py::test_f017_todos_los_puntos_de_escritura_usan_el_helper`
cuenta `_actor(request)` en `app.py` (15) y F-042 añade dos firmas (guardar fecha, R1;
deshacer fecha, R7). Opción A: `design.md` §6 enmendado para declarar adaptable ese test,
que pasa a esperar **17** y nombra en su docstring los dos puntos de F-042; nada más
cambia en él. Descartadas B (no firmar el mensaje) y C (esquivar el recuento).


Spec en `specs/F-042-recalcular-extras-al-cambiar-fecha/` (rama y worktree
`partes-wt-f042`). sv4 publica `{"tipo": "recalcular", ...}` en
`q-persistencia` tras guardar (o deshacer) la fecha; sv3 lo distingue del
mensaje de sv2 por `tipo` y ejecuta `conciliar_todos` sin lógica nueva. Sin
variables ni roles nuevos: la identidad de sv4 (`id-partes-dev`) ya tiene
*Storage Queue Data Contributor* sobre la cuenta de colas (leído con `az role
assignment list` el 2026-10-09). Hallazgo: el reparto mal calculado se arregla
solo con la siguiente ingesta (toda pasada recalcula todo); F-042 cierra esa
ventana, en la que alguien puede aprobar y congelar el reparto viejo.

DA1–DA6 aprobadas por el humano el 2026-10-09 (las seis recomendadas). Riesgo
preexistente anotado (§8 R-b): pasadas concurrentes de sv3 con `maxReplicas=5`.

**Implementación terminada (implementer, 2026-10-09). Reviewer: APPROVED en la pasada 1** (`progress/review_F-042.md`, sin cambios requeridos).
Informe: `progress/impl_F-042.md`; mutación: `progress/mutacion_F-042.md`.
`azure-apps/partes.md` actualizado (commit local `be02869` en `azure-apps`).

**MANUAL (humano), pendiente** — solo lectura salvo el despliegue; las lanza el
humano, los agentes no:

- **M1 · antes de desplegar** (base `partes`, firewall abierto a mano por el
  humano): estado del parte de la obra 0694 del 01/10. Puede estar **ya
  arreglado** si después entró otro parte (cualquier ingesta recalcula todo):

  ```sql
  SELECT r.line_index, r.empleado_line_no, r.tipo_hora, r.extra_auto,
         r.horas, r.horas_orig, r.sigrid_estado, d.approved
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND d.obra_codigo = '0694' AND d.fecha_int = 20261001
    AND r.deleted_at_utc IS NULL
  ORDER BY r.line_index, r.empleado_line_no, r.extra_auto;
  ```

- **Despliegue** (lo pide el humano), desde `infra/`, en este orden:
  `.\redeploy_partes.ps1 -Solo sv3` y después `.\redeploy_partes.ps1 -Solo sv4`.
- **M2 · tras desplegar sv3 y sv4**: en el portal, volver a guardar la fecha
  01/10 de ese parte (si no está aprobado; si lo está, otro parte sin congelar)
  ⇒ «recalculando extras». A los 1–2 min, en Log Analytics:

  ```powershell
  $WS = az containerapp env show -n cae-partes-dev -g rg-partes-dev --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
  az monitor log-analytics query -w $WS --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv3-persistencia' | where Log_s has 'recalculo' | project TimeGenerated, Log_s | order by TimeGenerated desc | take 20"
  ```

  ⇒ una línea `[sv3-worker] recalculo motivo=cambio_fecha document_id=<el del
  parte>`. Repetir la SQL de M1: cada base con `horas` = jornada del jueves y
  su `extra_auto` con el exceso.
- **M3 · poison**:

  ```powershell
  az storage message peek --queue-name q-persistencia-poison --account-name stpartespt7m3 --auth-mode login --num-messages 32
  ```

  ⇒ ningún mensaje con `"tipo": "recalcular"`.

## F-040 · done y DESPLEGADA (2026-10-08, sv3+sv4 r20261008234617), M1 y M2 hechas, pendiente de M3: recursos sin DNI — proponer por nombre, alias por recurso, registrarlos

**Despliegue 2026-10-08 23:46** (humano: «si, haz las 2»): sv3 y sv4 `r20261008234617`; sv4
Healthy; sv3 KEDA a 0 hasta el próximo mensaje. M1 (23:42, solo lectura): 303 líneas, 33
congeladas, recurso igual 270/270; casado nuevo 10, otro recurso 1. M2: `empleado_alias`
con `empleado_ide` y `recurso_ide` nullable (YES/YES); 0 alias (nunca se usó ninguno).
Sigrid el 2026-10-08: MO/0032 y MO/0033 de Porsan ya tienen `res.cif`; 16 recursos persona
de Porsan con baja 20261008 (quedan 23 de alta); Ruesma 205 de alta (ayer 231).


**Implementación terminada (2026-10-08), pendiente de reviewer.** Desbloqueada
con la opción A del humano (`design.md` §8 enmendado; los tres tests de F-023
cambian solo lo esperado). T1–T13 hechas, `init.sh` en verde, cobertura 100 %
de 66 líneas, mutación completa 40/40 muertos (2 timeouts de sv4 comprobados a
mano). Informe: `progress/impl_F-040.md`; mutación: `progress/mutacion_F-040.md`.
`azure-apps/partes.md` actualizado (commit local `ec971c2` en `azure-apps`).

**MANUAL (humano), pendiente** — solo lectura salvo el despliegue; las lanza
el humano, los agentes no:

- **T14 · M1, antes de desplegar**: desde la rama, `cd
  services/partes-persistencia && ../../.venv/Scripts/python.exe
  medir_casado_recursos.py`; mirar `sin_dni`/`sin_dni_sin_ficha` por empresa,
  `casado_pierde_casado` y `casado_propone_sin_dni` (informe en `logs/`).
- **T15 · despliegue**, desde `infra/`: `.\redeploy_partes.ps1 -Solo sv3` y,
  después, `.\redeploy_partes.ps1 -Solo sv4` (sv5 no se despliega).
- **M2 · tras sv3** (base `partes`, solo lectura): `SELECT column_name,
  is_nullable FROM information_schema.columns WHERE table_name =
  'empleado_alias' AND column_name IN ('empleado_ide','recurso_ide');` ⇒
  dos filas, las dos `YES`.
- **M3 · tras sv4** (portal, Ctrl+F5): en Conciliar de Porsan, `MO/0032` y
  `MO/0033` salen «sin DNI»; al confirmar uno, su alias queda con
  `recurso_ide` y la línea en `recurso_manual`; el preflight de la obra 0692
  la da por verificada.

Bloqueada en T4, desbloqueada con la opción A; ver `impl_F-040.md`.

Spec en `specs/F-040-recursos-sin-dni-por-nombre/` (rama
`feature/F-040-recursos-sin-dni-por-nombre`, worktree `partes-wt-f040`).
Servicios: sv3 (casado, conciliador, alias, medición) y sv4 (catálogo con «sin
DNI», alias por recurso), más el esquema de `empleado_alias` (`recurso_ide`,
`empleado_ide` nullable, por `ddl_complementario`, sin `.sql`). **sv5 no
cambia**: ya escribe una línea sin DNI con recurso casado (existe, empresa,
alta); solo un test de caracterización (R22). Despliegue sv3 → sv4 tras la
medición M1.

**Decisiones del humano (2026-10-08)** (`design.md` §12): DA1 **propone**
(`nombre_sin_dni`, a Conciliar; el alias aprendido hace que la siguiente vez
case); DA2 **columna `recurso_ide`** en `empleado_alias` (aprobada); DA3 **no
acotar sv5** («si el recurso está casado, sv5 no deberá poner pega a que no
tenga DNI»; R23–R26 retiradas, sin gemela ni guardián nuevos); DA4 **no se
re-casa** (aprobada). Riesgo anotado (§11): sv5 no comprueba la persona en una
línea sin DNI; solo la acotan sv3 (R10) y el catálogo de sv4.

## F-039 · done y DESPLEGADA (2026-10-08, sv4 r20261008234617), pendiente de M1 (humano): nombre de la empresa en combos y Conciliar

Implementer en el worktree `partes-wt-f039` (rama
`feature/F-039-nombre-empresa-en-combos`). Decisiones del humano
(2026-10-08): todo aprobado, DA1 y R4.

**Desbloqueada el 2026-10-08 (opción A del humano).** El bloqueo: dos tests
ajenos de sv4 (`test_f015_r26_sin_fecha_las_claves_son_las_de_siempre`,
`test_f023_r40_endpoint_obras_anade_la_empresa`) comprueban las claves
EXACTAS de `/api/sigrid/empleados` y `/api/sigrid/obras`, y R12 prohibía
tocarlos. Enmienda: R12 (requirements y design §4) admite esa única
excepción; ambos tests añaden `empresa_nombre` a lo esperado, nada más.

- T1–T4 hechas (mutación: 3 mutantes, 2 supervivientes del `score`
  matados con un test; `init.sh` final en verde, cobertura 100 % de 6
  líneas). Informe: `progress/impl_F-039.md`. Siguiente: reviewer; luego
  merge, despliegue de sv4 y M1 (humano).
- Desviaciones: solo la enmienda de R12 (decisión del humano).

**Verificación MANUAL (humano), pendiente.** No toca Sigrid ni la base
`partes`: es solo mirar el portal.

- **M1 · MANUAL (humano)** — tras desplegar sv4
  (`.\redeploy_partes.ps1 -Solo sv4` desde `infra/`; el despliegue lo pide
  el humano, los agentes no lo lanzan):
  1. Abrir el portal y recargar sin caché (**Ctrl+F5**).
  2. **Conciliar** → en una tarjeta, «Buscar otro recurso» (búsqueda
     manual): cada resultado termina en «· Ruesma» o «· Porsan», **no** en
     «· empresa 1» / «· empresa 28».
  3. **«+ Nuevo parte»**: el combo de obra y el de trabajador muestran
     «· Ruesma»/«· Porsan» detrás de cada opción, no «empresa N».
  4. **«+ Añadir línea»** (modal del detalle de un parte): lo mismo en los
     combos de obra y de trabajador.
  Una empresa sin nombre en `NOMBRES_EMPRESA` se vería «· Empresa N».

## Integración F-035/F-036 (rama `chore/integracion-f035-f036`, 2026-10-07): terminada

Tercera copia del criterio recurso persona (`res.cla = 1`) en sv4
`sigrid_lookup_client.py::_SQL_RECURSOS_ACTIVOS` (F-035): casa con sv3/sv5
(`WHERE res.cla = 1`), sin cambios de comportamiento. Ahora la vigila
`tests/test_f036_recurso_persona_gemelos.py` y la nombra la lista cerrada de
`CLAUDE.md`. Informe: `progress/impl_integracion_F-035_F-036.md`. Pendiente:
revisión y merge a dev (humano).

## F-037 · done y DESPLEGADA sv3 (2026-10-07, r20261007223505), pendiente de M2–M4: sv3 no duplica la extra automática de una base omitida

**Desplegada** a petición del humano («A, despliega», 2026-10-07): solo sv3, revisión
`ca-sv3-persistencia--r20261007223505` (imagen sha256:5dc32ec0…). KEDA min 0: la limpieza
de los 7 duplicados ocurre en la primera pasada, al llegar el siguiente mensaje a q-persistencia.
M1 previa (regla de congelación entera): 0.

**Implementación en curso** (implementer, worktree `partes-wt-f037`). DA1, DA2 y
DA3 aprobadas por el humano el 2026-10-07 (las recomendadas). Matiz del humano:
con la extra de la pareja congelada el recálculo no genera ninguna extra, ni
siquiera transitoria; los tests de dos pasadas lo vigilan con
`extras_reclasificadas == 0` en cada pasada. Implementación terminada (T1–T10):
informe en `progress/impl_F-037.md`, mutación en `progress/mutacion_F-037.md`
(21/21 muertos). Review pasada 1: CHANGES_REQUESTED solo documental (comandos
exactos de M1–M4 aquí abajo); pendiente la pasada 2.

**Despliegue y verificación MANUAL (humano; design §8), pendientes.** Las
cuatro son de **solo lectura, base `partes`, las lanza el humano**; los
agentes no las ejecutan.

- **M1 · antes de desplegar** — debe dar 0 filas (regla de congelación entera:
  estado congelante **o** parte aprobado). Si sale alguna, un duplicado ya
  viajó a Sigrid: arreglo manual antes de nada (R7 no lo toca). **Hecho por el
  líder el 2026-10-07 en producción: 0 filas**; los 4 documentos con
  duplicados no están aprobados.

  ```sql
  SELECT r.document_id, r.line_index, r.empleado_line_no, r.fecha_int, COUNT(*)
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.extra_auto
    AND (r.sigrid_estado IN ('encolado','registrado','dedicacion') OR d.approved)
  GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1;
  ```

- Desplegar **solo sv3** (`infra/redeploy_partes.ps1 -Solo sv3`) cuando lo pida
  el humano; los agentes no lo lanzan.
- **M2 · tras la primera pasada de sv3** (R21) — debe dar 0 filas (antes, 7):

  ```sql
  SELECT r.document_id, r.line_index, r.empleado_line_no, r.fecha_int, COUNT(*)
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.extra_auto
  GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1;
  ```

- **M3 · logs de `ca-sv3-persistencia`** — «DUPLICADA(S) borrada(s)» sale una
  vez (7 ids) y no vuelve; «revisar a mano en Sigrid» no sale nunca. En
  PowerShell, con la sesión de Azure abierta (el workspace se lee del entorno,
  no se versiona):

  ```powershell
  $WS = az containerapp env show -n cae-partes-dev -g rg-partes-dev --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
  az monitor log-analytics query -w $WS --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv3-persistencia' | where Log_s contains 'DUPLICADA(S) borrada(s)' or Log_s contains 'revisar a mano en Sigrid' | project TimeGenerated, RevisionName_s, Log_s | order by TimeGenerated asc" -o table
  ```

- **M4 · informativo (DA3)** — bases ordinarias congeladas, recortadas
  (`horas_orig`) y sin ninguna `extra_auto` de su clave; se espera 0. Si sale
  alguna, se repone en una feature aparte con el dato en la mano:

  ```sql
  SELECT b.id, b.document_id, b.line_index, b.empleado_line_no, b.fecha_int,
         b.horas, b.horas_orig, b.sigrid_estado, d.approved
  FROM parte_registros b JOIN parte_documents d ON d.id = b.document_id
  WHERE d.is_active AND NOT b.extra_auto
    AND COALESCE(TRIM(LOWER(b.tipo_hora)), '') IN ('', 'normal')
    AND b.horas_orig IS NOT NULL
    AND (b.sigrid_estado IN ('encolado','registrado','dedicacion') OR d.approved)
    AND NOT EXISTS (
      SELECT 1 FROM parte_registros e
      WHERE e.extra_auto
        AND e.document_id = b.document_id
        AND e.line_index = b.line_index
        AND e.empleado_line_no IS NOT DISTINCT FROM b.empleado_line_no
        AND e.fecha_int IS NOT DISTINCT FROM b.fecha_int);
  ```

Spec en `specs/F-037-extras-duplicadas-base-omitida/` (spec-author), worktree
`partes-wt-f037`. Rigor crítico; **solo sv3**. Causa leída en el código:
`revert_extras_auto` respeta la extra congelada pero restaura su base no
congelada, y el cálculo de splits la vuelve a partir (el día cuenta la extra
congelada y las horas restauradas) → una `extra_auto` nueva por pasada. El
caso inverso (base `registrado`, extra no congelada) pierde la extra.
Arreglo: «pareja» = `(document_id, line_index, empleado_line_no, fecha_int)`;
base y extras automáticas se congelan juntas **para el recálculo de sv3**
(núcleo puro `pareja_extra.py`, reversión y lectura del repositorio,
`_congelado` del conciliador). La siguiente pasada borra sola los 7
duplicados (no congelados) y no los recrea. `esta_congelado` /
`congelacion.py` y la lista cerrada no cambian. Choques con F-036: solo
`tests/dobles.py` (bloques distintos) y las altas en backlog/progress.

**Decisiones abiertas para el humano (design §10):** DA1 solo sv3 sin tocar
la regla compartida de congelación (recomendado); DA2 limpieza automática en
la primera pasada tras desplegar, sin script (recomendado); DA3 bases
congeladas que ya perdieron su extra (M4): solo se cuentan, reposición en
feature aparte si hay alguna (recomendado). Antes de desplegar sv3: M1 (ningún
duplicado ya encolado/registrado); después: M2 = 0 parejas con > 1 extra.

## F-036 · done y DESPLEGADA (2026-10-08, sv3+sv5 r20261008102337), M1 hecha, pendiente de M2/M3: sv3 casa contra los recursos persona de la empresa del parte

**Despliegue 2026-10-08** (a petición del humano, «si»): sv3, sv5 y sv4 `r20261008102337`;
sv4 y sv5 Healthy y arranque sin errores; sv3 KEDA a 0 hasta el próximo mensaje.
M1 (2026-10-08 10:15, solo lectura contra producción, autorizada por el humano):
242 líneas activas, 33 congeladas, recurso igual 209/209 (P = 0); casado nuevo 4 y
otro recurso 2, todas Porsan (no se re-casa lo ingerido). Recursos persona de alta
sin DNI: Porsan 2, otras empresas 7; Ruesma 3 con cif distinto de la ficha.
Informe local `services/partes-persistencia/logs/medicion_casado_20261008-1015.md`.
F-037: aún sin pasada de sv3 (último parte 2026-10-07 12:10): M2 = 7 duplicados.


**Implementación terminada, pendiente del reviewer** (implementer, worktree
`partes-wt-f036`, rama `feature/F-036-casado-contra-recursos`, sin push).
DA1, DA2 y DA3 aprobadas por el humano el 2026-10-07 (las recomendadas).
Informe: `progress/impl_F-036.md`; mutación: `progress/mutacion_F-036.md`.
Intérprete: el `.venv` del repositorio principal (el worktree no tiene uno).

Toca **sv3** (casado contra recursos `res.cla = 1`, `res.cla` en el maestro,
retirada del respaldo F-030, herramienta de solo lectura
`medir_casado_recursos.py`) y **sv5** (`res.cla = 1` en `recursos_por_dni`);
**sv4 no cambia**, sin schema. Nueva entrada en la lista cerrada de `CLAUDE.md`
con guardián `tests/test_f036_recurso_persona_gemelos.py`.

**R6, opción A del humano (2026-10-07), ya implementada:** un DNI leído de
una persona que Sigrid conoce (ficha o recurso) sin ningún recurso persona
queda sin casar (`dni_sin_recurso`), sin alias ni nombre, y va a Conciliar
(sv4 ya lo trata como sin casar; sin tocar sv4).

**Desviaciones declaradas** (detalle en el informe): `dni_de_recurso` y
`ficha_enlazada` adelantados a T3; categoría extra `otro_recurso` en R26; la
herramienta no usa `SessionFactory` (crea la base si falta) y saca el DNI
leído del `raw_extraction_json`; R22 resultó de caracterización.

**Despliegue y verificaciones MANUAL: solo lectura, las lanza el humano** (los
agentes no despliegan ni consultan producción).

- **M1 · antes de desplegar** — medición de solo lectura (sigrid-api
  `/api/sql/read` y SELECT en `partes` en transacción READ ONLY), con el
  `.env` de sv3 en `services/partes-persistencia/`:

  ```powershell
  cd services/partes-persistencia
  ../../.venv/Scripts/python.exe medir_casado_recursos.py
  ```

  Imprime el resumen y deja `logs/medicion_casado_<fecha>.md` y `.csv`.
  Revisar `mo_no_persona` y `cif_distinto_ficha` (tabla por empresa) y
  apuntar **P = `recurso_cambia` + `recurso_pierde` + `recurso_gana`**: las
  líneas cuyo `recurso_ide` cambiará en la primera pasada del conciliador.

- **Despliegue** (el script ordena sv3 → sv5):

  ```powershell
  cd infra
  . .\00_vars_partes.ps1
  .\redeploy_partes.ps1 -Solo sv3,sv5
  ```

- **M2 · tras desplegar** — la primera pasada del conciliador de la revisión
  nueva de sv3 (la dispara el primer parte que entre):

  ```powershell
  $WS = az containerapp env show -n cae-partes-dev -g rg-partes-dev --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId -o tsv
  az monitor log-analytics query -w $WS --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv3-persistencia' | where Log_s contains '[recurso-concil] registros=' or Log_s contains 'recursos persona sin DNI' | project TimeGenerated, RevisionName_s, Log_s | order by TimeGenerated asc" -o table
  ```

  Esperado: en la revisión nueva, una línea `[matcher-provider] recursos
  persona sin DNI (no casan por nombre): N de M` y, en la primera
  `[recurso-concil] registros=… actualizados=…`, `registros` ≈ las líneas no
  congeladas de M1 (`lineas` − `congeladas`). `actualizados` cuenta todas
  las líneas que reescribe la pasada (también las que no cambian de
  recurso): la cifra comparable con **P** de M1 sale de M2b.

- **M2b · el recurso que cambió** (SQL de solo lectura en la base `partes`,
  tras la primera pasada): con el CSV de M1 a mano, para los `registro_id`
  marcados `cambia`/`pierde`/`gana` comprobar el recurso nuevo:

  ```sql
  SELECT r.id, r.document_id, r.empleado_reside, r.recurso_ide, r.parte_estado
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.id IN (/* registro_id de M1 con recurso cambia, pierde o gana */);
  ```

  Esperado: `pierde` ⇒ `recurso_ide` NULL y `parte_estado = 'sin_recurso'`;
  `gana`/`cambia` ⇒ `recurso_ide` no NULL.

- **M3 · un parte nuevo de Porsan (empresa 28) de la 0678** con un
  trabajador sin ficha `emp` (SQL de solo lectura en la base `partes`):

  ```sql
  SELECT d.id AS document_id, d.created_at_utc, r.line_index,
         r.empleado_match_method, r.empleado_ide, r.empleado_reside,
         r.recurso_ide, r.parte_estado
  FROM parte_documents d JOIN parte_registros r ON r.document_id = d.id
  WHERE d.is_active AND d.empresa = 28 AND d.obra_codigo = '0678'
    AND d.created_at_utc > '<fecha y hora UTC del despliegue, ISO>'
  ORDER BY d.created_at_utc DESC, r.line_index;
  ```

  Esperado: la línea del trabajador sin ficha con `empleado_match_method =
  'recurso_dni'`, `empleado_ide` NULL y `empleado_reside = recurso_ide`; y
  `parte_estado` `ok` (si ya hay parte `hmo` del mes) o `sin_parte`.

**Alineación con F-035 (para el líder):** F-036 aplica `res.cla = 1` (DA3) en
sv3 y sv5; F-035 debe usar el mismo criterio en sv4. Las dos tocan
`CLAUDE.md` (lista cerrada) y la semántica 12 de `ARCHITECTURE.md`: conflicto
de merge trivial al integrar.

## F-035 · done y DESPLEGADA (2026-10-08, sv4 r20261008102337), pendiente de T9 (humano): selectores de trabajador sobre recursos activos, por empresa

### Desbloqueada (2026-10-07): el humano eligió la opción (a)

Se añadió la ruta al guardián F-016 con comentario `F-035 (R5)` y la
excepción quedó anotada en R22; la desviación de `METODOS_RECURSO` quedó
aceptada y anotada en design §4. Se retoma en T5.

**Estado (implementer, 2026-10-07):** T1–T8 y T10 hechos; T9 es la
verificación MANUAL del humano en local (solo lectura). Informe en
`progress/impl_F-035.md`, mutación en `progress/mutacion_F-035.md`.

**Revisión 1 (CHANGES_REQUESTED, `progress/review_F-035.md`) aplicada:** bug
del callback de «Nuevo parte» (`e.` → `r.`) con test que ejecuta el callback
con node; reasignar a una ficha quita `recurso_manual`; `/api/sigrid/recursos`
responde `ok: false` si Sigrid nunca cargó. Pendiente de la pasada 2.

### T9 · verificación MANUAL (la lanza el humano; SOLO LECTURA, no aprobar nada)

Con el `.env` local (Sigrid configurado), desde la raíz del repo:

```
python services/partes-front/main.py
```

Abrir el portal en el navegador y pulsar **Ctrl+F5** (estáticos nuevos). Tres
comprobaciones:
1. **Conciliar** (`/conciliacion`): en una tarjeta con partes de Porsan el
   selector de empresa sale en «Porsan» y aparece como candidato el
   trabajador del caso F-030 (solo recurso, `MO/0037`); al cambiar a otra
   empresa se ocultan los candidatos de Porsan y la búsqueda manual filtra.
2. **Detalle de obra 0678 de Porsan** (`/obras/obr-<ide de la 0678 Porsan>`):
   el combo de trabajador de una línea solo ofrece recursos de Porsan (y en la
   0678 de Ruesma, solo de Ruesma).
3. **Nuevo parte** (`/nuevo`): al elegir obra, el selector de empresa toma su
   empresa y queda bloqueado; al elegir trabajador se rellenan categoría y
   horas sugeridas. El modal «+ Añadir línea» (desde una obra) igual. NO
   pulsar «Crear» ni «Añadir» contra la base real.

### BLOQUEO previo (implementer, 2026-10-07): test ajeno en rojo por R5

**Qué pasa.** R5 manda crear `GET /api/sigrid/recursos`. El guardián ajeno
`services/partes-front/tests/test_f016_vista_admin_jornadas.py::test_f016_r20_f016_no_anade_ni_cambia_ninguna_ruta_de_sigrid`
fija la lista CERRADA de rutas `/api/sigrid/*` (tipos-hora, obras,
empleados, partidas, comprobar) y falla con la ruta nueva. R22 prohíbe tocar
tests ajenos y la orden del líder es parar ante un test ajeno en rojo. La spec
no lo previó (design §2 no lista ese test).

**Opciones para el humano:**
- **(a) Recomendada:** añadir `("/api/sigrid/recursos", ("GET",))  # F-035 (R5)`
  a la lista de ese guardián, como hizo F-024 con `/api/sigrid/comprobar` (su
  docstring prevé exactamente eso: se amplía de forma explícita, no se afloja),
  y anotar en R22 la excepción. Una línea en un test ajeno.
- (b) Sacar el endpoint del prefijo (p. ej. `/api/recursos`): no toca el
  guardián, pero cambia R5 y esquiva la intención de la lista cerrada.

**Estado al bloquear.** T1–T4 hechos y comiteados (un commit por tarea), T5
con sus tests escritos en RED (commit `F-035 T5 (en RED)`), T6–T10 sin hacer.
Suite de sv4 tras T4: solo rojo el guardián F-016 y los tests de vistas de T5
(esperado). Ningún otro test ajeno afectado: comprobado que T5/T6 no chocan con
más guardianes (`_comboSimple` se seguirá reutilizando sin modificarlo, como
exige `test_f016_r20_el_js_cablea_el_combo_sin_tocar_el_componente`).
Informe parcial con las trazas RED en `progress/impl_F-035.md`.

**En implementación (implementer, 2026-10-07).** DA1 y DA2 APROBADAS por el
humano el 2026-10-07 (empresa bloqueada a la de la obra cuando hay obra;
ampliar la lista cerrada de `CLAUDE.md` con el filtro de alta del SQL de
recursos de sv4, vigilado por el guardián). DA3/DA4 como en la spec. Anotado
en design §8. Tarea en curso al bloquear: T5 (tests en RED, plantillas sin hacer).

**Desviación justificada (T3):** design §4 decía «`METODOS_RECURSO` incluye
`recurso_manual`», pero `test_f030_r18_metodos_de_recurso` (test ajeno de
F-030) fija ese conjunto a `{recurso_dni, recurso_nombre}` (es el espejo de la
constante de sv3) y R22 prohíbe tocar tests ajenos. Se cumple R13 sin tocarlo:
`METODO_RECURSO_MANUAL` + `_METODOS_CASADO_SIN_FICHA = METODOS_RECURSO |
{recurso_manual}`, que usan `esta_casado` y `_sin_casar_en_cola`. Mismo
efecto que pedía el diseño; `METODOS_RECURSO` sin cambios.

Nota del arranque: el primer `bash harness/init.sh` de la sesión cayó en
pytest de la raíz (`sF` hacia el 96 %, salida truncada) con el árbol limpio;
al relanzar `python -m pytest tests -q` dio 445 passed, 1 skipped. Parece
intermitente (había otro implementer trabajando en paralelo en
`partes-wt-f036`); se vigila en las siguientes ejecuciones.

Spec en `specs/F-035-selector-recursos-por-empresa/` (spec-author). Rigor
estándar. **Solo sv4** (+ guardián `tests/test_f023_de_alta_gemelos.py`,
`docs/ARCHITECTURE.md` y la lista cerrada de `CLAUDE.md`); sv3 y sv5 sin
cambios, sin schema. Hallazgos: los combos (Conciliar, Nuevo parte, modal
«+ Añadir línea», combo por línea del detalle de obra y «Reasignar a…» del
listado de trabajadores) tiran de `/api/sigrid/empleados` (`emp`); el detalle
de parte no tiene combo de trabajador propio (solo el modal). sv3 recalcula el
recurso de toda línea no congelada por DNI (ficha o `res.cif`) y empresa de la
obra, así que sv4 guarda los `empleado_*` + `empleado_reside` y suelta el
recurso (F-023 R42); una línea sin ficha se marca `recurso_manual` para salir
de la cola de Conciliar. Nuevo endpoint `/api/sigrid/recursos` con su SQL;
`/api/sigrid/empleados` se queda (lo usa la pantalla de jornadas).

**Decisiones (design §8, ya resueltas):** DA1 empresa bloqueada a la de la obra
cuando hay obra (recomendado); DA2 ampliar la lista cerrada de `CLAUDE.md` con
el SQL de recursos de sv4 vigilado por el guardián (recomendado); DA3 y DA4
**resueltas por el humano (2026-10-07)** y ya en la spec: persona = recurso de
clase persona (`res.cla = 1`, criterio de `porcentajes`), DNI = `res.cif` o, si
vacío, el de la ficha (`res.conide > 0`); el que siga sin DNI no se ofrece. El
casado de sv3 con ese criterio es F-036 (otra spec). T9 es verificación
manual del humano en local, solo lectura.

## F-033 · done (2026-10-07): columna Empresa en el listado de obras

APPROVED del reviewer (pasada 1, `progress/review_F-033.md`). Resumen en `history.md`.
**Desplegada** (2026-10-07, a petición del humano): solo sv4, revisión
`ca-sv4-front--r20261007151555`, Healthy, arranque sin errores en Log Analytics.
Pendiente: verificación manual: abrir
`/obras`, ver la 0678 en dos filas «Ruesma» / «Porsan» y probar el filtro de
empresa (Ctrl+F5).

## F-032 · blocked (2026-10-07): activar Sesame en producción (solo festivos)

**Bloqueada por decisión del humano (2026-10-07, «bloquea esta»)** para atender
incidencias. Pendiente al retomar: P0 (`.env` de sesame-api publicado en GitHub,
rotar token) y visto bueno de DA1–DA10. La spec no cambia.

Spec en `specs/F-032-sesame-festivos-produccion/` (spec-author). Rigor
estándar. Toca sv3, sv4, `infra/` y `azure-apps/partes.md`; **sesame-api y
Azure los hace el humano** (design §2 y §7). Hallazgos: la integración F-003
ya está entera y apagada; los scripts `create_*` ya cablean `SESAME_*` pero
solo al crear la app (falta `add_sesame_partes.ps1`); cada mensaje de sv3
recalcula TODOS los partes activos no congelados, así que encender = recálculo
inmediato; hoy los respaldos difieren (sv3 nacionales, sv4 Madrid); una lista
vacía de Sesame se toma hoy por «sin festivos» (borraría los nacionales).

**Bloqueante de seguridad en sesame-api (P0):** su `.env` está versionado y
publicado en GitHub (`origin/dev`, `origin/pruebas`; commits `d226936`,
`dcef288`). No se ha leído. El humano debe sacarlo del índice y, si lleva
`SESAME_TOKEN`, rotarlo antes de cargarlo en el Key Vault.

**Decisiones abiertas para el humano (design §8):** DA1 sesame-api en
`cae-partes-dev` con ingress interno y secretos en kv-partes (recomendado) vs.
recursos propios con ingress externo; DA2 1 réplica fija; DA3 script de
encendido/apagado; DA4 mantener los dos niveles de F-003 (bloqueo del registro
incluido) en vez de «solo respaldo + log»; DA5 calendario con < 8 festivos ⇒
degradado (en el cliente gemelo); DA6 herramienta de contraste en sv3;
DA7 recálculo automático de lo no congelado, lo congelado solo se informa;
DA8 `/jornada` responde 502 sin contratos (arreglar en sesame-api); DA9
`azure-apps/sesame-api.md` lo escribe su dueño; DA10 rigor estándar.
Nota: en local el puerto 8006 lo usa hoy `porcentajes-transfer`.

## F-031 · done y DESPLEGADA (2026-10-06): el parte registrado acaba en el asiento analítico

APPROVED del reviewer en la pasada 2 (`progress/review_F-031.md`). Resumen en
`progress/history.md`. Despliegue COMPLETO a petición del humano («despliega
de forma completa con escritura total»): sv1-sv5 `r20261006173128` (orden
sv2 -> sv3 -> sv5 -> sv4 -> sv1), todas Healthy, 0 errores en Log Analytics;
sv5 en escritura real (`OBRA_PRUEBAS_FORZAR=false`), `MENSUALES_A_DEDICACION`
sin definir (apagado). Pendiente: aviso a porcentajes (texto abajo) y la
primera escritura controlada en real (modal en solo lectura, luego una
persona y un día).

### Spec v5 escrita (spec-author, 2026-10-06), pendiente de visto bueno

Decisiones del humano: «si, amplia la spec» y «lo de no pisarse con
porcentajes vale para una insercion normal no solo complementaria». La v5
añade el **alta protegida** frente a `porcentajes` (dedicacion-transfer,
F-037), que escribe en el MISMO parte de Sigrid: R40–R47 y design §13 (SQL
idéntico al suyo, relectura del periodo y uso del parte En registro que
haya, un reintento, error sin líneas) y la dependencia documentada
(R48–R49: cabeceras, `ARCHITECTURE.md`, `azure-apps/partes.md`; NO entra en
la lista cerrada de `CLAUDE.md`). Tareas nuevas T21–T32 (incluye repetir la
mutación completa, T31). La v4 (T1–T20) sigue implementada y sin review.
Resumen y decisiones en `progress/spec_F-031.md`.

**Decisiones abiertas para el humano (antes de T21):** DA9 diseño del alta
(usar el parte del otro servicio; `creado` por filas insertadas; aviso sin
recalcular); **DA10** adaptar dos tests ajenos de F-023 (`r32` a
`parameters[:6]`, `r34` a «contiene»); **DA11** la cabecera nueva pone en
rojo `porcentajes/.../test_f037_copias_partes.py::…ref_vigilada` hasta que
`porcentajes` recopie: aviso a `porcentajes` en el mismo trabajo (no se
edita desde aquí). Manual nueva: **M6** (design §11), tras desplegar sv5 y
dedicacion-transfer.

**Desbloqueada por decision del humano (2026-10-06, «si»)**: se cambia solo
el token `"partes_existentes"` por `"partes_del_periodo"` en el assert de
`test_f002_r20_el_estado_escrito_se_lee_dentro_del_lock` (desviacion D1 del
informe). Lo de abajo es el historico del bloqueo.

### (historico) bloqueo en T12

**Motivo del bloqueo (spec incorrecta en un punto, no improviso).** Al
implementar T12 (paso 5 con `partes_del_periodo`, design §7.4) se pone ROJO
un test AJENO: `services/partes-transfer/tests/test_f002_pipeline_fases.py::
test_f002_r20_el_estado_escrito_se_lee_dentro_del_lock`, que exige por
NOMBRE que el pipeline llame a `partes_existentes`:

    assert {"partes_existentes", "siguiente_cod_pt", "lineas_por_synckey",
            "escribir"} <= set(cli.llamadas)

Con F-031 el pipeline ya no llama a `partes_existentes` (lo sustituye
`partes_del_periodo`, que el doble tambien vigila bajo el lock). design §8
afirma que ningun test ajeno cambia y tasks.md manda parar si uno se pone
rojo. Sin alternativa limpia: seguir llamando a `partes_existentes` seria
una lectura extra por periodo solo para el test (contra R1), y que el doble
apunte `partes_existentes` al llamar a `partes_del_periodo` enganaria al
guardian.

**Propuesta (decide el humano):** cambiar en ese assert el nombre
`"partes_existentes"` por `"partes_del_periodo"` (un token; la intencion de
R20 de F-002, leer el estado escrito DENTRO del lock, se mantiene y la
comprueba `vigilar_lock`). Se declararia como desviacion D1 en el informe.

**Estado del trabajo:** T1-T11 hechas y commiteadas (un commit por tarea).
T12 IMPLEMENTADA en el arbol de trabajo SIN commitear (`registro_pipeline.py`
pasos 5, 7, 8 y docstring; `settings.py` con `EST_PARTE_CERRADO`/
`EST_PARTE_IMPUTADO`) y el arreglo del helper `_lin` de
`test_f031_pipeline_estado.py`: suite sv5 463 passed, 1 failed (solo ese
test ajeno); suite raiz 445 passed, 1 skipped. Con el visto bueno se cambia
el token, se commitea T12 y se sigue con T13-T20 (sv4, herramienta, docs,
mutacion). Si la decision es otra, `git checkout` de esos dos ficheros
deja la rama en T11.
Trazas RED de T3-T11 (salida real) en `progress/red_F-031.md`.


**Spec v4 APROBADA por el humano el 2026-10-06** («aprobado, se refiere a lo
que no este en registro»): «cerrado» = Cerrado o Imputado. Rama al día con
`dev` (F-029 y F-030 incluidas). Pasa al implementer.

Spec en `specs/F-031-asiento-analitico/`, resumen en `progress/spec_F-031.md`
(rama `feature/F-031-asiento-analitico`). Hallazgo: Sigrid ya genera el
asiento al «Contabilizar parte» (estado Imputado); sv5 no escribe asientos,
no escribe en partes cerrados. Spec v4 (2026-10-05): DA1/DA2 → parte
complementario (las líneas van a un parte En registro de la obra y mes; si
no hay, sv5 crea uno; el cerrado no se toca) y DA6 → la cuenta sale del
recurso (F-021), con la partida `CI/CD` solo de respaldo. DA6-e retirada.
Pendiente fuera de la feature: DA3 con Juan (borrador en Outlook).

### Implementacion (implementer, 2026-10-06)

- T1 hecha: caracterizacion en verde contra el codigo de hoy
  (`test_f031_pipeline_estado.py`: R4, R6, R10, R32, R33;
  `test_f031_pipeline_cuenta_partida.py`: R20, R22) y suite `f021` en verde
  (66 passed, R27).
- T2 hecha: `dobles.py` crece (partidas, `partes_del_periodo`,
  `partidas_de_lineas`, fallos inyectables, `partes_existentes` con el de
  mayor `ide`, `SettingsFake` 1/3/10). Suite sv5: 370 passed.
- T3 hecha: `test_f031_estado_parte.py` en ROJO (modulo inexistente);
  traza para el informe. Textos de aviso y motivo en ASCII sin tildes, como
  el resto de mensajes de sv5 (decision, no cambia el sentido de design §7.1).
- T4 hecha: `ParteSigrid`, `PartidaCuenta`, campos nuevos de
  `ParteDestino`/`AccionLinea` y `estado_parte.py`. T3 en verde (15).
- T5 hecha: `test_f031_cuenta_partida.py` en ROJO (ImportError).
- T6 hecha: `subcuenta_de_partida`, `OrigenSubcuenta`, `origen_subcuenta`
  y docstring (R7 de F-021 matizada). T5 + `test_f021_cuenta_analitica` en
  verde (60); suite sv5 410 passed.
- T7 hecha: `test_f031_cliente_partes.py` en ROJO (11 failed).
- T8 hecha: `partes_del_periodo` y `partidas_de_lineas` en el cliente
  (`partes_existentes`, `stmts_crear_parte`, `lineas_existentes` intactos).
  T7 en verde; suite sv5 421 passed.
- T9 hecha: tests de pipeline de la cuenta en ROJO (11 failed, 7 passed:
  las caracterizaciones y las guardas de «no leer»).
- T10 hecha: `_resolver_cuentas` con respaldo de partida y log `origen
  cuenta`. Corregido de paso el docstring que decia que la cola reintenta
  (observacion O1 del reviewer de F-021). T9, T1 y suite sv5 en verde (437).
- T11 hecha: tests de pipeline del parte en ROJO (22 failed, 11 passed:
  caracterizaciones de T1 y guardas que ya cumple el codigo de hoy).
- T12 hecha: `settings.py` (`EST_PARTE_CERRADO`, `EST_PARTE_IMPUTADO`) y
  pasos 5, 7 y 8 del pipeline. D1 aplicada en `test_f002_pipeline_fases.py`.
- T13 hecha: `test_f031_preflight_avisos.py` (sv4) en ROJO (11 failed; el
  reenvio y el modal de siempre, R30, ya en verde).
- T14 hecha: `app.js` (rotulo «complementario» + aviso escapado por parte;
  `notasCuentaHtml`). **Decision D2**: con `notasCuentaHtml` a nivel de
  modulo se ponia ROJO un test AJENO (`test_f022_vistas_seleccion.py::
  test_f022_r27_js_seccion_por_obra_con_resumen_y_listado`, que ejecuta
  `resumenHtml` con una lista cerrada de funciones); se define DENTRO de
  `resumenHtml` (solo la usa ella) y ningun test ajeno cambia. T13 se
  ajusto a eso y su RED se volvio a sacar. `node --check` OK; sv4 1672 passed.
- T15 hecha: `test_f031_comprobar_asiento.py` en ROJO (modulo inexistente).
- T16 hecha: `comprobar_asiento_analitico.py` (solo `_read`); T15 en verde
  (19). **Desviacion D3**: M1 y M2 NO se ejecutan (tasks.md T16 lo pedia al
  implementer, pero el encargo del lider manda dejar las MANUAL documentadas
  sin ejecutarlas); comandos en la lista MANUAL de abajo.
- T17 hecha: `docs/ARCHITECTURE.md` (semantica 13 matizada, 16 nueva,
  herramienta) y `partes-proyecto.md` §3.5.
- T18 hecha: `azure-apps/partes.md` §3.5, commit local `ef43cac` (sin push).
- T19 hecha: cobertura de lineas cambiadas 98,7 % (225/228). Mutacion
  completa (6 workers, timeout 600): campana 1 126/103/23 supervivientes;
  cerrados con `test_f031_mutantes.py` (y dos `or 0` muertos quitados);
  campana 2: 122 mutantes, 122 muertos, 0 supervivientes
  (`progress/mutacion_F-031.md`).
- T20 hecha: `bash harness/init.sh` en VERDE (raiz 445 passed/1 skipped,
  sv5 503, sv4 1672, cobertura 99,6 %). Informe en `progress/impl_F-031.md`.
  Pasa al reviewer.

#### v5 (alta protegida y dependencia con porcentajes; spec `9ea7c59`)

- T21 hecha: `test_f031_pipeline_alta.py`, caracterizacion de R40 en verde
  contra el codigo de hoy (3 passed).
- T22 hecha: `dobles.py` crece (`alta_protegida`, `al_alta`, `altas`);
  suite sv5 506 passed.
- T23 hecha: `test_f031_cliente_alta.py` en ROJO (5 failed; el `TypeError`
  sin empresa ya en verde).
- T24 hecha (DA10, visto bueno del humano 2026-10-06): en
  `test_f023_escritura_empresa.py`, `r32` compara `parameters[:6]` y `r34`
  exige que el SQL del `hmo` CONTENGA el filtro por codigo, tipo y empresa.
  Verde contra el codigo de hoy (54 passed).
- T25 hecha: `stmts_crear_parte` con el alta protegida. Comparado por AST
  con `git -C ../porcentajes show 40b9feb:services/dedicacion-transfer/infrastructure/sigrid/sigrid_write_client.py`:
  las dos sentencias con SQL y parametros identicos. T23 y F-023 en verde.
- T26 hecha: carreras (R43-R47) y R9 reescrito a R43/R45, en ROJO (9
  failed; el alta propia sin carrera ya en verde).
- T27 hecha: `_crear_parte` (alta, relectura con `elegir_parte`, un
  reintento, error) y docstring del paso 8; suite sv5 520 passed (guardas
  de carrera de F-002 incluidos).
- T28 hecha: cabecera de dependencia (solo docstring, +9 lineas cada uno)
  en `estado_parte.py` y `cuenta_analitica.py`, commit `e85ef0e`. Suite sv5
  520 passed. **DA11**: el test de copias de `porcentajes` se pone ROJO
  hasta que recopien (aviso de abajo; no se edita `porcentajes` desde aqui).

#### AVISO PARA `porcentajes` (DA11; texto exacto para que el humano lo pase)

> **Aviso de `partes` (F-031 v5) para `porcentajes` (F-037).** En la rama
> `feature/F-031-asiento-analitico` de `partes` han cambiado los dos
> ficheros que copiais literalmente:
> `services/partes-transfer/application/services/estado_parte.py` y
> `services/partes-transfer/application/services/cuenta_analitica.py`.
> **Que cambia:** SOLO el docstring de cabecera de cada uno: se anade un
> parrafo «DEPENDENCIA CON `porcentajes`» (9 lineas) que dice que son copia
> literal vuestra y que cambiarlos obliga a avisaros en el mismo trabajo.
> Ninguna regla ni linea de codigo cambia (`git diff 9b202e9 e85ef0e` de
> esos dos ficheros: 18 inserciones, 0 borrados, todas dentro del
> docstring). Por eso vuestro
> `services/dedicacion-transfer/tests/test_f037_copias_partes.py::test_f037_copia_igual_a_la_ref_vigilada`
> esta en ROJO: es «texto, se recopia» (vuestro design §12).
> **Que hacer:** recopiar los dos ficheros desde
> `git -C ../partes show e85ef0e833f01f69ff25cd2937dee1e703a03fd3:services/partes-transfer/application/services/<fichero>`
> y poner `COMMIT_COPIADO = "e85ef0e833f01f69ff25cd2937dee1e703a03fd3"`.
> Ese commit es el ultimo de la rama que toca los dos ficheros y sigue
> siendo valido cuando F-031 se mergee a `dev` (merge, no squash); en ese
> momento, `REF_VIGILADA` pasa a `dev` como ya preve vuestro test. Ademas,
> el alta del parte (`stmts_crear_parte`) de `partes` es ahora texto y
> parametros identicos al vuestro de `40b9feb` (alta protegida): si lo
> cambiais, avisad igual.

- T29 hecha: `docs/ARCHITECTURE.md` (semantica 16: alta protegida, parte
  compartido, copias, aviso obligatorio, fuera de la lista cerrada) y
  `partes-proyecto.md` §3.5.
- T30 hecha: `azure-apps/partes.md` §3.5 (alta protegida) y «que se rompe
  si cambia» (copias y alta con `porcentajes`), commit local `b09865f` (sin
  push).
- T31 hecha: mutacion campana 3 completa (6 workers, timeout 600): 129
  mutantes, 129 muertos, 0 supervivientes (`progress/mutacion_F-031.md`).
- T32 hecha: `bash harness/init.sh` en VERDE (raiz 445 passed/1 skipped,
  sv5 520, sv4 1672, cobertura 99,6 %); M6 anotada abajo; informe
  actualizado en `progress/impl_F-031.md`. Pasa al reviewer.
- T33 hecha (pasada 2 del reviewer): test de R40 con dos sentencias reales
  en una sola escritura (`c9871c8`, RED con la rotura en copias fuera del
  repo) y dos frases de docs alineadas con R43-R45 (`56e4caf`). Sin codigo
  de produccion: no se repite la mutacion. init.sh en VERDE. Vuelve al
  reviewer.

### F-031 · verificaciones MANUAL (humano; design §11). NO ejecutadas.

Despliegue (lo pide el humano): `.\infra\redeploy_partes.ps1 -Solo sv5` y
despues `.\infra\redeploy_partes.ps1 -Solo sv4` (aditivo; sin variables
nuevas obligatorias: `EST_PARTE_CERRADO`=3 y `EST_PARTE_IMPUTADO`=10 por
defecto). Rollback: imagen anterior.

- [x] **M0**: hecho por el humano el 2026-10-06 («cerrado» = no En registro).
- [ ] **M1 (solo lectura)**, desde `services/partes-transfer` con su `.env`:
  `../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra 0696 --ano 2026 --mes 1`
  Esperado: `PT26/00004 · Imputado · 308 linea(s)` y `asiento ANA26/00017: cuadra`.
- [ ] **M2 (solo lectura)**: igual con `--empresa 1 --obra 0404 --ano 2026 --mes 7`.
  Esperado: `PT26/00296 · En registro · 0 linea(s)` y sin linea de asiento.
- [ ] **M3 (produccion, sin escribir)**, tras desplegar sv5 y sv4 (Ctrl+F5):
  abrir el modal de aprobacion de lineas de agosto de una obra con partes
  Cerrados y **Cancelar**. Esperado: el parte rotulado «complementario»,
  codigo nuevo `PT26/…` «se creara» y el aviso que nombra el parte
  cerrado; en los logs de `ca-sv5-transfer`, `[registro] parte obra=…
  complementario=si`.
- [ ] **M4 (modo pruebas, obra 0404; solo si el humano lo autoriza)**: con
  PT26/00296 pasado a Cerrado por Administracion, aprobar en modo pruebas
  (`OBRA_PRUEBAS_FORZAR=true`) ⇒ complementario nuevo En registro con las
  lineas; comprobar con M2 y limpiar con
  `python .\prueba_escritura_sigrid.py limpiar --ejecutar`.
- [ ] **M5**: tras el primer «Contabilizar» de un complementario, M1 sobre
  su obra y mes ⇒ `cuadra` en el original y en el complementario.
- [ ] **M6 (v5, solo lectura, tras desplegar sv5 y el `dedicacion-transfer`
  de `porcentajes`)**: por una obra y mes con lineas de ambos servicios,
  `../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra <COD> --ano <AAAA> --mes <M>`
  (desde `services/partes-transfer`) lista UN solo parte `En registro`; en
  los logs de `ca-sv5-transfer`, `[registro] alta obra=<COD> … parte=propio`
  u `otro servicio`. Antes de desplegar, `porcentajes` tiene que haber
  recopiado (AVISO DA11 de arriba).

## F-030 · done y DESPLEGADA (2026-10-05), pendiente de M3 y M4

Desplegada a petición del humano: sv3 `ca-sv3-persistencia--r20261005180501`
(Running, esquema y alias 1, 28 cargados sin error = M1) y después sv4
`ca-sv4-front--r20261005180700` (100 % del tráfico, arranque limpio).
M3 (reprocesar los 2 partes de Porsan) en manos del humano: papelera en el
portal y correos de vuelta a la bandeja de partes@.

APPROVED del reviewer en la pasada 2 (`progress/review_F-030.md`; la pasada 1
pidio un test de cableado, T16 `88140da`). Resumen en `progress/history.md`.

**Desbloqueada por el lider (2026-10-05)**: retirado el worktree de F-031
(su spec queda en la rama `feature/F-031-asiento-analitico`, `b3a5cfd`);
`bash harness/init.sh` en VERDE (raiz 445 passed, cobertura 100 % 59/59,
tamano OK). Pasa al reviewer. Leccion: un worktree dentro del repo rompe el
guardian de `.sql` de F-017; los worktrees de agentes, fuera del repo.

**Implementacion TERMINADA (T1-T15), bloqueada SOLO por el portero**:
`bash harness/init.sh` final (HEAD `24a8448` + informe) da todo en verde
(sv3 754, sv4 1657, sv5 362, cobertura 100 % 59/59, tamano OK) salvo 1
test de raiz por causa AJENA (ver «Init en rojo» abajo). Informe en
`progress/impl_F-030.md`; mutacion 18/18 muertos. Para desbloquear: que se
retire el worktree `.claude/worktrees/agent-af837e18a30df3345` (F-031) y
relanzar `bash harness/init.sh`; si sale verde, F-030 vuelve a
`in_progress` y pasa al reviewer. Sin desviaciones de la spec.

Spec en `specs/F-030-recurso-sin-ficha/` (requirements 116/150, design
232/250, 15 tareas), **version 2**: reescrita con las decisiones del humano
del 2026-10-05; DA1-DA9 APROBADAS (design §8). Resumen llano y cambios
respecto a la v1 en `progress/spec_F-030.md`. Rama
`feature/F-030-recurso-sin-ficha`. Rigor critico.

- sv3: DNI canonico a 8 digitos (en `parte_normalizer.py`); «fichas de
  recurso» (MO/ con `res.cif`, sin ficha por DNI ni `conide`) casadas con el
  MISMO proceso que las de empleado (DNI, alias solo de empleados, nombre con
  las dos juntas); metodos `recurso_dni`/`recurso_nombre`; sin columnas.
- sv4 al minimo: `esta_casado` + fuera de la cola de conciliacion.
- sv5 sin codigo (tests: verificacion y cuenta 0 en la 28).
- **Implementado** (T1-T13, un commit por tarea, HEAD en la rama): ver
  `progress/impl_F-030.md`. Lista cerrada, `text_match.py` y sv5 sin
  tocar (T10). `azure-apps/partes.md`: commit local `1c7238c` (sin push).
- **Init en rojo por causa AJENA a F-030** (2026-10-05, tarde): el test de
  raiz `tests/test_f017_r22_sin_reescritura_historica.py::
  test_f017_r22_no_hay_ficheros_sql_de_migracion` hace `rglob("*.sql")`
  sobre TODO el repo y encuentra
  `.claude/worktrees/agent-af837e18a30df3345/infra/sql/01_dedicacion_lectura.sql`:
  el worktree (bloqueado, `locked`) de OTRO agente que esta escribiendo la
  spec de F-031 (rama `feature/F-031-asiento-analitico`, creado a las
  14:42). El implementer de F-030 no lo toca. Se pone verde solo cuando ese
  worktree se cierre (o si el humano decide que el test excluya
  `.claude/worktrees/`, cambio de otra feature). Sin el, `init.sh` da el
  resto en verde (cobertura 100 %, 59/59).

### F-030 · despliegue y verificaciones MANUAL (humano; T14, design §9)

Orden: **sv3 y despues sv4, en la misma sesion**; sv5 NO se despliega. Sin
schema nuevo. Hasta desplegar sv4, un casado por recurso se ve «Sin casar»:
no tocarlo en `/conciliacion`. Rollback: imagen anterior de sv3.

```powershell
.\infra\redeploy_partes.ps1 -Solo sv3
.\infra\redeploy_partes.ps1 -Solo sv4
```

- [ ] **M1 · tras sv3**: logs de arranque de `ca-sv3-persistencia`,
  `[matcher-provider] maestros cargados: ... recursos=N` sin error.
- [ ] **M2 · lectura en Sigrid antes de aprobar** (solo lectura, desde
  `services/partes-persistencia`, `PYTHONPATH=. ../../.venv/Scripts/python.exe
  <script>` con `SigridApiClient(...)._post_sql_read(sql=..., parameters=[],
  label="m2")`, comprobando `truncated`):
  `SELECT COUNT(*) FROM reshor rh JOIN con rc ON rc.ide = rh.reside WHERE
  rc.emp = 28 AND ISNULL(rh.caaide, 0) <> 0` => `0`.
- [ ] **M3 · reprocesar los 2 partes de Porsan (obra 0724, 25 y 28/09)**:
  (1) en el portal, si estan aprobados, «Marcar pendiente»; (2) «Mover a la
  papelera» cada parte (si no, la deduplicacion por sha256 lo ignora); (3)
  en el buzon `partes@ruesma.es`, mover sus correos de `Procesados` a la
  bandeja de entrada y marcarlos no leidos; (4) esperar sv1 -> sv2 -> sv3.
  Comprobar: el trabajador sin ficha sale casado con el nombre de su
  recurso y sus lineas con recurso y estado `ok`/`sin_parte` (no «Sin
  recurso»); el de ficha, igual que antes.
- [ ] **M4 · cuenta analitica, sin escribir**: abrir el modal de aprobacion
  de esas lineas (preflight, solo lectura) y buscar en los logs de
  `ca-sv5-transfer` `[registro] cuentas obra=0724 ok=0
  recurso_sin_cuenta=N` (N = lineas a escribir) y ninguna omitida por
  recurso. Aprobar de verdad es decision de Administracion; si se aprueba,
  comprobar por lectura que esas `hmores` (synckey `partes:<registro_id>`)
  tienen `caaide = 0`.

## F-029 · done y DESPLEGADA (2026-10-05): alias del logotipo de Ruesma (ruΞsma)

Desplegada a petición del humano: sv3 `ca-sv3-persistencia--r20261005121506`
(Healthy; arranque limpio, «alias de 2 empresa(s) ... 1, 28»).

APPROVED del reviewer en la primera pasada (`progress/review_F-029.md`);
resumen en `progress/history.md`. M1 concretado por el reviewer: tras
desplegar sv3, buscar en sus logs `[empresa-membrete]` con `sin_alias` y
texto `ru…sma` (no debe aparecer). Hoy Gemini transcribe el logotipo como
`ruesma` (`progress/explore_F-029_membrete.md`): el alias es red de seguridad.

Rama `feature/F-029-alias-logo-ruesma`. sdd=false, rigor estandar, solo
sv3 (config versionada). Implementada, pendiente de reviewer.

- T1 hecha: `services/partes-persistencia/tests/test_f029_alias_logo.py`
  contra la tabla versionada real; RED pegado en `progress/impl_F-029.md`.
- T2 hecha: alias `RUΞSMA` (normaliza «ru sma») en la empresa 1 de
  `config/empresas_membrete.yaml`, con comentario. Sin tocar código ni el
  prompt de sv2.
- **Desviación D1 (declarada)**: tres asserts de F-023 fijaban el
  contenido literal de la tabla (`test_f023_empresa_membrete.py`, uno;
  `test_f023_wiring_sv3.py`, dos). Ajustados al mínimo: la 1 pasa a
  `["RUESMA", "RUΞSMA"]`.
- Docs: ni `docs/ARCHITECTURE.md`, ni `partes-proyecto.md`, ni
  `azure-apps/partes.md` listan los alias, solo la ruta de la tabla: no
  se tocan.
- Mutación: alcance vacío (sin Python de producción); campaña manual sobre
  el YAML en el informe (7/8 muertos, el superviviente es equivalente).
- **M1 manual pendiente**: tras desplegar sv3, el primer parte de Ruesma
  con el logotipo sale con empresa 1 y origen `membrete`.

## F-019 · done y DESPLEGADA con el interruptor APAGADO (2026-10-05), pendiente de M3

Desplegada a petición del humano el 2026-10-05, en el orden de la spec:
sv3 `ca-sv3-persistencia--r20261005104505` y sv4
`ca-sv4-front--r20261005104930` (los dos inicializan el esquema sin errores,
163 sentencias complementarias), M1 y M2, y sv5
`ca-sv5-transfer--r20261005110655` (Healthy, 100 %, arranque limpio).
`MENSUALES_A_DEDICACION` no existe en el Container App: interruptor apagado,
sv5 decide lo de siempre.

- **M0** (líder, solo lectura, 2026-10-05): 12 líneas `omitido` de
  2026-09, todas con motivo «el recurso no tiene código de hora extra en
  Sigrid». Contexto de la base: 244 sin enviar, 34 `borrado_sigrid`, 12
  `omitido`, 1 `registrado`. Son las candidatas a reaprobar tras encender.
- **M1** (líder): `dedicacion_bandeja` existe, 0 filas, 23 columnas (sin
  nombre ni DNI), propietario el administrador.
- **M2** (lo ejecutó el humano; verificado por el líder):
  `dedicacion_app` conecta a `partes`, lee la bandeja (t), no lee
  `parte_registros` (f) y no crea en `public` (f).
- **Pendiente**: cerrar la regla de firewall `partes-puesto-pgris-20261005`
  si sigue abierta; feature espejo en `porcentajes`; **M3** al encender.
- **Lecciones de este despliegue** (los comandos de abajo y los de la spec
  se dejan como están porque un test fija el del `.sql`):
  `psql` de Windows ignora todo lo que va DETRÁS de la cadena de conexión:
  `-c`, `-v` y `-f` van delante
  (`psql -v rol=dedicacion_app -f infra/sql/01_dedicacion_lectura.sql "host=... dbname=partes user=... sslmode=require"`).
  Con el `az` actual la regla de firewall se nombra con `-n`, no con
  `--rule-name` (`fase1_infra_partes.ps1` sigue con `--rule-name`: no se
  cambia porque en versiones antiguas `-n` era el servidor).

APPROVED del reviewer en la primera pasada (`progress/review_F-019.md`);
D3, D4 y D5 aceptadas por el humano el 2026-10-03. Resumen en
`progress/history.md`. Queda a decisión del humano añadir la pareja de
congelación sv3/sv4 (F-004/F-024) a la lista cerrada de `CLAUDE.md`
(observación del reviewer; no la crea F-019).

Rama `feature/F-019-mensuales-a-dedicacion` (mergeada y borrada). Historial de tareas: ver
`specs/F-019-mensuales-a-dedicacion/tasks.md` (las marcadas `[x]` estan
hechas, un commit por tarea). Decisiones y desviaciones: se anotan aqui y
en `progress/impl_F-019.md`.

- T1 hecha: 26 tests de caracterizacion de `ReglasRegistro` en verde
  contra el codigo de hoy, ANTES de tocar `reglas_registro.py`.
- T2 hecha. **Desviacion D1 (interpretacion, no improvisacion)**: R2 y
  R3 bis chocan en una ficha M*+HL*+HE* (hoy inexistente en Sigrid: 0
  recursos M* con HL*). R2 mandaria su ordinaria a dedicacion; R3 bis
  prohibe que algo que hoy se escribe y no es incidencia cambie. Manda
  R3 bis (innegociable del humano transmitido por el lider: «encendido,
  solo cambia omitir->dedicacion e incidencia M* escribir->dedicacion»).
  Test: `test_f019_r3bis_mensual_con_hl_y_he_sigue_escribiendo_ordinarias`.
- T3 hecha. **Desviacion D2**: `resumen.dedicacion` del preflight (R7)
  solo aparece si hay alguna linea a dedicacion. Con la clave siempre
  presente fallaba `test_f002_r4_preflight_del_endpoint_no_escribe`, que
  compara el resumen clave a clave y T12 prohibe tocar tests ajenos; asi,
  con el interruptor apagado el contrato de F-002 queda identico.
- T4 hecha: `DedicacionBandejaOrm` (23 columnas, sin FK, indice
  `(anio, mes)`, server_default en toda NOT NULL) en las dos copias byte a
  byte; guardianes de raiz a seis tablas. Test extra en sv3
  (`test_f019_orm_bandeja.py`) para que la copia de sv3 tenga sus tests.
- T5 hecha. **Desviacion D3**: `dedicacion` NO entra en la tupla
  `ESTADOS_CONGELANTES` (design §4 lo pedia): dos tests ajenos (F-004 y
  F-024) fijan esa tupla literal y T12 prohibe tocarlos. La tupla no la
  usa ningun codigo de produccion; la congelacion de `dedicacion` va en
  `motivo_congelacion_linea/documento` y el guardian F-024 lo compara con
  sv3. Para el bloqueo de borrado definitivo: `vive_fuera` y
  `motivo_borrado_definitivo` (motivo propio para dedicacion).
- T6 hecha: `_upsert_bandeja` + `marcar_registros_sigrid(dedicacion=,
  prueba=, incidencias=)` en la misma transaccion. Decision: el
  `recurso_ide` de la fila es el del resultado de sv5 (pudo resolverlo por
  DNI) y, si no viene, el de la linea; el motivo de la linea no se trunca
  (el codigo `M*` es corto y la columna `codigo_mes` es String(16)).
- T7 hecha: `aplicar_resultado(..., incidencias=)`; el consumidor recibe la
  tabla de clases desde `main.py` (la construye `main()` con
  `construir_tabla_incidencias`, parametro opcional de
  `_componentes_de_cola` para no romper sus tests de F-002); `_trazar` usa
  la tabla del portal. Test de los dos canales marcando igual.
- T8 hecha: `excluidas["dedicacion"]` solo aparece si hay alguna (como
  `incompatible` de F-025: los tests de F-022/F-025 comparan `excluidas`
  literal); `_motivo_sin_lineas` lo dice; el listado del modal pinta
  `dedicacion`, fuera de `ESTADOS_ESCRITURA`. `agregar_ejecucion` (varias
  obras) NO junta `dedicacion`: lo rompia un test de F-022 y no lo pide la
  spec; el modal lo lee de cada grupo.
- T9 hecha: `retirar_de_dedicacion` + `POST /api/dedicacion/retirar`
  (ambito obligatorio, `_validar_ambito`, `_actor`). **Desviacion D4**: el
  guardian de F-017 `test_f017_todos_los_puntos_de_escritura_usan_el_helper`
  cuenta literalmente las llamadas a `_actor(request)` (14); R24 exige una
  mas, asi que el contador pasa a 15 con su docstring. Es un test ajeno a
  F-019 (T12 no lo preveia); esquivarlo escribiendo la llamada de otra
  forma habria sido enganar al guardian.
- T10 hecha: rama `dedicacion` en las dos vistas («→ dedicación», motivo
  en el `title` escapado por Jinja, boton «Retirar»); `app.js`: etiqueta
  del listado, aviso de `excluidas.dedicacion` y del resultado con
  `esc()`, `retirarDedicacion` con el `ambito` de `#aprobar-todo` y
  recarga. Sin CSS nuevo (`badge info` basta). `node --check` OK. El JS
  no tiene arnes: el comportamiento en navegador queda para M3.
- T11 hecha: `infra/sql/01_dedicacion_lectura.sql` (solo 3 GRANT + 4
  SELECT de comprobacion) y `tests/test_f019_sql_lectura.py` (analizador
  probado contra 15 alteraciones; R27 por AST: ningun literal no-docstring
  de `services/` lleva `GRANT`).
- T12 hecha. **Desviacion D5**: el guardian de F-017
  `test_f017_r22_no_hay_ficheros_sql_de_migracion` prohibia CUALQUIER
  `.sql` del arbol y R25 exige uno. Se admite SOLO
  `infra/sql/01_dedicacion_lectura.sql` (no es migracion: GRANT + SELECT,
  vigilado por el test de T11); cualquier otro `.sql` sigue fallando.
  Suites completas de sv3, sv4, sv5 y raiz en verde (cifras en el informe).
- T13 hecha: semantica 15 y «seis tablas» en `docs/ARCHITECTURE.md`;
  §3.5, §5, §5.5 bis y §6.6 en `docs/referencia/partes-proyecto.md`.
- T14 hecha: `azure-apps/partes.md` (nota F-019, §4.5 bis lo que
  exponemos y que se rompe, variable en §5.6), commit local `c7ad8e9` en
  `azure-apps` (sin push; ese repo no tiene remoto).

- T15 hecha: campana de mutacion completa, 126 mutantes, 125 muertos, 1
  superviviente (`include_in_schema` de la ruta nueva) cerrado con test
  nuevo; `progress/mutacion_F-019.md`. Informe: `progress/impl_F-019.md`.
- T19 hecha: `bash harness/init.sh` en verde (cobertura de lineas
  cambiadas 100 %, 201/201). T16-T18 pendientes del humano (abajo).

**Las desviaciones D3, D4 y D5 tocan tests ajenos a F-019 o se apartan
del design por ellos: necesitan el visto bueno del humano.** Si no se
aceptan, alternativas: D3 meter `dedicacion` en `ESTADOS_CONGELANTES` y
actualizar los dos tests; D4/D5 no tienen alternativa limpia (R24 exige
`_actor(request)` y R25 exige el `.sql`).

### Pendiente MANUAL (humano) · T16-T18 (design §10)

Orden: **sv3 → sv4 → M1, M2 → sv5** (interruptor apagado) → feature espejo
de `porcentajes` leyendo la bandeja → **M3** (encender).

- **T16 · M0** (ANTES de desplegar; PG `partes`, abrir firewall a tu IP):
  `SELECT sigrid_estado, left(fecha,7) AS mes, count(*) FROM parte_registros WHERE sigrid_motivo LIKE '%codigo mensual%' OR sigrid_motivo LIKE '%es mensual%' GROUP BY 1,2 ORDER BY 2;`
  Anotar el resultado aqui.
- **T17 · despliegue** (lo pide el humano), desde `infra/` y EN TRES
  pasadas (con `-Solo sv3,sv4,sv5` el script ordenaria sv3 → sv5 → sv4):
  `./redeploy_partes.ps1 -Solo sv3`, luego `./redeploy_partes.ps1 -Solo sv4`.
  - **M1** (tras sv3 y sv4): `SELECT count(*) FROM dedicacion_bandeja;` → 0.
  - **M2**: `psql "host=<servidor> dbname=partes user=<admin> sslmode=require" -v rol=<rol_app_dedicacion> -f infra/sql/01_dedicacion_lectura.sql`
    → las comprobaciones dan true / false / false (si la tercera da true,
    avisar; no se corrige aqui).
  - `./redeploy_partes.ps1 -Solo sv5` con el interruptor APAGADO (no hay
    que tocar nada: `MENSUALES_A_DEDICACION` no existe en Azure y su
    defecto es false).
- **T18 · M3** (solo cuando la feature espejo de `porcentajes` lea la
  bandeja):
  `az containerapp update -n ca-sv5-transfer -g rg-partes-dev --set-env-vars MENSUALES_A_DEDICACION=true`;
  aprobar una linea de un mensual, ver «→ dedicación» en la vista y
  `SELECT registro_id, version, vigente, tipo, codigo_mes, prueba FROM dedicacion_bandeja ORDER BY actualizado_at_utc DESC LIMIT 5;`;
  «Retirar» (vigente false, version 2) y reaprobar (vigente true,
  version 3). Si algo falla, apagar con el mismo comando y `=false`.

## F-028 · done y DESPLEGADA (2026-10-02), pendiente de M1

APPROVED del reviewer (`progress/review_F-028.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`62c544b`) y desplegada a petición
del humano: sv4 `ca-sv4-front--r20261002122235` (Healthy, 100 % del tráfico,
arranque limpio en Log Analytics).

Rama `feature/F-028-ancho-detalle`, solo sv4. `base.html` admite una clase
extra en el contenedor del `<main>` (bloque `container_class`, vacío por
defecto); `obra_detail.html` y `trabajador_detail.html` usan
`container--ancho` (`styles.css`: `width: calc(100% - 32px)`, sin tope).
Listados y topbar sin cambios. Informe: `progress/impl_F-028.md`. Sin
desviaciones. Sin despliegue.

Pendiente MANUAL (humano, tras desplegar sv4 y Ctrl+F5): **M1** abrir el
detalle de una obra (y el de un trabajador) en la ventana ancha (3440 px) y
comprobar que el contenido ocupa todo el ancho menos 16 px por lado y que no
hay scroll horizontal en la matriz de días ni en la tabla de líneas cuando
caben; un listado (Obras) sigue centrado a 1500 px. Si la tabla de líneas
sale estirada o con scroll por anchos de columna guardados de antes, doble
clic en la manija de la columna los reajusta (O2 del reviewer).

## F-025 · done y DESPLEGADA (2026-10-02), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-025.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`04ac4fb`) y desplegada a petición del humano: sv4
`ca-sv4-front--r20261002110836`; el log de arranque lista las clases
(H=CIH:dia_completo). azure-apps actualizado por el líder (commit local `6347c60`:
`INCIDENCIAS_PATH` y la regla). Pendientes MANUAL (humano): M1 (lectura en
PG antes de desplegar, requiere firewall) y M2–M5 tras desplegar sv4, con
los pasos de `impl_F-025.md` §6. Clasificación confirmada por el humano
con Administración el 2026-10-02: F día completo y **H (huelga) día
completo** (cambiado respecto a la spec, que la proponía parcial).

## F-022 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-022.md`, seis observaciones no
bloqueantes; O4 y O5 dan lugar a F-027); resumen en `progress/history.md`.
Mergeada a `dev` (`5dea576`) y desplegada a petición del humano: sv4
`ca-sv4-front--r20261001210234` (140 sentencias, Uvicorn 8014, revisión
anterior retirada). El aviso de filtrar por obra en la ficha de persona ya
no aplica.
azure-apps: commit local `fdc6e1d` (sin push).

Pendientes MANUAL (humano, design §9; pasos exactos en `impl_F-022.md` §7):
M1 consulta de lectura en PG (¿ya pasó un lote de varias obras?); desplegar
sv4 (solo sv4) y Ctrl+F5; M2–M7 en navegador en modo pruebas (selección,
filtros, ocultas, persona con dos obras, listado y excluidas, muchas filas y
regresión del botón por línea); M8 tras la primera aprobación real de varias
obras. El JS no tiene arnés: lo de navegador solo lo verifica M2–M7.

## F-024 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-024.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`93a3eff`) y desplegada a petición
del humano: sv5 `ca-sv5-transfer--r20261001170655` (Uvicorn 8005) y luego sv4
`ca-sv4-front--r20261001170858` (140 sentencias, transfer y sigrid-lookup
CABLEADOS, Uvicorn 8014, revisión anterior retirada). azure-apps: commit local `03f994c` (sin push).

**AVISO OPERATIVO (DA13): ya NO aplica tras el despliegue del 2026-10-01**; era: no usar «Aprobar todo» en
la obra 0719 · 09/2026 ni «Aprobar visibles» en la ficha de sus trabajadores
(reescribiría las 35 líneas que Administración borró a propósito).

Pendientes MANUAL (comandos exactos en `progress/impl_F-024.md`, design §9):
M1 consulta de `registrado` en PG antes de desplegar (requiere firewall);
M2 desplegar sv5 y luego sv4; M3 abrir la obra 0719 en el periodo del
16–28/09 y ver en el log `[comprobacion-sigrid] … borradas=35` sin
`[sigrid-write]`; M4 PG: PT26/00314 con 35 `borrado_sigrid`; M5 navegador
(Reaprobar, botón, sondeo del modal, casilla de borradas: el JS no tiene
tests). Después: M3 de F-023 (reconciliar recursos) y reaprobación por
Administración.

## F-021 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-021.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`3e5d85f`) y desplegada a petición
del humano: sv5 `ca-sv5-transfer--r20261001183051` y luego sv4
`ca-sv4-front--r20261001183229` (arranques limpios en Log Analytics).
**M1 hecha por el líder**: 0 líneas `partes:%` en `hmores` (nada que
rellenar). M2 requiere escritura en modo pruebas desde local: solo con
autorización expresa del humano. Observación O1 del reviewer: el docstring de `_resolver_cuentas`
(`registro_pipeline.py:210`) dice que la cola reintenta; no reintenta (sv4
marca las líneas en error hasta que se reaprueban). Corregir en la próxima
feature de sv5.

MANUAL (humano), design §9 — solo lecturas salvo M2 (modo pruebas):

- **M1 · antes de desplegar sv5** (sigrid-api, base `ruesma`, lectura):
  `SELECT h.ano, h.mes, COUNT(*) AS n, SUM(CASE WHEN ISNULL(h.caaide,0)=0
  THEN 1 ELSE 0 END) AS sin_cuenta FROM hmores h WHERE h.synckey LIKE
  'partes:%' GROUP BY h.ano, h.mes`. Esperado: lo que haya escrito sv5
  desde la exploración (0 filas el 2026-10-01); si hay, decidir según DA6.
- **M2 · tras desplegar sv5** (modo pruebas, obra `0404`): aprobar un
  parte con ordinarias, extras y una incidencia de un recurso de la
  empresa 1 y leer `SELECT h.synckey, ah.cod AS hora, c.cod AS cuenta,
  ca.cenide, o.cenide AS cen_obra FROM hmores h JOIN obr o ON o.ide =
  h.obride LEFT JOIN auxhor ah ON ah.ide = h.horide LEFT JOIN con c ON
  c.ide = h.caaide LEFT JOIN caa ca ON ca.ide = h.caaide WHERE h.synckey
  IN (…)`. Esperado: `cuenta` = `<código del centro de 0404>.<subcuenta>`,
  `ca.cenide = cen_obra`; `CI*`/`CIZ` con la subcuenta del tipo por
  defecto. En el log de sv5: `[registro] cuentas obra=0404 ok=…`. Limpiar
  con `prueba_escritura_sigrid.py`.
- **M3 · tras desplegar sv4** (navegador, Ctrl+F5): preflight de un
  recurso cuya subcuenta no tiene la `0404` (consulta en design §9 M3).
  Esperado: bloque «N linea(s) se registraran sin cuenta analitica» en el
  modal y la línea escrita con `caaide = 0`.
- **M4 · Administración**: la línea de M2 se ve en Sigrid con la cuenta
  igual que una tecleada; confirmar DA3 y DA13 (Porsan sin cuenta).

### (histórico) spec escrita, pendiente de aprobación

Spec en `specs/F-021-cuenta-analitica-sigrid/` (rama
`feature/F-021-cuenta-analitica-sigrid`, sin commits). Exploración de solo
lectura en `progress/explore_F-021_sigrid.md`. Toca **sv5** (regla y
escritura) y **sv4** (solo un aviso en el modal del preflight); sv3 no.

Hallazgo: la «cuenta analítica del recurso» **no** es `res.caaide` (0 en
todos); es `reshor.caaide` (recurso × tipo de hora), una plantilla del centro
`00000`. La línea manual lleva en `hmores.caaide` la cuenta **del centro de
su obra** con la misma subcuenta: 99,64 % de coincidencia en la empresa 1 con
respaldo por el tipo de hora por defecto. Porsan (28) no usa cuenta en horas
(0 %). Hoy hay 0 líneas de sv5 en Sigrid: nada que reescribir.

Decisiones a validar (design §8, con recomendación):

1. DA1 · origen `reshor.caaide` del tipo escrito; si no, del tipo por defecto.
2. DA2 · destino: la cuenta del centro de la obra con esa subcuenta.
3. DA3 · sin cuenta ⇒ escribir 0 y avisar solo si la obra no la tiene; no bloquear.
4. DA4 · aviso en el modal del preflight (JS de sv4); alternativa: solo log.
5. DA5 · la partida no interviene.
6. DA6 · sin reescritura de lo ya registrado (M1 lo comprueba antes).
7. DA7 · fallo al leer cuentas ⇒ la petición falla entera.
8. DA8 · sin variable de activación (marcha atrás = revisión anterior).
9. DA9 · `caaide` obligatorio en `stmt_insert_linea`.
10. DA10 · `cuaide` sin escribir; cuentas de baja sin filtrar.
11. DA11 · corregir solo comentarios de `prueba_escritura_sigrid.py`.
12. DA12 · despliegue sv5 → sv4 (cualquier orden es seguro).
13. DA13 · Porsan: nada en código; si la quieren, se rellena `reshor` en Sigrid.

## F-023 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

Mergeada a `dev` (`27fc03c`) y desplegada a petición del humano, que decidió
desplegar sin esperar a M1 ni M5. Orden de la spec: sv5 primero
(`ca-sv5-transfer--r20261001083016`) y luego sv2 → sv3 → sv4
(`…--r20261001083313`). Arranques comprobados en Log Analytics: sv5 Uvicorn
8005; sv2 catálogo auxhor CABLEADO; sv3 «140 sentencias complementarias»,
Sigrid «todas las empresas», alias del membrete 1 y 28; sv4 «140 sentencias»,
transfer y sigrid-lookup CABLEADOS, Uvicorn 8014; portal responde 302 (Easy
Auth). Hechas por el líder (solo lectura, sigrid-api, base `ruesma`):
**M4 OK** (`0404` solo en la empresa 1) y **línea base de M2**: `PT26` máximo
`00338` en la empresa 1 y `00121` en la 28 antes de cualquier aprobación con
el código nuevo. T17 no se pudo hacer: extensión de Chrome sin conectar.


APPROVED del reviewer en la pasada 2 (`progress/review_F-023.md`); resumen en
`progress/history.md`. Rama `feature/F-023-recurso-alta-empresa`, sin mergear
ni desplegar. Desviación D1 del implementer (el PATCH de obra del portal
resuelve por `ide`) aceptada por el reviewer.

### MANUAL (humano) pendientes de F-023 (design §9 y T17)

1. **M1 · antes de desplegar (lectura, SQL Server vía sigrid-api y PG
   `partes`)**: `ide` de obras gemelas en Sigrid
   (`SELECT con.ide, con.cod, con.emp FROM obr JOIN con ON con.ide = obr.ide
   WHERE con.cod IN (SELECT c.cod FROM obr o JOIN con c ON c.ide = o.ide
   GROUP BY c.cod HAVING COUNT(DISTINCT c.emp) > 1)`) y, con esos ides, en
   `partes`: `SELECT r.obra_ide, d.approved, count(*) FROM parte_registros r
   JOIN parte_documents d ON d.id = r.document_id WHERE d.is_active AND
   r.deleted_at_utc IS NULL AND r.obra_ide IN (…) GROUP BY 1, 2;`
2. **M5 · antes de desplegar sv2**: con sv2 en local, ≥ 10 partes reales
   (≥ 5 de cada empresa): `empresa_membrete` correcto y el resto de la
   cabecera y los empleados igual que su extracción guardada. Anotar en
   `progress/evals_F-023.md` sin nombres ni DNIs.
3. **Despliegue** (lo pide el humano): orden **sv5 → sv2 → sv3 → sv4**
   (`redeploy_partes.ps1 -Solo svN`). Al arrancar sv3/sv4 el DDL
   complementario pasa de 137 a 140 sentencias (log de arranque).
4. **M2 · tras sv5** (lecturas por `POST /api/sql/read` de sigrid-api,
   base `ruesma`; `<OBRA_IDE>`, `<AAAA>`, `<MM>` = obra de la empresa 28 y
   mes del parte aprobado; `$KEY` = function key que el humano saca del Key
   Vault, nunca escrita en ningún fichero). Antes de aprobar, apuntar el
   `PT` máximo de cada empresa con la 2.ª consulta (con `28` y con `1`):
   ```powershell
   $q = @{ database = 'ruesma'; max_rows = 10; parameters = @(<OBRA_IDE>, <AAAA>, <MM>);
     sql = 'SELECT con.ide, con.cod, con.emp, con.tip FROM hmo JOIN con ON con.ide = hmo.ide WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? AND ISNULL(hmo.reside, 0) = 0 AND con.tip = 35' } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q
   $pt = @{ database = 'ruesma'; max_rows = 1; parameters = @('PT26/%', 28);
     sql = 'SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?' } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $pt
   ```
   **Esperado**: la 1.ª devuelve UNA fila con `emp = 28` y `tip = 35`; si
   la cabecera la creó sv5, su `cod` es el máximo de la 28 anterior + 1 (la
   2.ª consulta con `28` lo devuelve) y el máximo de la empresa `1` no ha
   cambiado. `truncated` = false.
5. **M3 · tras sv3** (lo lanza el humano): `POST
   <url-de-sv3>/admin/reconciliar-recursos` → `{"ok": true, …,
   "partes_sin_recurso": N}`. Después, en la base `partes` (solo lectura;
   `:dni` = DNI del caso guía, que el humano escribe en la consola y no se
   apunta en ningún fichero):
   ```sql
   SELECT r.recurso_ide, r.parte_estado, (d.approved OR r.sigrid_estado IN ('encolado','registrado')) AS congelada, count(*)
   FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
   WHERE d.is_active AND r.deleted_at_utc IS NULL
     AND upper(replace(replace(r.empleado_dni,'-',''),' ','')) = upper(:dni)
   GROUP BY 1, 2, 3 ORDER BY 3, 1;
   ```
   y, con los `recurso_ide` que salgan, en Sigrid: `SELECT res.ide, rc.emp,
   rc.fecbaj FROM res JOIN con rc ON rc.ide = res.ide WHERE res.ide IN
   (<ides>)`. **Esperado**: las filas NO congeladas tienen un único
   `recurso_ide`, de `emp = 1` con `fecbaj` 0 (no el dado de baja en 2021),
   y `parte_estado` `ok` o `sin_parte`; las congeladas conservan el que
   tenían.
6. **M4**: el código `0404` (modo pruebas) existe en una sola empresa
   (`SELECT con.emp FROM obr JOIN con ON con.ide = obr.ide WHERE con.cod = '0404'`).
7. **T17 · navegador (sv4, Ctrl+F5)**: los combos de obra y trabajador
   muestran «· empresa N»; en «+ Nuevo» y en «Añadir línea», con obra
   elegida (o fijada por el parte), el combo de trabajador solo ofrece
   fichas de su empresa; elegir la gemela de la 28 en el combo de obra del
   detalle deja esa obra (no la de la 1).

## F-020 · done y DESPLEGADA (2026-09-30), pendiente de verificación manual

Cerrada con APPROVED del reviewer; resumen en `progress/history.md`.
Mergeada a `dev` y desplegada a petición del humano:
`redeploy_partes.ps1 -Solo sv1` → imagen `sv1-partes:latest`
(digest `sha256:06fa219d…`), revisión **`ca-sv1-poller--r20260930150607`**,
`Healthy` y `RunningAtMaxScale`. Arranque limpio en el log: carpetas origen,
Procesados y Errores resueltas, «Pre-checks OK» y primer sondeo del inbox
con `200 OK`. Pendiente del humano (design §10):

1. ~~Merge a `dev` y despliegue de sv1~~ (hecho).
2. Mover **uno** de los cuatro correos del escáner («Attached Image», 17/09 y
   tres del 30/09) de `Errores` a la carpeta origen y marcarlo **no leído**.
3. Logs de `ca-sv1-poller`: `correo adjunto con 1 PDF interior(es)`,
   `Documento logico INGERIDO` (una por página) y `movido a Procesados`; el
   parte (o sus páginas) en el portal.
4. Reprocesar los otros tres igual (la dedup de sv3 por `document.sha256`
   hace inocuo repetir uno ya ingerido).

## Sesión 2026-09-02 · sv5 pasa a MODO NORMAL de escritura en Sigrid

Cambio operativo en Azure, pedido por el humano. No toca código ni features.

```powershell
az containerapp update -n ca-sv5-transfer -g rg-partes-dev `
    --set-env-vars OBRA_PRUEBAS_FORZAR=false
```

Verificado tras el cambio (lecturas reales, no supuestos):

| Comprobación | Resultado |
|---|---|
| `OBRA_PRUEBAS_FORZAR` | `false` |
| `SIGRID_API_DATABASE` | `ruesma` (la base de escritura, no la réplica) |
| Revisión activa | `ca-sv5-transfer--0000002`, 100 % tráfico, 1 réplica, `RunningAtMaxScale` |
| Otras revisiones | ninguna activa |

`OBRA_PRUEBAS_COD=0404` y `MARCA_PRUEBAS=PRUEBA-IA` siguen definidas pero son
inertes con el flag en `false`. **Desde ahora cada parte aprobado en el portal
se registra en SU obra real de Sigrid.**

Del arranque no se pudo leer la línea de Uvicorn: el buffer de
`az containerapp logs show` venía lleno de trazas del SDK de colas y el
arranque ya había pasado. La evidencia válida es la revisión corriendo con su
réplica.

Documentación actualizada en el mismo trabajo: `azure-apps/partes.md`
(commit local `66682f8`, **sin push**).

### Lo que queda pendiente de esto

1. **Limpiar las líneas `PRUEBA-IA` de la obra 0404** que dejó la etapa de
   pruebas. El flag ya no afecta a lo escrito, así que el orden da igual, pero
   la basura sigue en Sigrid:
   `cd services\partes-transfer && python .\prueba_escritura_sigrid.py limpiar --ejecutar`
2. **Revisar si algún parte de la BD `partes` figura como registrado en Sigrid
   cuando en realidad fue a la 0404** (aprobado mientras el modo pruebas estaba
   activo). Ofrecido al humano, aún sin hacer.
3. **Aviso: el `.env` local de sv5 también tiene `OBRA_PRUEBAS_FORZAR=false`.**
   Cualquier prueba lanzada desde local escribe en la obra REAL, al contrario
   de lo que manda `CLAUDE.md` para pruebas locales.

## Sesión 2026-08-25 y anteriores

Sesión 2026-08-25: **F-005 `in_progress`** en `feature/F-005-graphkey-keyvault`
(limpieza documental, ver la sección final). De la sesión anterior
(2026-08-19/20): **F-015 y F-016 `done`**, las dos APROBADAS por el reviewer,
mergeadas, publicadas y **DESPLEGADAS**. **F-014 `blocked`** como deuda
aparcada, pero su puerta ya está abierta (ver abajo).

| Rama | Estado |
|---|---|
| `feature/F-016-admin-empleado-jornada` | mergeada a `dev` y borrada |
| `feature/F-014-candef-9-sigrid` | petición lista, aparcada a la espera de RRHH |

`dev` = merge de F-016 (`5606954`), publicado, con F-015 dentro.

## Despliegue del 2026-08-20 (00:10)

`redeploy_partes.ps1 -Solo sv3,sv4` desde el árbol en `dev`. Ambos servicios en
la revisión **`r20260820000737`**:

| Servicio | Estado comprobado |
|---|---|
| `ca-sv4-front` | `Running`, 1 réplica. Arranque limpio: «esquema inicializado (137 sentencias complementarias)» → `Application startup complete` → Uvicorn en 8014. `HTTP 401` sin cookie ⇒ Easy Auth en pie. |
| `ca-sv3-persistencia` | `ScaledToZero` (KEDA min 0, normal). Su log de arranque **ya está verificado** (2026-08-20 por la mañana): ver la sección siguiente. |

Con esto queda aplicado también el DDL pendiente de **F-010** (M1/M2).

Dos tropiezos, ninguno de código y los dos ya conocidos:

1. `RequestDisallowedByAzure` (MFA) en el primer intento: el `az login` normal
   vale para el build en el ACR pero no para `containerapp update`. Se resuelve
   con el `--claims-challenge` de `infra/README_partes.md:28`.
2. `getaddrinfo failed` de DNS en el **paso final informativo**, ya creadas las
   dos revisiones: solo dejó vacío el «Portal sv4: https://». FQDN real:
   `ca-sv4-front.yellowplant-2add9c3e.spaincentral.azurecontainerapps.io`.

Aprendizaje operativo: `az containerapp logs show --tail` ya no alcanza el
arranque —el polling de colas llena el buffer en minutos—. Los logs de arranque
salen con `az monitor log-analytics query -w <workspace de log-partes-dev>`
filtrando por `RevisionName_s`.

## Verificación del despliegue (2026-08-20, mañana)

Dos verificaciones lanzadas a subagentes. Informes:
`progress/verif_sv3_arranque_20260820.md` y
`progress/verif_esquema_partes_20260820.md`.

### 1. Arranque de sv3 — VERDE

Sin `Traceback`, sin `ERROR` y **sin ningún WARNING de jornada** (ni candef
fuera del mapa, ni fallo leyendo `empleado_jornada`). Esquema inicializado con
**137 sentencias complementarias**, las mismas que reportó sv4. Wiring
correcto: `[jornada][wiring] mapa candef -> jornada semanal: 8:40, 9:42`, más
calendario, Sigrid, SharePoint y consumo de `q-persistencia`. Misma imagen del
despliegue (`sv3-partes:latest`, digest `sha256:b3b533c5…`). Devuelto a **0
réplicas**, confirmado `ScaledToZero`.

Dos aprendizajes operativos:

- **La revisión `r20260820000737` YA había arrancado** entre 22:09 y 22:14 UTC
  de anoche y su log estaba en Log Analytics desde entonces. Forzar réplicas no
  era necesario: antes de hacerlo, mirar si la revisión ya tiene filas en
  `ContainerAppConsoleLogs_CL`.
- **Cada cambio de `--min-replicas` crea una revisión nueva.** La activa ya no
  se llama `r2026…` sino `ca-sv3-persistencia--0000010`. El código se rastrea
  por **digest del ACR**, no por el nombre de la revisión.
- El `az containerapp update` pasó a la primera: el `--claims-challenge` no
  llegó a hacer falta (el humano había reautenticado con MFA en su consola).

### 2. Esquema en PostgreSQL — CONFORME (verificado contra la base real)

Al primer intento el subagente reportó `connection timeout expired` y **acusó
al firewall**. Era un diagnóstico sin evidencia: la IP pública del puesto
(`nslookup myip.opendns.com`) YA tenía regla en `psql-albaranes-rs9k2`, y
`Test-NetConnection ... -Port 5432` responde `TcpTestSucceeded: True` en 0,01 s.
Al reintentar, `psycopg` conectó en 0,1 s con el mismo host, puerto y usuario.
**Lección** (candidata a automejora del arnés): un timeout no basta para
acusar al firewall sin probar antes el TCP crudo.

Verificado contra PostgreSQL 16.14, base `partes`:

- **19/19 columnas** en `empleado_jornada`: nombre, orden ordinal, tipo,
  nulabilidad y `DEFAULT` coinciden con el ORM y con la spec.
- **`ix_empleado_jornada_dni_norm`** presente sobre `(dni_norm)`, no único, más
  la PK con secuencia. **Cero CHECKs**, que es lo correcto: F-015 §6 delega esas
  validaciones a la aplicación (F-016/R27).
- **M1 de F-010 ✅**: `ix_parte_registros_deleted_at_utc` presente, recuentos
  exactos **7/47/56/7**, `ux_parte_documents_sha256_active` intacto. Ninguna
  tabla ganó ni perdió columnas.
- **Base ↔ sv3 ↔ sv4 coinciden**: las dos copias del ORM siguen byte-idénticas
  y cuadran con la base. Control cruzado: 118 + 19 = **137 sentencias**, justo
  lo que loguearon los dos servicios.
- **4 filas de prueba** de las pruebas en navegador, **ya desactivadas** por el
  humano: `origen='manual'` ✅ y `created_by`/`updated_by` **NULL** ✅, que es
  lo esperado sin `DEFAULT_REVIEWER` (H1) y confirma ese hallazgo desde la base.

**R7 VERIFICADO** (2026-08-20, segunda vuelta). Alta en pantalla con último
día incluido `2026-07-31`: la base guarda **`hasta = 2026-08-01`** y el listado
repinta `2026-07-31`. La conversión «+1 día» funciona. Confirmado por partida
doble con una fila de control (último día `2026-08-20` → `hasta = 2026-08-21`),
y una tercera fila «sin fin» cubre la mitad NULL del requisito.

`desde` sin desplazamiento de huso en las tres. Se sostiene porque `desde` y
`hasta` son **`varchar(16)`** con la fecha ISO, no `date`/`timestamp`: no hay
capa que pueda reinterpretar la zona horaria.

**R12 (solapes) sin violación**: las tres filas se solapan en julio pero solo
una está activa; la auditoría muestra que el humano desactivó cada una antes de
crear la siguiente (baja 11:31:16 → alta 11:31:42), así que el alta **no debía**
rechazarse. La rama de rechazo sí se ejercitó, pero en la prueba anterior de
navegador (el aviso rojo nombrando la fila en conflicto), no en estas filas —
lógicamente no deja rastro en la base, porque no llega a crear nada.

### 2-bis. (histórico) el falso bloqueo por firewall

No se pudo consultar la base real: la IP pública del puesto no figura en
ninguna regla de `psql-albaranes-rs9k2` (`connection timeout expired`). **No se
tocó nada del servidor**, que es compartido. Queda pendiente de que el humano
añada la regla (`datamart-puesto-pgris-<fecha>`) y se relance; el SQL exacto
está listo en el informe, incluida la **M1 de F-010**.

Lo verificable sin base salió **CONFORME**: 19 columnas declaradas, índice
`ix_empleado_jornada_dni_norm` sobre `(dni_norm)` declarado, y las **dos copias
de `orm_models.py` (sv3 y sv4) byte-idénticas** — el defecto que F-010 vino a
arreglar sigue sano. `ddl_complementario()` genera 137 sentencias, 19 de ellas
de `empleado_jornada`: **cuadra con el log de arranque de los dos servicios**.

Sin CHECKs de horas 0–24 ni de vigencias en la base, y eso es **correcto**: la
spec los pone en la aplicación (F-016/R27), no en el schema.

Dos correcciones que salieron de aquí:

- **Errata en `specs/F-015-jornada-semanal-candef/design.md` §8**: dice «las 16
  columnas». La tabla normativa §6, el ORM y el guardián dicen **19**. El texto
  está mal, no el código. Pendiente de corregir.
- **F-010 no tiene «migraciones M1/M2»**: M1/M2/M3 son sus *verificaciones
  manuales*. M2/M3 se dan por cumplidas con las 137 sentencias; **M1 sigue
  pendiente** (índice `ix_parte_registros_deleted_at_utc` y los recuentos
  7/47/56/7) y necesita acceso a la base.

### 3. Pruebas en navegador (2026-08-20, humano) — SUPERADAS

Las 6 verificaciones de `specs/F-016-admin-empleado-jornada/design.md` §8.2 y
el punto de KPI de **F-015 T12**, hechas por el humano contra el portal
desplegado. **Todo funciona.** Combo de trabajador (la 6, que ningún test
cubre): busca por nombre y por DNI, y el alta guarda el DNI elegido. Alta con
DNI ficticio: sale el aviso de R19 y la fila se crea igual. Solape: rechazado
nombrando la fila en conflicto, sin crear nada. Contigua: aceptada. El
listado enseña el `hasta` **inclusivo**, no el interno.

Tres hallazgos, ninguno de ellos un fallo del código desplegado:

**H1 · `DEFAULT_REVIEWER` NO está configurada en el Container App de sv4.**
Comprobado en Azure: la variable no existe en la plantilla del contenedor, y
`.env.example` la declara vacía. El helper `_actor`
(`services/partes-front/interface_adapters/web/app.py:477`) lo contempla —
«sin `DEFAULT_REVIEWER` configurado se sella `NULL` y la operación NO falla»—
y la plantilla pinta `—`. Consecuencia que va más allá de F-016: **los once
puntos de auditoría del portal (`approved_by`, `deleted_by` y las cuatro
entradas de `undo_log`) llevan sellando NULL desde el primer despliegue**. La
auditoría del portal está en blanco, no «firmada con un genérico».
Reordena el enunciado de **F-017**: no es «pasar del valor genérico al usuario
real», es que hoy no hay ni genérico. **DECIDIDO por el humano el 2026-08-20**:
NO se configura un `DEFAULT_REVIEWER` provisional; se espera a **F-017**. El
NULL dice «no se sabe», que es la verdad, y un genérico crearía un tramo de
filas que luego habría que explicar.

**H2 · El KPI de jornada se resuelve con el PRIMER DÍA DEL PERIODO MOSTRADO,
no con hoy** (`app.py:698`, decisión consciente de R25). El periodo que sale
por defecto es el más reciente **con registros de ese trabajador**. Efecto
práctico: se creó una excepción con `desde` = hoy y **el KPI no la reflejaba**;
tampoco con `desde` = 1 del mes en curso. Con `desde` = 2026-01-01 apareció al
instante. Le pasó al humano, que conoce el sistema: **a un administrador le
parecerá que la pantalla no funciona**. No es un bug —la caché se invalida
bien y sv4 tiene una réplica— pero es deuda de usabilidad real. Candidatas:
avisar en la pantalla, o resolver el KPI con `hoy` cuando la excepción esté
vigente hoy.

**H3 · Hueco de borde**: si el trabajador **no tiene ningún registro**, la
ficha no construye calendario, y entonces el KPI se calcula con `date.today()`
pero pasando `excepcion=None` — ignoraría una excepción vigente hoy. En esa
rama la fecha y la excepción dejan de ir juntas. Menor, pero es una
incoherencia real.

**LIMPIEZA**: las pruebas dejaron filas en `empleado_jornada` de la BASE REAL,
incluida una de **un trabajador real** con vigencia desde 2026-01-01 y 42
h/sem. Hay que dejarlas todas `inactiva` (esta pantalla no borra, por diseño).

## F-017 · done, APROBADA y lista para mergear (2026-08-21)

Identidad real de Easy Auth en sv4. Resumen en `progress/history.md`; detalle
en `progress/impl_F-017.md`, `progress/mutacion_F-017.md` y
`progress/review_F-017.md`.

Verificado por el reviewer re-ejecutando: **1.057 tests** en sv4 + 138 en la
raíz, cobertura **99,3 %**, mutación **32/32 muertos, 0 supervivientes, 0
timeouts**. Solo sv4, cero cambios de schema. Primera vuelta RECHAZADA con
tres defectos, los tres corregidos y verificados —el guardián ampliado lo
comprobó **rompiéndolo**—.

**MERGEADA Y DESPLEGADA el 2026-08-21.** La ambigüedad que la spec no podía
cerrar **queda cerrada a favor de lo diseñado**. `GET /whoami` en el portal
desplegado devuelve:

```json
{"actor":"<upn del usuario>","origen":"cabecera-name",
 "entorno":"desplegado","senal_despliegue":"CONTAINER_APP_NAME",
 "cabeceras_easy_auth":["X-MS-CLIENT-PRINCIPAL-NAME",
                        "X-MS-CLIENT-PRINCIPAL",
                        "X-MS-CLIENT-PRINCIPAL-ID"]}
```

- Azure inyecta el **UPN**, no el display name: la apuesta de DA3 era correcta.
- Manda `cabecera-name`; el suplente base64 no hace falta.
- R5c detecta el entorno por la **señal A** (`CONTAINER_APP_NAME`), como
  confirmó T0. La señal B (haber visto una cabecera) no llegó a necesitarse.

**HALLAZGO PARA F-018**: Easy Auth inyecta también
**`X-MS-CLIENT-PRINCIPAL-ID`**, que es el **`oid` inmutable** del usuario.
F-017 dejó por escrito que no guardaba el `oid` «porque no hay columna y no se
va a inventar una», remitiendo a F-018 — y ahora sabemos que **el dato está
disponible en una cabecera dedicada**, sin decodificar el token. Si F-018 crea
la tabla de auditoría, puede llevar `actor` (legible) y `actor_id`
(inmutable) sin coste extra: es la diferencia entre una auditoría que aguanta
un cambio de nombre y otra que no.

**Verificación que queda**: aprobar algo en el portal y comprobar que
«Aprobado por» ya sale con el usuario real.

**Aviso para F-018**: su borrador vive en el worktree
`worktree-agent-ad862e62640d64553` y **heredó el criterio del corte SIN la
excepción de `undo_log.actor`**. Hay que refrescarlo contra `dev` después de
mergear, antes de darlo por bueno.

## Cierre de sesión · 2026-08-21

Trabajo hecho hoy, todo commiteado en `dev` (**`git push origin dev` PENDIENTE**):

1. **Verificación completa del despliegue del 2026-08-20** (sv3 y sv4, esquema
   con las 19 columnas, M1 de F-010, las 6 de F-016 §8.2, KPI de F-015, R7 y
   R12). Sin nada abierto.
2. **F-017 done, mergeada, desplegada y verificada en producción.**
3. **F-005 revisada** contra Azure: su primer objetivo ya estaba cumplido.
   **Pendiente de decisión del humano**: cerrarla o reescribirla como retirada
   de `graphkey_nobom.json`.
4. **F-009 eliminada** por decisión del humano; su lista de automejoras sigue
   viva en este fichero, sin feature propia.
5. **F-018 dada de alta**, con spec redactada **en un worktree sin integrar**.

### Por dónde seguir, en orden

1. `git push origin dev`.
2. Comprobar en el portal que **«Aprobado por» ya sale con el usuario real**
   (única verificación que queda de F-017).
3. **Integrar la spec de F-018** desde `worktree-agent-ad862e62640d64553`
   (commit `eee9d53`), refrescándola antes contra `dev`: heredó el criterio del
   corte SIN la excepción de `undo_log.actor`, y tiene material nuevo (el `oid`
   de `X-MS-CLIENT-PRINCIPAL-ID`). Luego `git worktree remove`.
4. ~~Decidir sobre **F-005**~~ — hecha y cerrada el 2026-08-25.
5. Cuando toque: el **correo de F-014 a RRHH**. La actualización del arnés ya
   no está pendiente: va por la 1.7.3.

## Lo que el humano tiene que decidir o hacer

1. **Verificaciones del despliegue**: las 6 de F-016 §8.2 y el KPI de F-015
   **SUPERADAS** en navegador el 2026-08-20 (sección anterior). Quedan: el
   contraste contra la BASE (`origen`, `is_active`, `created_by` y que el
   `hasta` sea un día después del escrito) y la **M1 de F-010**, los dos a la
   espera de la **regla de firewall** de `psql-albaranes-rs9k2`; el «último
   laborable 6 h» con `candef = 9` de verdad, que no llega hasta F-014; y la
   **limpieza** de las filas de prueba.
   Decisión pendiente: qué hacer con `DEFAULT_REVIEWER` (H1).
2. **Enviar la petición de F-014 a RRHH**: la condición ya se cumple (F-015
   desplegada). Texto aprobado en `progress/peticion_F-014.md`.
3. **F-017** (identidad real de Easy Auth): **spec escrita el 2026-08-20**, a
   la espera de aprobación del humano. Ver la sección «F-017 · spec escrita»
   más abajo. Mientras no exista, todas las filas de auditoría del portal
   siguen sellando `NULL` (H1).
4. **Dos dudas abiertas de F-016** (`design.md` §13): los tres normalizadores
   de DNI equivalentes de sv4 (¿feature de limpieza aparte?) y si las filas con
   `origen` `sigrid`/`sesame` serán editables cuando existan.
5. **Automejoras del arnés** acumuladas (lista abajo), ya sin feature propia:
   F-009 se eliminó el 2026-08-20 por decisión del humano. Varias con evidencia
   medida. Destino previsto: portarlas a `arnes-base` al actualizar el arnés.

## F-015 · done, en `dev` (2026-08-19)

Jornada del día por jornada semanal derivada del candef y último día laborable.
Resumen en `progress/history.md`; detalle en `progress/impl_F-015.md`,
`progress/mutacion_F-015.md` y `progress/review_F-015.md`.

Verificado por el reviewer: 1.195 tests, cobertura **99,4 %** (520/523),
mutación **259/237/22/0** (91,5 %). Regresión cero: con `candef = 8` —que hoy
son todos— no cambia el comportamiento de nadie. Por eso se puede desplegar
sin F-014.

## F-016 · done, en `dev` y desplegada (2026-08-19/20)

Pantalla `/admin/jornadas` en sv4: crear, editar, cerrar, desactivar y
reactivar las excepciones de jornada. Resumen en `progress/history.md`; detalle
en `progress/impl_F-016.md`, `progress/mutacion_F-016.md` y
`progress/review_F-016.md`.

Verificado por el reviewer ejecutando y recalculando: 799 tests en sv4 (134
nuevos) + 92 en la raíz, cobertura **98,5 %** (326/331), mutación **93/79/14/0**
(85 %). Cero cambios de schema, cero ficheros fuera de sv4, cero rutas nuevas
de catálogo, cero `DELETE`.

## F-014 · DEUDA IMPORTANTE, aparcada (2026-08-19)

Decisión del humano: no es crítico, lo ejecuta RRHH en Sigrid y lleva tiempo;
él avisará. La petición está redactada y **APROBADA** en
`progress/peticion_F-014.md` (rama `feature/F-014-candef-9-sigrid`), con un ⛔
en la cabecera.

**El orden importa**: primero F-015 desplegada, después el correo. Aplicar el
`candef = 9` en Sigrid con sv3/sv4 sin F-015 daría **−3 h/semana** de extra
negativa a esos 7 recursos; al revés no pasa nada. **Desde el despliegue del
2026-08-20 esa condición se cumple**: el correo ya se puede enviar en cuanto el
humano quiera.

Cuando se retome: enviar el correo (§7) → RRHH cambia el `candef` de 7 fichas y
el DNI de `MO/0037` → responde qué decide con `MO/0007` (de alta pero sin
partes desde 2026-02-04) → ejecutar V1/V2/V3 en solo lectura → segunda revisión
→ `done` → merge.

Hallazgos que no conviene perder: los códigos `MO/NNNN` **no identifican una
sola ficha** (bajo MO/0006, MO/0007 y MO/0008 hay homónimas de alta, misma
categoría, misma hora por defecto y también con `candef = 8`: solo las separa
`res.ide`); `MO/0031` tiene dos fichas de alta que registran en 2026 y ahí
desempata la categoría; y `MO/0037` sigue sin DNI (`res.conide = 0`).

## F-017 · spec escrita (2026-08-20), pendiente de aprobación

`specs/F-017-identidad-easy-auth/` con los tres ficheros. **Solo sv4**: se
comprobó que sv5 ya acepta el campo `usuario` (`Optional[str]`) y **solo lo
loguea** — no llega a ninguna columna de Sigrid, así que empezará a registrar
un nombre real sin un cambio de código. Cero cambios de schema: las siete
columnas de autor ya existen y la más estrecha es `String(120)`
(`undo_log.actor`, `empleado_jornada.created_by`/`updated_by`,
`empleado_alias.created_by`); un UPN cabe de sobra y el helper trunca a 120 de
una vez para todos.

**Ocho decisiones que el humano tiene que aprobar o rebatir** (detalle y
argumentos en `design.md` §11):

| # | Decisión propuesta |
|---|---|
| DA1 | Manda `X-MS-CLIENT-PRINCIPAL-NAME`; el token base64 es el suplente y **nunca** puede lanzar |
| DA2 | Se guarda el **UPN**, no el `oid`: la columna la leen personas (`parte_detail.html`, `admin_jornadas.html`) y no hay dónde meter el `oid`. Identidad inmutable ⇒ F-018 |
| DA3 | El actor se normaliza a **minúsculas** (los UPN son insensibles a mayúsculas; si no, un `GROUP BY` cuenta dos personas donde hay una) |
| DA4 | **ENMENDADA por el humano el 2026-08-20 y ya incorporada.** El fallback tiene **dos ramas**: sin desplegar ⇒ `local:<DEFAULT_REVIEWER>` / `local:sin-identidad`; **desplegado y sin cabecera ⇒ `sin-identidad`, sin prefijo, con WARNING por petición**. Motivo: escribir `local:` en producción no sería «honesto», sería **afirmar un origen falso** y taparía una caída de la autenticación en una columna. La operación se completa igual en las dos ramas |
| DA4 bis | Se distingue el entorno **sin variable nueva ni tocar Azure**: `CONTAINER_APP_*` presente **o** haber visto ya una cabecera de Easy Auth desde el arranque (segunda señal, red de seguridad de la primera). ⚠ **Supuesto de plataforma NO verificado en este repo**: nadie lee esas variables hoy ⇒ **T0 es una puerta** que lo comprueba con `az containerapp exec … printenv` **antes** de implementar, y si no aparecen, `blocked` y se consulta |
| DA5 | `DEFAULT_REVIEWER` se queda con el nombre, cambia el significado: pasa a ser la etiqueta de la sesión local. Renombrarla obligaría a tocar Azure para nada |
| DA6 | El test `test_f016_r13_auditoria` **se pone rojo a propósito** (T4, es la evidencia de que `_actor` manda) y se repara **fabricando la cabecera**, no parcheando el helper: `_actor` es una clausura dentro de `build_app` y no hay nada que `monkeypatch` alcance |
| DA7 | Las filas que escribe **sv3** (ingesta automática) NO se tocan: ahí el autor es el pipeline, no una persona |
| DA8 | **Aprobado por el humano.** `GET /whoami` devuelve actor, **por qué rama salió** (`cabecera-name` / `cabecera-token` / `local` / `sin-identidad-desplegado`), `entorno`, la señal que lo prueba y los **nombres** de las cabeceras presentes (nunca valores). Con la enmienda gana papel: es el único sitio donde se comprueba la detección de entorno **sin escribir una fila** |

**Filas históricas**: no se reescribe ni una (R22). Con H1 la decisión sale
más barata de lo previsto — no hay genéricos que traducir, hay `NULL`, que ya
dice la verdad. Y como a partir de la feature **siempre** hay actor (R7), el
corte queda exacto y gratis: `autor IS NULL` ⇔ «anterior a F-017». Se
documenta en `docs/referencia/partes-proyecto.md` (T10) con un hueco
`⛔ PENDIENTE: fecha de despliegue` que **rellena el humano al desplegar**.

**Ambigüedades encontradas que conviene que el humano sepa:**

0. **La enmienda mete un riesgo nuevo, y es el único de la feature que
   ensucia datos**: si en Azure no existieran las `CONTAINER_APP_*`, el
   portal se creería local y firmaría filas de producción como `local:…` —
   justo la mentira que la enmienda quiere evitar. El fallo es asimétrico
   (creerse desplegado en local es inocuo: `sin-identidad` + WARNINGs en un
   puesto de trabajo). Mitigado por tres vías: **T0** lo comprueba antes de
   implementar (y si falla, `blocked`), el arranque lo loguea, y la segunda
   señal lo corrige en cuanto entra el primer usuario autenticado. Aun así,
   el humano debe saber que la detección de entorno pasa a ser **una pieza
   con peso en la auditoría** que antes no existía.
1. **No está verificado que Azure inyecte `-NAME`** con el UPN: en local no
   existe la cabecera y en el repositorio no hay ni una referencia a
   `X-MS-CLIENT-PRINCIPAL`. Puede llegar el *display name*. No es un fallo
   (identifica igual) y `/whoami` lo resuelve en un minuto (M1), pero el
   humano debe saber que el valor exacto que acabará en la columna **no se
   puede confirmar hasta desplegar**.
2. **Alcance colateral no acotado del todo**: siete ficheros de tests de
   F-002/F-003/F-004 configuran `DEFAULT_REVIEWER="ana"` y alguno comprueba
   ese valor. **T1 los inventaría antes de tocar nada** en vez de descubrirlos
   a mitad, pero el número final de tests a ajustar no se sabrá hasta ese
   inventario.
3. **`docs/referencia/partes-proyecto.md` §5.4 está desactualizado**: dice que
   `created_by`/`updated_by` llevan `DEFAULT_REVIEWER`. Con H1 sabemos que
   llevan `NULL`. Se corrige en T10.
4. **`.env.example` de sv4 no está versionado** (el `.gitignore` ignora
   `*.example`), igual que pasó con `JORNADAS_ADMIN_ENABLED` en F-016: la
   documentación efectiva de `DEFAULT_REVIEWER` va al docstring y a
   `azure-apps/partes.md` (T11).
5. **Aviso para F-008**: esta feature confía en el texto en claro de la
   cabecera porque lo que decide es una *anotación*, no un permiso. Un **rol**
   leído igual sí sería una decisión de permiso y ahí esa confianza deja de
   ser gratis (`design.md` §8).

## Orden del backlog

1. **F-017** — identidad real de Easy Auth en sv4 (`pending`, prioridad 8).
   **Spec escrita** en `specs/F-017-identidad-easy-auth/` (2026-08-20), a la
   espera de que el humano apruebe las ocho decisiones DA1–DA8. Los once
   puntos exactos, verificados de nuevo contra el árbol: `app.py` líneas
   1675, 1769, 1804, 1859, 1862, 2279, 2305, 2319, 2338, 2348 y 2559.
2. **F-014** — `blocked`, solo la desbloquea RRHH.
3. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-011 jornada reducida
   (última; fuente candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-016 (NUEVO)**: las 6 verificaciones de
  `specs/F-016-admin-empleado-jornada/design.md` §8.2, con el portal levantado
  y PostgreSQL. La 6 (comportamiento del combo de trabajador en el navegador)
  no la cubre ningún test.
- **F-015 · T12** (desplegado el 2026-08-20; los logs de esquema de sv4 **y de
  sv3** ya están comprobados, los dos con 137 sentencias y sin errores): la tabla
  `empleado_jornada` con sus **19** columnas y el índice
  `ix_empleado_jornada_dni_norm`; un trabajador de la cuadrilla con viernes de
  6 h **sin** aviso de jornada incompleta y el KPI «9 h · 42 h/sem · último
  laborable 6 h»; y que un parte ya aprobado **no**
  cambie su desglose tras la primera pasada de sv3. Ojo: la cuadrilla sigue con
  `candef = 8` hasta F-014, así que ese punto solo se ve del todo después.
- **F-010:** M2/M3 cumplidas (137 sentencias en sv3 y sv4). **M1 pendiente**:
  índice `ix_parte_registros_deleted_at_utc` y recuentos 7/47/56/7, a la espera
  de la regla de firewall de PostgreSQL.
- **F-014**: la puerta ya está abierta (F-015 desplegada el 2026-08-20); queda
  enviar la petición cuando el humano decida.
- **F-002 (Azure):** validar en navegador la aprobación asíncrona (⏳ encolado →
  ✓ PT26/…, obra 0404 en modo pruebas), limpiar 0404 (`python
  prueba_escritura_sigrid.py limpiar --ejecutar` en sv5) y pasar sv5 a modo
  normal (`az containerapp update -n ca-sv5-transfer -g $RG --set-env-vars
  OBRA_PRUEBAS_FORZAR=false`).
- **F-003:** encendido cuando sesame-api esté desplegado (P2) — variables
  SESAME_* en sv3 y sv4 a la vez + secreto `sesame-api-key` en kv-partes. Ojo:
  encender contra URL muerta bloquea aprobaciones por diseño.
- **F-004:** 7 comprobaciones en navegador con Ctrl+F5 (pasos al final de
  `progress/impl_F-004.md`).
- **F-013:** validar el Excel `services/partes-front/logs/
  festivos_por_trabajador_2026.xlsx` (no versionado): Alicante 8/21 y
  asignaciones por centro.
- **sesame-api (otro repo, del humano):** commitear el árbol P2 (incluye el fix
  `daysOff` del 2026-08-18), desplegar, doc en azure-apps (P3);
  `contract_not_found` → 404 en vez de 502.
- **Sesame HR (RRHH):** completar el calendario Alicante; contratos vacíos
  (0/218) — decidir si se cargan.
- **Cambio de modelo Gemini** en sv2 (comando dado; actualizar
  `infra/create_capps_partes.ps1:38`).

## Automejoras del arnés pendientes (⇒ genéricas a `arnes-base`)

> **F-009 se eliminó de `harness/features.json` el 2026-08-20** por decisión
> del humano. Esta lista NO desaparece con ella: sigue siendo el registro de lo
> que hay que portar a `arnes-base`. Varios puntos (1, 2, 3 y 7) son de la
> campaña de mutación y **probablemente ya vengan resueltos en el arnés
> 1.6.0**, que la rehace entera; confirmarlo con
> `progress/analisis_arnes_1.6.2.md` antes de implementar ninguno.
>
> Los **dos puntos originales de F-009**, que NO son de mutación y se habrían
> perdido al borrar la ficha, se conservan aquí:
>
> - **C4 bis**: cuando un fichero del alcance con muchas líneas cambiadas
>   genera **0 mutantes**, exigir evidencia alternativa (fase RED específica
>   sobre ese fichero).
> - **C3/C4 + `init.sh`**: cruzar los imports nuevos de terceros del diff
>   contra el `requirements.txt` del manifiesto de despliegue del servicio que
>   los importa. Habría cazado en automático el crash-loop de `azure-*` de
>   F-002.

1. **La más rentable, confirmada con datos por F-015 y anotada desde F-010**:
   `harness/mutacion.py` ejecuta solo la suite del servicio dueño del fichero
   mutado, así que **el guardián de una copia gemela nunca mata mutantes**
   (vive en `tests/` de la raíz). Fueron **27 de los 48 supervivientes** de la
   2.ª campaña de F-015, todos falsos «equivalentes». Arreglo: ejecutar también
   la suite de la raíz (~4 s aquí) o, mínimo, avisar cuando el fichero mutado
   tenga copia gemela declarada en `CLAUDE.md`.
2. **El presupuesto de mutación por mutante es engañoso** (F-015): con 16
   evaluadores y una suite de ~80 s, el timeout de 120 s de `rigor.json`
   convirtió 100 mutantes en «timeout», que **no es una medición**. Debería
   escalar con la concurrencia o avisar cuando los timeouts pasen de un umbral.
3. **`progress/mutacion_*.md` debería registrar qué suite se ejecutó** por
   fichero (reviewer de F-016): sin eso, en una feature que toque dos servicios
   el hueco de (1) no se detecta sin recalcular.
4. **C4 de `CHECKPOINTS.md` podría pedir un recuento mecánico
   test-por-requisito** sobre los nombres `test_fXXX_rN_*`, en vez de fiarse de
   la tabla de trazabilidad de la spec (reviewer de F-016).
5. **Checkpoint para features cuyo entregable es una petición a un tercero**
   (reviewer de F-014): clave unívoca verificada, apartado «qué NO se toca»,
   verificación escrita ANTES con control de daños, resultado esperado en TODOS
   los escenarios, barrido de datos sensibles porque el documento sale del
   repositorio.
6. **Generalizar «si el entregable es una medición, el reviewer la re-ejecuta
   en vez de leerla»** (reviewer de F-014): es lo que destapó su defecto D1.
7. **Desconfiar por defecto de los supervivientes de una copia duplicada**, en
   `.claude/agents/reviewer.md` (reviewer de F-015).
8. **Fixture de app compartida en sv4** (deuda transversal, no del arnés): la
   suite pasó de ~52 s a ~114 s porque cada test de endpoint levanta `build_app`
   entera. Patrón heredado de F-002/F-003/F-004.

Las anteriores de F-013 (AM-1..3), F-004 y F-010 siguen en `history.md`.

## Notas de contexto

- **Deuda detectada el 2026-08-19**: `services/partes-front/
  consulta_reshor_recursos.py` tiene 4 DNIs y nombres de personas reales
  **hardcodeados y versionados** (líneas 27-31) y apunta a una ruta `.env` de
  otro repositorio. Pendiente de decisión del humano.
- **`JORNADAS_ADMIN_ENABLED` no está en ningún fichero versionado**: el
  `.gitignore` de sv4 ignora `*.example`. Default `True` en el código y
  documentada en `azure-apps/partes.md`. No es un olvido: el implementer evitó
  un `git add -f` y el reviewer le dio la razón.
- F-013 (2026-08-18): 218 empleados; festivos OK (Madrid 196, Tomares 15,
  Sevilla 4, Málaga 2, Alicante 1 parcial); contratos en Sesame: NINGUNO ⇒
  jornada/reducida sin fuente en Sesame; F-011 repriorizada a baja por eso.
- F-012 (2026-08-18): decisiones firmes del humano sobre la jornada semanal, ya
  implementadas por F-015.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano); no proponer
  push.

---

## F-017 · Identidad real de Easy Auth (sv4) — pendientes del humano

Rama `feature/F-017-identidad-easy-auth`. Implementación terminada (T0–T14),
suite en verde, **pendiente de review**. Informe: `progress/impl_F-017.md`.

### ⚠ DECISIÓN PENDIENTE — R14/R15 nombran una columna que nadie escribe

Verificado contra el árbol al implementar T6 (y coincide con lo que encontró
el agente de F-018 por su cuenta):

- `undo_log.actor` **existe pero no la escribe nadie**: `_record_undo` ni
  siquiera acepta un actor.
- Las cuatro operaciones de R14/R15 —los tres borrados y el alta manual—
  **no generan ninguna fila de `undo_log`**. Solo la generan las ediciones.
- `crear_parte_manual` **acepta `by=` y lo ignora**: el parámetro no aparece
  en su cuerpo.

Lo implementado es lo que manda `design.md` §5.2: entregar `_actor(request)`
por el parámetro `by=`. Para los tres borrados eso llega de verdad a
`deleted_by`; para el alta manual se queda en la puerta del repositorio.

**No se resolvió por cuenta propia**, y el motivo es que las dos salidas
posibles se salen del alcance aprobado:

| Salida | Por qué se paró |
|---|---|
| Que los borrados escriban en `undo_log` | Hay que **crear** filas de historial que hoy no existen: payload de restauración, `undo_last` sabiendo deshacerlas y entradas nuevas en el widget de deshacer. Es funcionalidad nueva, y un log de acciones es **F-018** |
| Que `crear_parte_manual` use su `by=` | **No hay dónde escribirlo**: ni `parte_documents` ni `parte_registros` tienen columna `created_by` (solo la tienen `empleado_alias` y `empleado_jornada`). Exigiría **columna nueva** ⇒ cambio de schema en las dos copias gemelas del ORM ⇒ prohibido por la spec y por `CLAUDE.md` |

**Consecuencia que hay que conocer**: el criterio del corte (`autor IS NULL`
⇔ «anterior a F-017») vale para las columnas de autor que sí se escriben,
**no para `undo_log.actor`**, que seguirá siempre a `NULL`. Queda dicho así,
sin redondear, en `docs/referencia/partes-proyecto.md` §5.7 punto 3.

### Verificaciones MANUAL pendientes

- **M1 bis — YA EJECUTADA en T0 (2026-08-20), resultado POSITIVO.** Las cuatro
  variables `CONTAINER_APP_NAME` / `_REVISION` / `_REPLICA_NAME` / `_HOSTNAME`
  **existen** en `ca-sv4-front`. La señal A de R5c es un hecho verificado, no
  un supuesto; no hace falta la alternativa `ENTORNO=produccion`.
  Comprobado **sin volcar el entorno**, una variable por invocación:
  `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_NAME"`
  (ídem con las otras tres). **No usar `printenv` a secas**: vuelca los
  secretos resueltos desde Key Vault.
- **M1 — tras desplegar.** Abrir `https://<fqdn de ca-sv4-front>/whoami` con
  la sesión de Entra iniciada y comprobar tres cosas: `actor` es el correo/UPN
  de quien mira, `origen` es `cabecera-name` y `entorno` es `desplegado`.
  Lecturas posibles:
  - `origen = cabecera-token`: la cabecera `-NAME` no llega y el suplente hace
    su trabajo. Correcto, pero **anótalo**.
  - `origen = sin-identidad-desplegado`: Easy Auth no inyecta nada.
    **Incidente**: la feature funciona (no miente), pero la autenticación del
    portal está rota. Parar y avisar.
  - `origen = local` o `entorno = local`: la detección de R5c ha fallado en
    Azure y el portal estaría firmando filas de producción como locales.
    **Parar y avisar de inmediato**: es el único fallo de esta feature que
    ensucia datos. El campo `senal_despliegue` dice qué se buscó.
- **M2 — tras desplegar.** Aprobar un parte de prueba desde el portal y
  comprobar en la base `partes`:
  `SELECT id, approved_by, approved_at_utc FROM parte_documents WHERE approved_at_utc IS NOT NULL ORDER BY approved_at_utc DESC LIMIT 5;`
- **M3 — tras desplegar.** Borrar una línea de prueba y comprobar:
  `SELECT created_at_utc, action, actor FROM undo_log ORDER BY id DESC LIMIT 5;`
  **Ojo**: por lo dicho arriba, `actor` saldrá `NULL` y el borrado **no**
  generará fila de `undo_log`. La comprobación útil hoy es sobre
  `parte_registros.deleted_by`.
- **M4 — antes y después de desplegar.** Que las filas anteriores sigan
  intactas (R22): el número debe ser **el mismo** las dos veces:
  `SELECT count(*) FROM parte_documents WHERE approved_at_utc IS NOT NULL AND approved_by IS NULL;`

M2, M3 y M4 necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya
está pendiente más arriba en este mismo documento.

### Otros pendientes de F-017

- **La fecha del corte la rellena quien despliegue.**
  `docs/referencia/partes-proyecto.md` §5.7 tiene el hueco marcado como
  `⛔ PENDIENTE: fecha de despliegue`, y
  `tests/test_f017_r23_corte_documentado.py` se pondrá **rojo** cuando se
  cambie, a propósito: obliga a actualizar el test en el mismo trabajo.
- **`DEFAULT_REVIEWER` cambia de significado, no de nombre**: ya no es «quién
  firma el portal» sino la etiqueta de la sesión local (`local:<valor>`).
  Sigue sin estar configurada en Azure y **no hace falta configurarla**.
- **Nota para F-018** (aviso recibido del coordinador, no aplicado aquí a
  propósito): si F-018 llama a `_resolver_identidad` más de una vez por
  petición, saldrán varios WARNING de R5b. Hoy no ocurre —cada endpoint pide
  el actor una sola vez—, así que memoizar sería resolver un problema que aún
  no existe. Cuando F-018 lo necesite, son tres líneas en
  `_resolver_identidad` y no cambia ninguna firma.

---

## Actualización del arnés: 1.4.0 → 1.7.2 (2026-08-21)

Rama `chore/arnes-1.7.2`, sin push. Origen: `arnes-base` (payload 1.7.2 del
2026-08-21). Ejecutado `instalar_arnes.ps1 -Modo actualizar`; los seis ficheros
«adaptados» se restauraron a la versión de `partes` y las novedades genéricas
se portaron a mano, bloque a bloque. Backup del instalador en
`%LOCALAPPDATA%\arnes-base\backups\partes\20260821-232232` (16 ficheros).

**Qué entra**: puerta de tamaño del papeleo (`harness/tamano.py`, sección
7 quater de `init.sh`), `BACKLOG.md` generado desde `features.json`
(`harness/backlog.py`, sección 3 bis), centinela de campaña de mutación en
curso (sección 1 bis), motor de mutación de la 1.6.0–1.7.2 (línea base que no
puede mentir, mutación de `is`, sin envenenar el árbol con bytecode,
`--ficheros`, dimensionado automático de timeout y workers), reglas RM1–RM6 del
reviewer en `CHECKPOINTS.md` y 16 tests nuevos del arnés en `tests/`.

**Qué se conservó de `partes`**: las tres adaptaciones de `init.sh`
(`REQUIERE_ENV=0`, cabeceras de las secciones de configuración y 9), el punto
C4 de dominio de `CHECKPOINTS.md` (empleado ≠ recurso, incidencias, schema
duplicado), `docs/CONVENTIONS.md` entero (la plantilla no cambió desde 1.4.0) y
todo el contenido propio de `CLAUDE.md`. Los cuatro agentes de `.claude/agents/`
no tenían adaptación local: se comprobó antes de dejar que el instalador los
pisara.

**Rigor**: `nivel_por_defecto` pasa de `critico` a `estandar`, pero **las 17
features declaran su nivel explícitamente**, así que ninguna cambia de
exigencia. Lo que sí cambia de aquí en adelante: las campañas de nivel
`estandar` van **muestreadas a 20 mutantes con semilla fija** (`--max-mutantes 0`
para la campaña entera) y sus números **no son comparables** con los de
campañas anteriores. Tampoco lo son los tiempos: desde la 1.7.2 el timeout por
mutante se deriva de la línea base medida.

**Verificado**: `bash harness/init.sh` en verde con el arnés v1.7.2 — 401 tests
pasados (138 antes de la actualización) y 1 saltado, servicios sv3/sv4/sv5 en
verde por caché, `BACKLOG.md` generado. `python -m harness.mutacion --estado` y
`python -m harness.tamano --feature F-018` responden bien.

**Pendiente / sabido**: `ruff` sube de 468 a 496 avisos, los 28 nuevos en el
código del arnés recién entrado (deuda del genérico, no bloquea). Nada que
propagar de vuelta a `arnes-base`: esta actualización solo consume.

## Actualización del arnés: 1.7.2 → 1.7.3 (2026-08-25)

Rama `chore/arnes-1.7.3`. Correctivo de la puerta de tamaño que estrenó la
1.7.0: la sección 7 quater medía también el papeleo de features **`done`**, y
una feature cerrada que declara la rama base como suya dejaba el portero en
rojo permanente en `dev`. El snippet descarta ahora la ficha si su `status` es
`done` y el N/A lo dice con sus palabras. Encontrado en `porcentajes`, no aquí:
en `partes` ninguna feature declara `dev` o `main` como rama, así que el
portero nunca llegó a ponerse rojo por esto.

Toca `harness/init.sh` (portado a mano, conservando las tres adaptaciones de
`partes`), `tests/test_tamano.py` y `harness/VERSION`. Verificado:
`bash harness/init.sh` en verde con v1.7.3, 402 tests pasados y 1 saltado.

## F-005 · GRAPH_KEY en Key Vault: constancia de la comprobación (2026-08-25)

Rama `feature/F-005-graphkey-keyvault`. Feature de **limpieza documental**
(`sdd: false`, rigor `documental`): **no se toca código de producción**. Queda
aquí la constancia que pide su criterio A4.

### Lo comprobado contra Azure (solo lectura, sesión de `pgris@ruesma.es`)

| Fecha | Qué se comprobó | Resultado |
|---|---|---|
| 2026-08-20 | Los **tres** servicios que usan Graph (`ca-sv1-poller`, `ca-sv3-persistencia`, `ca-sv4-front`) | `GRAPH_KEY` llega como `secretref:graph-key`, y el secreto de la Container App es una **referencia** a Key Vault (`keyVaultUrl` informado), **no una copia**. Ningún valor en claro. |
| 2026-08-25 | El secreto `GRAPH-KEY` en el Key Vault de `rg-partes-dev` (`$KV`) | **Existe y está habilitado**. Creación y última actualización: `2026-06-22T13:59:10+00:00`. |

sv5 no usa Graph. Es decir: el objetivo original de la feature —sacar la
credencial de las variables de entorno en claro— **ya estaba cumplido de
hecho** antes de abrirla; lo que quedaba era la limpieza.

### Lo comprobado en el árbol

- **Ningún script de `infra/` lee `graphkey_nobom.json`.**
  `add_secrets_partes.ps1` pide el JSON por consola con
  `Read-Host -AsSecureString` y lo sube con `az keyvault secret set`, sin
  tocar disco. `create_capps_partes.ps1:63,73`, `create_sv1_poller.ps1:44,49`
  y `create_sv4_front.ps1:41,62` montan `GRAPH_KEY=secretref:graph-key` sobre
  un `keyvaultref` resuelto con la identidad gestionada `id-partes-dev`.
- **Nunca entró en git**: `git log --all -- infra/graphkey_nobom.json` no
  devuelve nada, y sigue cubierto por `.gitignore:15`.
- **Borrado del disco** el 2026-08-25 (criterio A1). El valor vive en el Key
  Vault, ya verificado arriba.

### HALLAZGO H1, RESUELTO: la segunda copia del secreto en disco

`infra/partes-infra.zip` (33 KB, del 2026-07-26, **no versionado**, cubierto
por la regla `*.zip` del `.gitignore`) contenía dentro `graphkey_nobom.json`
con `tenant_id`, `client_id` y un `client_secret` no vacío. Comprobado sin
imprimir los valores: 32 entradas, una foto de `infra/` del 2026-06-22, y todo
lo demás que llevaba está en git en versiones más nuevas.

**Borrado el 2026-08-25 por decisión del humano**, entero. En el árbol no
queda ningún rastro de `graphkey*` (`find . -name "graphkey*"`, vacío), así
que el objetivo real de A1 —que la credencial de Graph no esté en claro en el
disco— sí está conseguido.

### F-005 · CERRADA, APROBADA por el reviewer (2026-08-25)

Ronda 1: `CHANGES_REQUESTED` por **dos frases falsas** en documentación —el
defecto que esta feature existía para eliminar—. `README.md` atribuía
`PG-PASSWORD` a `add_secrets_partes.ps1` (la carga `fase1_infra_partes.ps1:151`)
e `infra/README_partes.md` decía que el script «solo conoce el nombre del
secreto, nunca su valor» (el valor viaja en `az keyvault secret set --value`).
Corregidas en `ad770be` y `861c0d1`, más `65430cd` en `azure-apps`. El
implementer encontró además que **su propio informe repetía las dos frases** en
las tablas de A2 y A3, y las arregló ahí también.

**La puerta de tamaño del arnés 1.7.3 mordió por primera vez** en este
repositorio: `progress/review_F-005.md` salió a 151 líneas contra un tope de
140 y dejó el portero en KO. El implementer NO lo recortó —recortar el informe
de quien te revisa para que tu entrega salga verde es justo lo que la puerta
impide—; lo recortó el reviewer a 140/140 y lo commiteó (`0d7fd31`).

Veredicto final **APROBADO** (`progress/review_F-005.md`). Verificaciones
independientes del reviewer que conviene no perder: barrido de `git ls-tree`
sobre **todos** los commits alcanzables (el nombre `graphkey_nobom.json` no
aparece en ningún árbol de la historia), barrido de secretos sobre el diff
completo `dev...HEAD` (cero hallazgos) y contraste línea a línea de cada
afirmación de los documentos contra los scripts de `infra/`.

`bash harness/init.sh` en verde: 402 pasados / 1 saltado, cobertura N/A por
nivel `documental` con su motivo impreso, puerta de tamaño 206/220 y 140/140.

Dos cosas que el reviewer deja apuntadas y **no** entran aquí:

- **Deuda preexistente**: `add_secrets_partes.ps1` pasa el secreto por
  `--value`, que lo deja visible en la línea de comandos del proceso. Se
  arreglaría con `--file` o con `Az.KeyVault`.
- **Automejora del arnés (genérica ⇒ `arnes-base`)**: que `CHECKPOINTS.md`
  obligue, en nivel `documental`, a que cada afirmación de un documento sobre
  cómo se ejecuta algo cite el fichero y la línea que la respalda. Aquí todo
  pasó en verde y el defecto era una frase falsa.

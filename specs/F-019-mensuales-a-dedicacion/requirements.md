<!-- specs/F-019-mensuales-a-dedicacion/requirements.md -->
# F-019 · Horas de los mensuales a dedicación — Requisitos (EARS)

Origen: petición del humano del 2026-09-29, con siete decisiones cerradas
(`harness/features.json`, entrada F-019; no se reabren). Los cinco puntos
abiertos y tres más que salieron al diseñar son **DA1–DA8** (`design.md` §8):
**pendientes del humano**. Estos requisitos están escritos con la
recomendación de cada DA; si el humano elige otra, se reescriben antes de
implementar. Servicios: **sv5, sv4 y sv3** (`design.md` §1). Rigor **crítico**.

Vocabulario: «mensual» = recurso con algún código de hora `M*` en `reshor`
(decisión 1, el mismo criterio que dedicación, P1); «línea» = fila activa de
`parte_registros`; «bandeja» = tabla `dedicacion_bandeja` de la base
`partes`; «interruptor» = ajuste de sv5 `MENSUALES_A_DEDICACION` (DA8).
Tests `test_f019_rN_*`, sin red ni BBDD (dobles de sigrid-api, SQLite en
memoria con el ORM, `TestClient`). Datos reales (lectura de Sigrid del
2026-10-02): 195 recursos persona de alta con `M*`; 32 de ellos son `MCAP` +
`HECAP`; ninguno tiene `HL*` ni dos `M*`; los 163 sin `HE*` tienen todos `M*`.

## A · Enrutado en sv5 (DA7)

- **R1** (estado). MIENTRAS el interruptor esté apagado (valor por defecto),
  `ReglasRegistro` debe decidir exactamente lo mismo que antes de F-019 para
  cualquier línea (R1–R5 del docstring actual).
- **R2** (evento). CUANDO el interruptor esté encendido y la línea tenga
  recurso y ese recurso tenga un código `M*`, la acción debe ser
  `dedicacion`, con `codigo_mes` = ese código, para: horas ordinarias,
  horas extra si el recurso no tiene `HE*`, e incidencias **de cualquier
  rol** (inicio, intermedio y fin: decisión 2).
- **R3** (evento). CUANDO el interruptor esté encendido y una línea **extra**
  sea de un mensual que además tiene `HE*` (capataz `MCAP`+`HECAP`), debe
  seguir R4 de hoy: `escribir` con su `HE*` (DA4).
- **R4** (ubicuo). Antes que R2 siguen mandando, por este orden, la omisión
  previa por verificación del recurso (F-023), el tipo de hora no
  reconocido en una línea que no es incidencia, la falta de recurso y la
  falta de horas en una línea que no es incidencia: se omiten con su motivo
  de siempre.
- **R5** (evento). CUANDO una línea que iría a `dedicacion` ya tenga línea
  en Sigrid por su `synckey`, la acción debe ser `ya_registrado`, no
  `dedicacion`: Sigrid manda y nada se cuenta dos veces.
- **R6** (ubicuo). Una acción `dedicacion` no escribe en Sigrid, no abre
  parte, no resuelve cuenta analítica y no participa en conflictos.
- **R7** (ubicuo). El preflight de sv5 debe incluir las acciones
  `dedicacion` (con `codigo_mes`) y `resumen.dedicacion` con su número.
- **R8** (ubicuo). El resultado de sv5 (HTTP y `q-transfer-result`, fuente
  única `resultado_a_dict`) debe llevar `dedicacion`: lista de
  `{registro_id, recurso_ide, codigo_mes}`; vacía con el interruptor
  apagado y en el resultado fallido.

## B · La bandeja (DA1, DA2)

- **R9** (evento). CUANDO sv4 aplique un resultado de sv5 (por cualquiera de
  los dos canales) con entradas en `dedicacion`, debe, en la MISMA
  transacción, dejar cada línea en `sigrid_estado = 'dedicacion'` con motivo
  «enviada a dedicación (`<codigo_mes>`)» y escribir su fila en la bandeja.
- **R10** (ubicuo). La fila de la bandeja lleva, de la línea: `recurso_ide`,
  `fecha_int`, `anio`, `mes`, obra (`obra_ide`, `obra_codigo` y la empresa
  del parte), partida (`partida_ide`, `partida_cod`), `tipo` (`normal`,
  `extra` o `incidencia`), `horas` tal cual (también negativas y en
  festivos: decisión 3), `incidencia_codigo` y su clase de
  `config/incidencias.yaml` (o nula); del resultado: `codigo_mes` y
  `prueba` (= `forzada_pruebas`); y quién y cuándo. Nunca nombre ni DNI.
- **R11** (evento). CUANDO la línea no tenga fila, debe crearse con
  `version = 1` y `vigente = true`.
- **R12** (evento). CUANDO la línea ya tenga fila vigente con el mismo
  contenido, su fila no debe cambiar (ni `version` ni fechas): reaplicar el
  mismo resultado es inocuo.
- **R13** (evento). CUANDO la línea tenga fila retirada o con otro
  contenido, debe actualizarse con `vigente = true` y `version + 1`.
- **R14** (no deseado). SI falla la escritura de la bandeja, ENTONCES la
  línea no debe quedar en `dedicacion` (rollback de la transacción) y el
  error debe propagarse como cualquier fallo de la traza (el mensaje de
  cola se reintenta).

## C · El estado en el portal (decisión 7, DA5)

- **R15** (ubicuo). `dedicacion` congela la línea igual que `registrado`, en
  sv4 (`congelacion.py`, línea y documento) y en sv3 (`esta_congelado`), con
  un motivo que diga que está en dedicación y que se libera con «Retirar de
  dedicación». El guardián de raíz de F-024 debe compararlo en las dos.
- **R16** (ubicuo). Vaciar la papelera o eliminar definitivamente no debe
  borrar una línea en `dedicacion` (como `registrado`, F-004 R12).
- **R17** (evento). CUANDO se apruebe una selección, las líneas en
  `dedicacion` no deben viajar a sv5: se cuentan en `excluidas.dedicacion`
  con detalle, y si no queda nada el 422 lo dice.
- **R18** (ubicuo). El listado del modal de aprobación debe mostrar las
  acciones `dedicacion` con estado «a dedicación» y su motivo; no suman en
  las horas que se escribirán en Sigrid.
- **R19** (ubicuo). Las vistas de obra y de trabajador deben pintar
  `dedicacion` como «→ dedicación» (con el motivo en el `title`), nunca
  como «omitido», con el botón «Retirar».
- **R20** (ubicuo). «Marcar pendiente» un parte con líneas en `dedicacion`
  sigue permitido y no las retira (como `registrado`, F-004 R10/R11).

## D · Retirada y reaprobación (DA5)

- **R21** (evento). CUANDO se llame a `POST /api/dedicacion/retirar` con
  `registro_ids` y `ambito`, sv4 debe validar el ámbito como la aprobación
  (F-022: un id ajeno es 422 sin tocar nada) y, para cada línea en
  `dedicacion`, en una transacción: fila de la bandeja a `vigente = false`,
  `version + 1`, `retirado_por`/`retirado_at_utc`; línea a
  `sigrid_estado = NULL` y motivo «retirada de dedicación».
- **R22** (ubicuo). Las líneas del ámbito que no estén en `dedicacion` no se
  tocan y se devuelven contadas en `no_aplica`.
- **R23** (evento). CUANDO una línea retirada se reapruebe, debe seguir el
  camino normal (R2 o, con el interruptor apagado, las reglas de siempre) y
  su fila debe volver a `vigente` con `version + 1` (R13).
- **R24** (ubicuo). El autor de la retirada es `_actor(request)` (F-017).

## E · Acceso de dedicación (DA1, DA3)

- **R25** (ubicuo). El repositorio debe traer
  `infra/sql/01_dedicacion_lectura.sql`, idempotente, para que lo ejecute
  **el humano** con `psql` en la base `partes`: `GRANT CONNECT` a la base,
  `USAGE` en `public` y `SELECT` **solo** sobre `dedicacion_bandeja` al rol
  que se le pase por variable; y las comprobaciones de lectura de R26.
- **R26** (no deseado). SI el script contiene `CREATE ROLE`, `ALTER ROLE`,
  `ALTER SYSTEM`, `CREATE EXTENSION`, `SUPERUSER`, un privilegio distinto de
  `SELECT` sobre una tabla, otra tabla que `dedicacion_bandeja`, una
  contraseña o un host, ENTONCES el test estático debe fallar.
- **R27** (ubicuo). Ningún servicio ni test ejecuta `GRANT`: el arranque de
  sv3 y sv4 solo crea la tabla (`create_all` + DDL complementario).

## F · Lo que no cambia

- **R28** (ubicuo). sv1 y sv2 no cambian. Los no mensuales se registran
  exactamente igual. sv5 sigue siendo el único que escribe en Sigrid y sigue
  sin BBDD. partes no calcula porcentajes ni lee la base `dedicacion`.
- **R29** (ubicuo). Las demás tablas no cambian; `orm_models.py` sigue
  byte-idéntico en sv3 y sv4 y el guardián de F-010 pasa a seis tablas con
  la lista literal de columnas de la bandeja.

## G · Documentación

- **R30** (ubicuo). `docs/ARCHITECTURE.md`: semántica 15 (mensuales a
  dedicación: criterio, interruptor, bandeja, retirada) y «seis tablas» en
  la 7. `docs/referencia/partes-proyecto.md`: §3.5 (R1–R3 con el
  interruptor) y la tabla nueva en §5.
- **R31** (ubicuo). `azure-apps/partes.md` (repositorio aparte, commit
  local): nota de cabecera F-019, la bandeja como **lo que exponemos**
  (contrato de columnas, quién lee y con qué permiso), la variable de sv5 y
  «qué se rompe si cambia» (criterio `M*` compartido con dedicación).

## H · Fase RED exigible

Traza RED en `progress/impl_F-019.md` para **R1, R2, R3, R4, R5, R8, R9,
R12, R13, R14, R15, R17, R21, R22 y R26**. R1 se fija con tests de
caracterización **antes** de tocar `reglas_registro.py` (deben pasar en
verde contra el código de hoy y seguir en verde después).

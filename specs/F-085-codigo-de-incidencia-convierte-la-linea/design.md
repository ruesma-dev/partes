# F-085 · Diseño

**Nivel de rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`): escribe en
producción, en `hmores` de Sigrid (`ruesma`). Parte A: lo que sv4 decide (`es_incidencia`,
`tipo_hora`) es lo que sv5 escribe (`reglas_registro.py`), y sv5 gana una omisión. Parte B: un
`UPDATE` nuevo sobre líneas CI* (`sigrid_write_client.stmt_mover_linea`, `registro_pipeline.py`).
Si D1 = (a), las dos features son `critico` por el mismo disparador.

## 1. Contexto y causa (contrastado con `dev` 0a77900)

Caso 0678, recurso 2777451, parte PT26/00137. La 25012 (18/11, 8 h normales) pasó a CIA en el
portal y siguió `normal`: `set_registro_hora` (`parte_repository.py` ≈3288) solo guarda `hora_*`,
y `tipo_hora_de_codigo("CIA")` da `normal` (F-066 R13/R14: hueco de spec). Todo lo demás mira
`es_incidencia`: la matriz (≈1600, necesita `incidencia_codigo`), la columna Tipo
(`obra_detail.html` ≈239, `trabajador_detail.html` ≈284), la racha (`_roles_de_racha` ≈2583) y
sv5 (`reglas_registro.decidir`: rama de horas ⇒ «sin horas» con 0 h, o `_elegir` toma el primer
HL* y escribe HLOF con 8 h: hmores 416574, `partes:25012`). sv3 (`recurso_conciliador._overwrite`
≈328) pisó la CIA manual con HLOF porque no mira `hora_match_method`; la partida sí lo respeta
(`partida_conciliador.py` ≈150). sv3 restaura `horas = horas_orig` en toda fila no congelada con
`horas_orig` (`sqlalchemy_parte_repository.py` ≈583): una incidencia convertida debe dejarlo nulo.
Racha: sv5 mueve el CIZ (F-060) pero nunca un CI*; ante un inicio posterior ya registrado solo hay
`racha_desordenada` (F-060 R10, DA7). Estado medido: 18/11 HLOF 8 h (416574), ninguna CIA (la del
19, 416122, y su CIZ 416123 se borraron a mano en Sigrid), CIZ el 25/11 (416563). Portal: 25012
`registrado` normal con CIA, 25096 (19/11) `borrado_sigrid`, 25405 (21/11) sin registrar.

## 2. Parte A · sv4 (`services/partes-front/`)

**Modificar**
- `application/services/clase_hora.py`: `PREFIJO_INCIDENCIA = "CI"`, `CODIGO_FIN = "CIZ"`,
  `es_codigo_incidencia(codigo) -> bool`, `es_codigo_fin(codigo) -> bool` (R1). `tipo_hora_de_codigo`
  no cambia: quien decide antes es `conversion_clase`.
- `infrastructure/database/parte_repository.py`:
  - `_REG_UNDO_FIELDS` + `incidencia_codigo` (R10). Las entradas viejas sin la clave no la
    restauran (`_apply_reg_snapshot` ya mira `if f in snap`).
  - `set_registro_hora(..., clase: ClaseNueva)` aplica la `ClaseNueva` y devuelve
    `ResultadoHora | None` (None = no existe) con `clase_cambiada`, `tipo_hora`, `es_incidencia`,
    `incidencia_codigo` y el `(recurso, fecha_int)` de la línea (`_recurso_de`). Con cambio de
    clase la acción de deshacer es `registro_clase` y el snapshot añade `_REG_UNDO_MARCAS`
    (`horas_orig`, `extra_auto`); sin él, `registro_hora` como hoy (R10).
  - `undo_last`: para `registro_clase` devuelve `document_ids` = `documentos_de_los_dias` de las
    líneas restauradas (R11).
- `infrastructure/persistencia/recalculo_publisher.py`: `MOTIVO_CODIGO_INCIDENCIA =
  "codigo_incidencia"`, `MOTIVO_DESHACER_CODIGO_INCIDENCIA = "deshacer_codigo_incidencia"`.
- `interface_adapters/web/app.py`, `set_registro_hora`: tras `catalog.get_by_ide`, llama a
  `conversion_clase.decidir` con `app.state.tabla_incidencias`; su `error` ⇒ 400 (R5, R6) antes de
  tocar nada. Respuesta de R9. Con `clase_cambiada`, `_pedir_recalculo_compartido(
  repository.documentos_de_los_dias(pares), MOTIVO_CODIGO_INCIDENCIA, actor)`; con varias líneas
  (`bulk`), un pedido por llamada (cada PATCH es una petición; el compartido de F-049 los agrupa).
  `undo_apply`: rama `registro_clase` como la de `celda_edit` (R11).
- `static/app.js`, `onChange`: si algún resultado trae `clase_cambiada`, `window.location.reload()`;
  si no, como hoy (R13).

**Crear**
- `application/services/conversion_clase.py` (application, puro, sin E/S): `ClaseNueva`
  (`es_incidencia`, `tipo_hora`, `incidencia_codigo`, `vaciar_horas`, `cambia`, `error`) y
  `decidir(*, es_incidencia, incidencia_codigo, tipo_hora, codigo, tabla) -> ClaseNueva`:
  1. `es_codigo_fin` ⇒ `error = MOTIVO_CIZ_NO_SE_ELIGE` (R5).
  2. `es_codigo_incidencia` sin letra en `tabla.por_sigrid` (o sin tabla) ⇒ `error` R6.
  3. Con letra ⇒ forma canónica; `cambia` si no era incidencia o la letra difiere (R2, R3).
  4. Incidencia + código con clase (`tipo_hora_de_codigo` no None) ⇒ vuelta atrás (R4).
  5. Si no, la regla de F-066 tal cual (R7; una incidencia sin código no cambia, F-066 R15).
- `tests/test_f085_conversion.py` (unit + integración con SQLite en memoria y `TestClient`),
  `tests/test_f085_app_js.mjs` o el patrón node de F-066 para R13.

## 3. Parte A · sv3 (`services/partes-persistencia/`)

- `application/services/recurso_conciliador.py`, `_overwrite`: si `reg.get("hora_match_method")
  == "manual"`, devuelve solo categoría, `hora_candef` y `recurso_precio_hora`, y deja el INFO de
  R15 si el código del recurso difiere. El resto de la función no cambia (R18).
- `sqlalchemy_parte_repository.py`, `fetch_registros_para_recurso`: + `hora_match_method` (R17).
  `_PISA` no cambia. `pareja_extra.py` tampoco: la base convertida deja de ser miembro y su extra
  automática no congelada se borra sin recrearse (R12). Tests: `tests/test_f085_sv3_manual.py`.

## 4. Parte A · sv5 (`services/partes-transfer/`)

- `domain/models/registro_models.py`: `es_codigo_ci(cod) -> bool` (prefijo `CI`, normalizado);
  `HoraRecurso.es_incidencia` pasa a usarla (mismo resultado).
- `reglas_registro.py`: `MOTIVO_CODIGO_INCIDENCIA`; en `decidir`, tras `previa` y antes de
  `_decidir_mensual`, si no es incidencia y (`es_codigo_ci(linea.hora_codigo)` o su `hora_ide` es
  un CI* de `self._horas[recurso]`) ⇒ `omitir` (R19). Tests: `tests/test_f085_sv5_guarda.py`.

## 5. Parte B · recolocar el inicio

### 5.1 sv5
- `config/settings.py`: `mover_inicio: bool` de `MOVER_INICIO` (defecto `false`), con comentario.
- `application/services/racha_ciz.py` (puro): `MOTIVO_INICIO_EN_PARTE_CERRADO`,
  `motivo_inicio_en_parte_cerrado(ide, cod, estado)`, `DecisionInicio(tipo, linea, motivo,
  no_movido)` y `decidir_inicio(fecha_int, recurso_ide, codigo, candidatas, *, partes,
  est_registro, marca_pruebas, nombre_estado)`:
  1. `primera` = línea de la racha (`es_linea_de_la_racha`) posterior a D de menor (fecha, `ide`).
  2. Es inicio previo si su código normalizado es `codigo`, su synckey no acaba en `SUFIJO_CIZ` y
     hay un CIZ de la racha (`es_ciz_del_recurso`) con fecha ≥ la suya (D9).
  3. No lo es ⇒ `CREAR`, con `no_movido` = la primera línea posterior de código `codigo` si la hay
     (WARNING de R23).
  4. Enlazada ⇒ `ENLAZADA` (`motivo_linea_enlazada`); parte ausente o no En registro ⇒
     `PARTE_CERRADO`; si no ⇒ `MOVER` (R21, R22).
- `application/pipelines/registro_pipeline.py`, `_ciz_de_racha`: con `_mover_inicio()`, los
  `inicio` (rol de la línea) `escribir` con código CI* ≠ CIZ y `racha_registro_ids` suman sus
  synckeys (`partes:<i>` y `:ciz`) a la MISMA llamada a `lineas_de_racha` y sus `hmoide` a la de
  `estados_de_partes` (una llamada por petición, como hoy). Primero `decidir_mismo_dia` (sin
  cambios, R24); después `decidir_inicio`: `MOVER` ⇒ `a.mover = linea`; otros ⇒ `_omitir`. La rama
  `a.mover` del paso de escritura ya sirve (genérica: `stmt_mover_linea` conserva `horide`) y ya
  deja `movida_de`; el INFO pasa a decir `inicio_movido` si el código no es CIZ (R25). Apagado, ni
  lee ni decide nada nuevo (R27). Preflight: igual, consultivo (R26).

### 5.2 sv4
- `config/settings.py`: `mover_inicio` de `MOVER_INICIO` (defecto `false`).
- `application/services/racha_incidencia.py`: `MOTIVO_INICIO_MOVIDO = "inicio_movido"`,
  `motivo_inicio_movido(cod, hmores_ide, fecha_int)` (≤ 255) y `aviso_desordenada(hist,
  fecha_int, clave=None)`: con `clave`, None si el siguiente día que cuenta es de esa clave (R29).
- `parte_repository.py`: `_fin_movido` elige motivo por `e["hora_codigo"]` (CIZ ⇒ `fin_movido`;
  otro ⇒ `inicio_movido`), mismo CAS (R28). `_roles_de_racha` pasa `clave` a `aviso_desordenada`
  para las incidencias `inicio` solo con `mover_inicio` encendido.

### 5.3 Encendido
Se enciende tras M2–M3: **sv5 y luego sv4**; se apaga sv4 y luego sv5. `MOVER_CIZ` debe seguir
encendido (B usa el paso 6 bis de F-060). Vuelta atrás: apagar los dos; lo ya movido se queda.

### 5.4 Casos con `SigridFake` (R30–R32)
Recurso R, código CIA, CIZ en 25. (a) 19: CIA `partes:<id19>`, 25: CIZ `partes:<id25>`; aprobar
18 (`inicio`, tramo `[id19…id25]`) ⇒ una sentencia `UPDATE hmores SET fec = 20261118, synckey =
'partes:<id18>' …` sobre la del 19, ninguna `INSERT`; escrita con `movida_de = id19`; sv4 deja id19
`omitido` `inicio_movido`. (b) sin la del 19 ⇒ `INSERT` de la CIA del 18 sin hermano (`posterior`).
R31: tras (a), aprobar 17 mueve la línea (ahora `partes:<id18>`) al 17 e id18 queda `omitido`.

## 6. Relación con otras features

- **F-066**: R14 revocado; R13 y R17 matizados (un CI* da letra; CIZ y CI* sin letra, 400); R16
  ampliado (R10). Se enmiendan citando «F-085 R3/R4» solo `test_f066_r14_incidencia_no_cambia`
  y las filas de `test_f066_r13`/`r17` que lleven un CI* (hoy ninguna).
- **F-060**: se revoca en parte DA7 («trabajo o inicio antes de una incidencia registrada ⇒
  aviso y corrección manual»; «Fuera de alcance»: mover el CI* hacia atrás): con B, el inicio de
  la misma clave se recoloca. Petición literal del humano: «tiene que poner inicio de incidencia y
  quitar el inicio del dia 19». El trabajo antes de una incidencia registrada sigue con aviso.
- **F-062**: sin cambios; el hermano se decide antes de mover y nunca coincide con un movimiento.
- **F-083**: sin cambios. Su caso espejo (un CIZ cambiado a mano a CIV) no es inicio previo por
  D9 (a): no hay CIZ detrás; R32 lo vigila con sus casos R13–R17.
- **F-081** (spec aprobada, sin implementar): sigue «una incidencia no es editable» (su R5) y aquí
  las registradas siguen congeladas: no se solapan. Pero su R3 («mismo tipo que el que tiene»)
  daría por «ordinaria» un CI*, porque F-066 no los distingue: D14 propone enmendarlo para usar
  `es_codigo_incidencia`/`es_codigo_fin` de F-085 (422). F-085 va antes en `dev`.
- **F-053**: ninguna sentencia `DELETE`; mover es `UPDATE` (su guardián ya cubre el cliente). Los
  conflictos del paso 7 corren igual para un inicio movido (F-060 R27).
- **F-025**, **F-037/F-069** y **F-049** (marca, pareja, recálculo): se reutilizan sin cambios.

## 7. Límite de servicio y gemelos

Cada pieza vive en un solo servicio: la conversión en sv4, lo manual en sv3, la guarda y el
movimiento en sv5, el motivo del día movido en sv4. `es_codigo_ci` de sv5 y `es_codigo_incidencia`
de sv4 son la misma regla de prefijo que ya tiene cada servicio (`HoraRecurso.es_incidencia`, el
`cod.startswith("CI")` de sv3 en `_reshor_index`); no se añade a la lista cerrada de `CLAUDE.md`
ni se copia ningún fichero. La congelación gemela (F-024) y `orm_models.py` no cambian. Si el
reviewer viera una duplicación nueva, es decisión del humano.

## 8. Verificaciones manuales (`MANUAL (humano)`)

Lectura S de Sigrid: la de F-083 §8 (`Invoke-RestMethod … /api/sql/read`, `$KEY` del Key Vault).
Lectura P de `partes`: `psql -X -v ON_ERROR_STOP=1 -c "<sql>" "host=<servidor> dbname=partes
user=<usuario> sslmode=require"`.
- **M0 (líder, solo lectura, antes de T1)**: (1) P: `SELECT COALESCE(r.sigrid_estado,'') AS e,
  UPPER(TRIM(r.hora_codigo)) AS cod, COUNT(*) FROM parte_registros r JOIN parte_documents d ON
  d.id = r.document_id WHERE d.is_active AND r.deleted_at_utc IS NULL AND NOT r.es_incidencia AND
  UPPER(TRIM(r.hora_codigo)) LIKE 'CI%' GROUP BY 1,2 ORDER BY 1,2` (líneas heredadas, D7).
  (2) P: `SELECT id, fecha_int, tipo_hora, es_incidencia, incidencia_codigo, hora_codigo, horas,
  sigrid_estado, sigrid_hmores_ide FROM parte_registros WHERE recurso_ide = 2777451 AND fecha_int
  BETWEEN 20261117 AND 20261130 AND deleted_at_utc IS NULL ORDER BY fecha_int, id`.
  (3) S: `$q = @{ database='ruesma'; max_rows=50; parameters=@(2777451, 20261117, 20261130);
  sql='SELECT h.ide, h.fec, a.cod, h.can, h.synckey FROM hmores h LEFT JOIN auxhor a ON a.ide =
  h.horide WHERE h.reside = ? AND h.fec BETWEEN ? AND ? ORDER BY h.fec, h.ide' } | ConvertTo-Json`.
  Esperado: 416574 (18, HLOF, 8, `partes:25012`), 416563 (25, CIZ) con la synckey de una línea AT
  activa del portal entre el 19 y el 25; nada de `partes:25016`. Si la synckey del CIZ no es de
  esa racha, **PARA**: M4 escribiría un CIZ el 19.
- **M1 (local, modo pruebas, parte A)**: preparación de F-062 §9 (obra 0404, PRUEBA-IA,
  `OBRA_PRUEBAS_FORZAR=true`, `/health` con `modo_pruebas: True` o **PARA**). Línea de 10 h (8 +
  extra automática de 2): elegir CIA ⇒ recarga, Tipo «AT · …», matriz sin horas y, tras el
  recálculo, sin la extra; Deshacer ⇒ todo como antes (la extra vuelve tras el recálculo); otra
  vez CIA, aprobar ⇒ S da CIA con `can` 0 en `partes:<id>`; elegir CIZ ⇒ 400; en otra incidencia,
  elegir HLxx ⇒ Ordinaria con horas vacías. Limpieza de F-062 §9.
- **M2 (local, modo pruebas, parte B, `MOVER_INICIO=true` en sv5 y sv4)**: V los días 2–4.
  Aprobar el 3 (CIV + CIZ hermano), el 4 (el CIZ pasa al 4), el 2 ⇒ S: CIV en el 02 con
  `partes:<id2>`, nada con `partes:<id3>`, CIZ en el 04; portal: el 3 `omitido · inicio_movido`.
  V el 1 y aprobarlo ⇒ CIV en el 01; el 2 `omitido`. Limpieza.
- **M3 (local, parte B, opcional, con autorización de la edición a mano)**: V 1–3; aprobar el 3;
  el humano cambia a mano en Sigrid el CIZ de pruebas a CIV; aprobar el 1 ⇒ `INSERT` del CIV del
  01, sin mover, consola con `racha_inicio_no_movido`. Limpieza.
- **M4 (producción, reparación del caso, tras desplegar A; D15 (a))**: (1) repetir M0 (2)–(3).
  (2) Administración edita en Sigrid la 416574: código CIA, `can` 0, `tot` 0, synckey intacta
  (sin borrar). (3) S ⇒ 416574 CIA `can` 0. (4) Con OK expreso del humano, P en transacción:
  `UPDATE parte_registros SET es_incidencia = true, tipo_hora = 'AT', incidencia_codigo = 'AT',
  horas = NULL, horas_orig = NULL, hora_match_method = 'manual', sigrid_motivo = 'F-085: reparada a
  mano (Sigrid 416574 editada a CIA)' WHERE id = 25012 AND sigrid_estado = 'registrado' AND
  sigrid_hmores_ide = 416574 AND UPPER(TRIM(hora_codigo)) = 'CIA'`: debe dar `UPDATE 1`; si no,
  `ROLLBACK` y **PARA**. (5) En el portal, ↻ de la 25096 (19/11) y aprobar la 25405 (21/11) ⇒ las
  dos `omitido` con «el fin, CIZ linea 416563, ya esta el dia 2026-11-25». (6) S ⇒ CIA el 18
  (416574), CIZ el 25 (416563) y ningún otro CI* del 17 al 30; Sincronizar (F-052) ⇒ 25012
  `igual`.
- **M5 (producción, solo lectura, tras encender B)**: S `SELECT x.ide, x.fec, y.ide AS ide_post,
  y.fec AS fec_post, a.cod FROM hmores x JOIN auxhor a ON a.ide = x.horide JOIN hmores y ON
  y.reside = x.reside AND y.horide = x.horide AND y.fec > x.fec AND y.synckey LIKE 'partes:%' WHERE
  a.cod LIKE 'CI%' AND a.cod <> 'CIZ' AND x.synckey LIKE 'partes:%' AND y.ide > ? ORDER BY x.ide`
  (`?` = máximo `ide` al encender) ⇒ ningún par en días seguidos de la misma racha.

## 9. Documentación y frontera

- `docs/ARCHITECTURE.md` semántica 3 (conversión, CIZ y CI* sin letra, guarda de sv5, lo manual en
  sv3) y 4 (B: `MOVER_INICIO`, `inicio_movido`); `docs/referencia/partes-proyecto.md` §3.5 y §4.4;
  comentarios de `config/settings.py` de sv4 y sv5.
- **¿Cruza la frontera del proyecto? Sí, solo en documentación.** No cambian endpoints, tablas,
  colas, el contrato sv4↔sv5 (B reutiliza `racha_registro_ids` del inicio y `movida_de`) ni
  recursos compartidos. Cambia el comportamiento de sv5 sobre `hmores` y una variable nueva
  (`MOVER_INICIO`): se actualiza `azure-apps/partes.md` (paso 3 de sv5: 3c–3e, «Qué se rompe»,
  variables), en commit aparte con el protocolo de `CLAUDE.md`.

## 10. Ficheros que NO se tocan

`congelacion.py` y `esta_congelado` (gemelos F-024), los `orm_models.py`, `pareja_extra.py`,
`parte_normalizer.py`, `incidencias_horas.py`, `incidencias.yaml`, `partida_conciliador.py`,
`decidir_fin`, `decidir_mismo_dia`, `stmt_mover_linea` (tal cual), `estado_parte.py`,
`cuenta_analitica.py`, `sincronizacion.py`, las plantillas (pintan por `es_incidencia`), sv1, sv2.

## 11. Riesgos y alternativas descartadas

- Descartado que `tipo_hora_de_codigo` dé la letra para un CI*: la usan F-049, F-056 y F-052
  para horas. La decide `conversion_clase`, y solo un cambio de clase pide recálculo (R11).
- Un CIZ cambiado a mano a CI* con otro CIZ detrás se tomaría por inicio previo: son «dos CI* en
  la racha», lo que el humano pide quitar. El día X del inicio previo no viaja con D (está
  `registrado`); si viajara `encolado`, el CAS de R28 no lo toca (WARNING de F-060).
- Con A sin B, una incidencia el día antes de un inicio registrado deja dos CI* y el aviso de hoy.

## 12. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Partir | (a) dos features: F-085 = parte A (R1–R20, sv4+sv3+sv5) y otra nueva = parte B (R21–R32), las dos `critico`; (b) una sola | (a): A arregla el caso de origen sola y B estrena escrituras de CI* con su propia campaña | |
| D2 Horas al convertir en incidencia | (a) nulas, y `horas_orig` nulo (forma canónica); (b) conservarlas | (a) | |
| D3 Vuelta atrás (incidencia ⇒ código de horas) | (a) se permite y las horas quedan vacías; (b) horas = jornada por defecto; (c) 409, no se permite | (a) | |
| D4 Extra del mismo día y trabajador | (a) recálculo compartido: sv3 retira la extra automática no congelada; la explícita o congelada se queda con la marca F-025; (b) sv4 manda a la papelera todas las extras de ese día; (c) nada | (a) | |
| D5 CIZ y CI* sin letra | (a) 400 los dos; (b) solo CIZ, el CI* sin letra como hoy; (c) (a) y además ocultarlos del desplegable | (a) | |
| D6 Guarda de sv5 (R19) | (a) sí; (b) no, basta sv4 | (a): cubre las líneas heredadas y cualquier otra vía | |
| D7 Líneas heredadas con CI* sin ser incidencia (M0 (1)) | (a) nada retroactivo: sv5 las omite y se vuelve a elegir el código; (b) migración SQL | (a) | |
| D8 sv3 y lo manual | (a) respetar siempre `manual`; (b) solo si es un CI*; (c) solo si el código está en `reshor` del recurso | (a), como la partida | |
| D9 Qué CI* es el inicio previo | (a) la primera línea de la racha posterior, del mismo código y con un CIZ en su día o después; (b) la primera del mismo código aunque no haya CIZ (enmienda F-083 R15); (c) no mover | (a): no rompe F-083 | |
| D10 Inicio previo enlazado o en parte cerrado | (a) omitir con motivo, sin otro CI*; (b) escribir otro CI* con WARNING | (a), como F-060 R17–R18 | |
| D11 Estado del día que era inicio | (a) `omitido` con `inicio_movido`; (b) `omitido` con el motivo de día intermedio de sv5 | (a), como `fin_movido` | |
| D12 Interruptor de B | (a) `MOVER_INICIO` nuevo en sv5 y sv4, apagado; (b) bajo `MOVER_CIZ` (desplegar = activar); (c) solo en sv5 | (a): escribe en Sigrid, vuelta atrás sin redesplegar | |
| D13 Guardado por cada paso del campo de horas | (a) fuera: feature aparte `estandar` (guardar al salir del campo, una entrada de deshacer por edición); (b) dentro | (a) | |
| D14 F-081 R3 | (a) enmendarla: un CI* o CIZ no cuenta como «ordinaria» (422), con las funciones de R1; (b) sin cambios | (a) | |
| D15 Reparación del caso 0678 | (a) M4: Administración edita la 416574 a CIA 0 h y el humano autoriza el `UPDATE` de la 25012 en `partes`; (b) Administración la borra en Sigrid, «Comprobar en Sigrid» la deja `borrado_sigrid` y se repara con la feature (convertir y reaprobar); (c) esperar a F-081 | (a): no borra en Sigrid | |

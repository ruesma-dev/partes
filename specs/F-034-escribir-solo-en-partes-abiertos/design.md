<!-- specs/F-034-escribir-solo-en-partes-abiertos/design.md -->
# F-034 · sv5 solo escribe en partes de Sigrid abiertos — Diseño

## 1. Encaje, límite de servicio y hallazgos

- **sv5** es el único que escribe en Sigrid (vía sigrid-api, base `ruesma`): toda la regla
  vive allí. **sv4** solo pinta el motivo que manda sv5 (DA7). sv1–sv3, schema, colas y
  contrato JSON sv4↔sv5: sin cambios. Ninguna responsabilidad nueva fuera de sv5.
- **Lista cerrada de `CLAUDE.md`: no crece** (DA8). Nada se duplica entre servicios.
- **`porcentajes`**: `estado_parte.py` (copia literal suya, vigilada contra nuestro `dev`
  por su `test_f037_copias_partes.py`) y `stmts_crear_parte` (alta idéntica) **no se
  tocan** (DA6); la lógica nueva va en un módulo nuevo. Su `dedicacion-transfer` tiene el
  mismo hueco (`stmt_insert_linea` y `stmt_borrar_linea` sin guarda): se le avisa (§8).

Hallazgos en `dev` 4bda57e (`services/partes-transfer/`):

1. `registro_pipeline.py` l.547–656: la elección del parte (`_evaluar`, paso 5) ya corre
   **dentro del lock**, pero `stmt_insert_linea` (`sigrid_write_client.py` l.523–542) no
   mira `con.est`. El lock solo serializa sv5; Administración puede cerrar o contabilizar
   el parte en la ventana (lecturas de `max_pos`, alta, lotes).
2. `escribir` (l.113–133) parte en lotes de `SIGRID_MAX_STATEMENTS` (15): cada lote es una
   transacción. Tras escribir, el pipeline relee por synckey solo para el `hmores_ide`
   (l.649–655) y **da por escritas todas**: una línea que no entró saldría `registrado`.
3. **Pisado** (l.613–620): `stmt_borrar_linea` = `DELETE FROM hmores WHERE ide = ?`, sin
   guarda, y `res.borradas` se cuenta al construir la sentencia. **Contradice la regla del
   humano** «no se debe borrar en sigrid… si una hora extra se queda a cero no se borrará
   sino se pondrá a cero» (DA4). Se guarda aquí; cambiarlo a 0 va aparte (recomendado).
4. **F-046** (`reajuste_pipeline.py`): la guardia y el `UPDATE` ya exigen `c.est = ?`
   (sin `UPDLOCK`); `stmt_insertar_extra` solo queda protegido de forma indirecta (su base
   se actualiza antes en la misma transacción). Un parte cerrado ⇒ no editable (DA10 de
   F-046, R21/R26): se conserva (DA5).
5. Reaprobación: synckey existente ⇒ `ya_registrado`, sin sentencias. F-024 (comprobación),
   F-019 (dedicación) y `comprobar_asiento_analitico.py` no escriben en Sigrid.
   `prueba_escritura_sigrid.py` borra (fase `limpiar`) solo líneas `PRUEBA-IA` de la obra de
   pruebas: herramienta manual sancionada por `CLAUDE.md`, fuera de alcance.

## 2. Ficheros

**Crear**

- `services/partes-transfer/application/services/parte_abierto.py` (application, puro).
- `services/partes-transfer/tests/test_f034_cliente_guarda.py`,
  `test_f034_parte_abierto.py`, `test_f034_pipeline_cierre.py`.
- `services/partes-front/tests/test_f034_resultado_omitidas.py`.

**Modificar**

- `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py`: §3.
- `services/partes-transfer/application/pipelines/registro_pipeline.py`: §4 (paso 9 y la
  relectura); docstring de los pasos 8–9.
- `services/partes-transfer/tests/dobles.py` (`SigridFake`): §6.
- Tests de F-021/F-046 que fijan el SQL de las sentencias tocadas (`test_f021_cliente_cuenta.py`
  R14, `test_f046_cliente_reajuste.py`, `test_f046_t22_cliente_bordes.py`): se **amplían**
  al texto y parámetros nuevos, nunca se relajan; cada enmienda, citada en el informe.
- `services/partes-front/static/app.js`: `resultadoHtml` (§5).
- `docs/ARCHITECTURE.md` (semántica 16) y `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`
  (§8; commit local en ese repositorio).

**NO se tocan**: `application/services/estado_parte.py`, `stmts_crear_parte`,
`_crear_parte`, `reajuste_lineas.py` (motivos de F-046, DA9), `reglas_registro.py`,
`comprobacion_lineas.py`, `prueba_escritura_sigrid.py`, sv4 Python (repositorio, congelación,
`resultado_sigrid.py`), plantillas, ORM, colas.

## 3. SQL (sv5, infraestructura: `SigridWriteClient`)

Un único fragmento, usado por todas las sentencias que tocan líneas:

```python
def _guarda_parte_abierto(self, col: str) -> str:   # col: "?" o "hmores.hmoide" o "h.hmoide"
    return ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
            f"WHERE c.ide = {col} AND c.est = ?)")
```

`UPDLOCK, HOLDLOCK` retiene la fila de `con` hasta el `commit`: el cierre en Sigrid
(`UPDATE con SET est = …`) espera a que acabe nuestra transacción, así que «comprobar y
escribir» es atómico (R1, R8). El estado es `self._est` (`EST_PARTE_ACTIVO`), salvo en
`stmt_actualizar_linea`, que conserva su parámetro `est_registro`.

| Sentencia | Cambio | Parámetros nuevos (al final) |
|---|---|---|
| `stmt_insert_linea(..., pisadas: Sequence[int] = ())` | `SELECT x.n, …` desde la subconsulta `x` (patrón de `stmt_insertar_extra`) + `WHERE <guarda sobre ?>` + si hay pisadas `AND NOT EXISTS (SELECT 1 FROM hmores p WHERE p.ide IN (…) AND ISNULL(p.can, 0) <> 0)` (R2, R4) | `hmoide, est, *pisadas` |
| `stmt_borrar_linea(ide)` | pasa a método de instancia; `DELETE FROM hmores WHERE ide = ? AND <guarda sobre hmores.hmoide>` (R3) | `est` |
| `stmt_guardia_reajuste` | `FROM con c` → `FROM con c WITH (UPDLOCK, HOLDLOCK)` (R5) | ninguno |
| `stmt_actualizar_linea` | igual que la guardia (R5) | ninguno |
| `stmt_insertar_extra` | `AND <guarda sobre ?>` tras el `NOT EXISTS` de su synckey (R6) | `hmoide, est` |

Los tests fijan **el texto exacto** y la lista de parámetros de cada sentencia (rigor
crítico: un mutante de cadena tiene que morir). El cliente sigue teniendo un único
`DELETE` (R7), y los `INSERT` de líneas nunca usan un agregado con `WHERE`.

## 4. Pipeline de registro (sv5, aplicación)

En `_registrar_bajo_lock` (todo sigue bajo `self._lock`, R8):

1. **Pisadas por línea**: `pisadas_de: dict[int, list[int]]` = `ide` de `c.lineas` de cada
   conflicto confirmado, para cada `registro_id` de `c.registros`.
2. Paso 9: `stmt_borrar_linea(ls.ide)` como hoy, **sin** incrementar `res.borradas`;
   `stmt_insert_linea(..., pisadas=pisadas_de.get(a.registro_id, ()))`.
3. `escribir(statements)` (sin cambios en el reparto por lotes).
4. **Relectura** (R9): `lineas_por_synckey` (ya existía) → `confirmar_escritas(...)`.
   Si hubo pisadas: `lineas_por_ide(pisadas)` (método F-024 existente) → `res.borradas` =
   pisadas que ya no están (R12) y `vivas` = las que siguen con `can ≠ 0`.
5. **No escritas** (R10, R11, R13): una `partes_del_periodo` por periodo afectado; para
   cada una, `parte_que_impidio(...)` da el parte cerrado (el de su pisada viva primero,
   luego el elegido); con él, `motivo_parte_no_abierto(cod, self._nombre_estado(est))`; sin
   él, `motivo_no_escrita(cod)` + `logger.error`. Van a `res.omitidas`; WARNING con obra,
   periodo, códigos, estados y `registro_id` (sin nombres).
6. Una excepción de cualquier relectura sube (R14): sv4 marca `error` como hoy.

`preflight` no cambia (consultivo, sin lock). `_crear_parte` no cambia (R18).

## 5. Módulo puro nuevo y portal

`application/services/parte_abierto.py` (sin E/S; imports solo de `domain`):

```python
MOTIVO_PARTE_NO_ABIERTO = "parte_no_abierto"
MOTIVO_NO_ESCRITA = "no_escrita"
def motivo_parte_no_abierto(cod: str | None, estado: str) -> str: ...
def motivo_no_escrita(cod: str | None) -> str: ...
def confirmar_escritas(escritas: list[dict], leidas: dict[str, LineaSigrid]
                       ) -> tuple[list[dict], list[dict]]:  # (confirmadas, no_escritas)
def parte_que_impidio(hmoide_elegido: int, hmoides_pisadas_vivas: Sequence[int],
                      estados: dict[int, int | None], *, est_registro: int) -> int | None: ...
```

`confirmar_escritas`: escrita = synckey releída **y** `hmoide` igual al elegido; rellena
`hmores_ide`. Texto (DA3, sin tildes como el resto de motivos de sv5, ≤ 255):
`parte_no_abierto: el parte PT26/00314 ya no esta En registro (Cerrado); no se registra.
Reaprueba para llevarla al parte En registro del mes` y
`no_escrita: Sigrid no confirmo la linea en el parte PT26/00314; reaprueba`.

**sv4** (`static/app.js`, `resultadoHtml`): la línea «N linea(s) no registradas (reglas)»
pasa a «N linea(s) no registradas:» + lista `ap-list` de `esc(clave) · n`, con `clave` =
texto antes del primer `:` (o el motivo entero), en orden de aparición (R19). Las
omitidas solo traen `registro_id` y `motivo`: no se pintan nombres.

## 6. Doble `SigridFake` (tests/dobles.py)

- `cerrar_al_escribir: dict[int, int]` (`hmoide → est`): se aplica al entrar en el
  **primer** `escribir` que lleve `insert` o `borrar` (Administración en la ventana).
- `insert` lleva `guarda_hmoide` y `pisadas`; el doble no inserta si ese parte no está
  En registro o alguna pisada sigue con `can ≠ 0`. `borrar` (método de instancia) no borra
  si el parte de la línea no está En registro. Así el doble cumple la semántica del SQL
  real, fijado aparte por `test_f034_cliente_guarda.py`.
- `lineas_por_ide(ides)` como el cliente real, con `_comprobar_lock`.

## 7. Tests (sin red ni BBDD; datos sintéticos)

| Fichero | Cubre |
|---|---|
| `test_f034_cliente_guarda.py` | R1–R7: texto y parámetros exactos de las 5 sentencias; con y sin pisadas; `x.n` y sin agregado con `WHERE`; un solo `DELETE` en el cliente; `stmts_crear_parte` intacto |
| `test_f034_parte_abierto.py` | R9, R11: motivos (prefijos, código, estado, ≤ 255), `confirmar_escritas` (otro `hmoide`, ausente), `parte_que_impidio` (pisada primero, elegido, ninguno) |
| `test_f034_pipeline_cierre.py` | R8–R18: ejemplos 1–4; dos periodos con uno cerrado; lotes de 15 con cierre a medias; lecturas solo si hay no escritas; `caplog` sin nombres; relectura que falla; `vigilar_lock`; complementario y `ya_registrado` en cerrado |
| `test_f034_resultado_omitidas.py` (sv4) | R19 ejecutando `resultadoHtml` con `node` (patrón de `test_f031_preflight_avisos.py`), escape; R20 con `marcar_registros_sigrid` (`omitido` + `ESTADOS_REAPROBACION`) |

Fase RED con traza para R1–R6, R9–R13 y R19; R15–R18 y R20 son de caracterización.

## 8. Documentación

- `docs/ARCHITECTURE.md`, semántica 16: «Toda sentencia de sv5 que toca `hmores` lleva la
  guarda de parte abierto (`UPDLOCK, HOLDLOCK` sobre `con`); lo que no entra sale
  `omitido` `parte_no_abierto` y se reaprueba».
- `azure-apps/partes.md` (pasos 5–6 y «Qué se rompe»): lo mismo, y la **nota a
  `porcentajes`**: su `stmt_insert_linea`/`stmt_borrar_linea` no llevan guarda; sus copias
  (`estado_parte.py`, alta) no cambian. `dedicacion.md` es de `porcentajes`: no se toca.

## 9. Verificaciones manuales

- **M1 (líder, solo lectura, antes de implementar; `sql/read`, base `ruesma`)**:
  (a) partes de obra por estado: `SELECT h.mes, c.est, COUNT(*) n FROM hmo h JOIN con c ON
  c.ide = h.ide WHERE c.tip = 35 AND ISNULL(h.reside,0) = 0 AND h.ano = 2026 AND h.mes IN
  (9,10) GROUP BY h.mes, c.est`; (b) líneas del portal por estado de su parte: `SELECT
  h.ano, h.mes, c.est, COUNT(*) n FROM hmores r JOIN hmo h ON h.ide = r.hmoide JOIN con c
  ON c.ide = h.ide WHERE r.synckey LIKE 'partes:%' GROUP BY h.ano, h.mes, c.est` (que estén
  en partes cerrados es normal: se cerraron después); (c) periodos con más de un parte En
  registro (`HAVING SUM(CASE WHEN c.est = 1 THEN 1 ELSE 0 END) > 1`), esperado 0.
- **M2 (humano, tras `redeploy_partes.ps1 -Solo sv5` y `-Solo sv4`)**: desde local, modo
  pruebas (`OBRA_PRUEBAS_FORZAR=true`, obra 0404, `PRUEBA-IA`): aprobar una línea ⇒
  `registrado` en el parte En registro de 0404 (el SQL nuevo es válido y la guarda deja
  pasar). Si hay caso, un reajuste F-046 en 0404 ⇒ aplicado.
- **M3 (humano, con autorización expresa; solo obra 0404)**: con el parte de pruebas de
  0404 Cerrado en Sigrid, reaprobar una línea nueva ⇒ complementario (R15); y un
  `stmt_insert_linea` sobre el parte cerrado ⇒ `affected_rows = 0`. Limpiar con
  `prueba_escritura_sigrid.py`.
- **M4 (humano)**: el modal de resultado agrupa los motivos (vale una omitida por regla).

## 10. Riesgos y alternativas descartadas

- **Interbloqueo** con el cierre de Sigrid (nosotros `hmores`→`con`, ellos quizá al revés):
  SQL Server mata a uno; si somos nosotros, `sql/write` falla, la petición queda `error` y
  reaprobar es seguro (synckey). Aceptado.
- **Lotes**: un cierre entre lotes deja unas líneas escritas y otras no; la relectura decide
  línea a línea (R9), no la respuesta.
- **Descartado**: releer `partes_del_periodo` justo antes de `escribir` (DA1 B): estrecha la
  ventana pero no la cierra. Reintento automático al complementario (DA2 B): segunda alta
  bajo el lock y más superficie para un caso raro.

## 11. Decisiones abiertas (para el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Dónde se comprueba el estado | A: guarda en cada sentencia SQL (`UPDLOCK, HOLDLOCK`). B: releer los partes dentro del lock justo antes de `escribir`. C: A + B | **A** (B no cierra la ventana; C añade una lectura sin ganar nada) |
| DA2 | Línea cuyo parte se cerró en la ventana | A: `omitido` con motivo, reaprobable (al reaprobar va al complementario). B: reintento automático al complementario en la misma petición. C: fallo global (`error`) | **A** |
| DA3 | Texto del motivo | A: el de §5. B: corto, «parte_no_abierto: PT26/00314 (Cerrado); reaprueba» | **A** |
| DA4 | Pisado con `DELETE` (contra la regla «no borrar») | A: aquí solo la guarda + R4; «pisar = poner a 0» en feature aparte. B: cambiarlo aquí a `UPDATE can = 0, tot = 0` (textos de sv4, contador, enlazadas). C: desactivar el pisado hasta esa feature | **A** (lo ya planteado por el líder; R4 sirve igual con `can = 0`) |
| DA5 | Reajuste F-046 con parte cerrado | A: se mantiene DA10 de F-046 (no editable) + `UPDLOCK` y guarda en la extra. B: regularizar en el complementario (rompe synckey = `registro_id`) | **A** |
| DA6 | Gemelo con `porcentajes` | A: no tocar `estado_parte.py` ni el alta; módulo nuevo; nota en `azure-apps/partes.md`. B: regla en `estado_parte.py` y que recopien | **A** (B rompe su test de copias en cuanto llegue a `dev`) |
| DA7 | Qué ve el usuario | A: además del `title` del badge, el modal agrupa las omitidas por motivo. B: sin cambio en sv4 | **A** |
| DA8 | Lista cerrada de `CLAUDE.md` | A: no crece (todo en sv5). B: — | **A** |
| DA9 | Motivo F-046 «(estado 10)» | A: no tocar. B: nombrar Cerrado/Imputado (toca `reajuste_lineas.py` y sus tests) | **A** (fuera de alcance; ya dice «no esta En registro») |

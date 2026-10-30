<!-- progress/impl_F-034.md -->
# F-034 · Informe del implementer: sv5 solo escribe en partes abiertos

Rama `feature/F-034-escribir-solo-en-partes-abiertos` (worktree `partes-wt-f034`), sobre
`dev` 4bda57e. Rigor **crítico**. Spec aprobada entera por el humano el 2026-10-20 («Ok a
las 2», DA1–DA9; DA4 = A, el pisado a 0 va en F-053). M1 del líder anotada en design §9.
Sin escrituras en Sigrid, sin push.

## Qué cambió

**sv5 · infraestructura** (`infrastructure/sigrid/sigrid_write_client.py`)

- `_guarda_parte_abierto(col)`: `EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK)
  WHERE c.ide = <col> AND c.est = ?)`, un único fragmento para todas las sentencias (R1).
- `stmt_insert_linea`: `ide` de la subconsulta `x` (nunca agregado con `WHERE`), guarda
  sobre su `hmoide` y, con `pisadas=`, `AND NOT EXISTS (… p.ide IN (…) AND ISNULL(p.can, 0)
  <> 0)` (R2, R4). Parámetros nuevos al final: `hmoide, est, *pisadas`.
- `stmt_borrar_linea`: método de instancia, `DELETE … WHERE ide = ? AND <guarda sobre
  hmores.hmoide>` (R3). Sigue siendo el único `DELETE` del cliente (R7).
- Reajuste F-046: guardia y `UPDATE` leen `con` con `UPDLOCK, HOLDLOCK` (R5; mismos
  parámetros, `stmt_actualizar_linea` conserva `est_registro`); `stmt_insertar_extra`
  lleva además la guarda (`hmoide, est` al final) (R6).

**sv5 · aplicación**

- `application/services/parte_abierto.py` (nuevo, puro): `motivo_parte_no_abierto`,
  `motivo_no_escrita` (≤ 255, sin tildes, texto de DA3), `confirmar_escritas`,
  `parte_que_impidio`.
- `application/pipelines/registro_pipeline.py`, paso 9 y relectura, todo bajo el lock (R8):
  `pisadas_de` por `registro_id` de cada conflicto confirmado → `pisadas=` en su `INSERT`;
  tras `escribir`, relee por synckey y solo da por escrito lo que está en el parte elegido
  (R9); `borradas` = pisadas que ya no están (`lineas_por_ide`, R12); con no escritas, UNA
  `partes_del_periodo` por periodo afectado (R10), motivo `parte_no_abierto` con el parte de
  la pisada viva primero y luego el elegido, o `no_escrita` + ERROR (R11); WARNING sin
  nombres (R13); sin `try`: una relectura que falla tumba la petición (R14).

**sv4** (`static/app.js`, `resultadoHtml`): «N linea(s) no registradas:» + lista `ap-list`
`esc(clave) · n` por motivo, en orden de aparición (R19). El badge `omitido` ya llevaba el
motivo entero en el `title` (sin cambio). Repositorio sin cambio (R20).

**Docs**: `docs/ARCHITECTURE.md` semántica 16 y docstring de los pasos 8–9 (R21);
`azure-apps/partes.md` pasos 5–6 y nota a `porcentajes` (commit local `5e95d6e` en
`azure-apps`, solo `partes.md`).

**No se tocan** (T9): `estado_parte.py`, `cuenta_analitica.py` (`git diff --quiet dev` →
código 0), `stmts_crear_parte`, `_crear_parte`, `reajuste_lineas.py`, schema, contrato JSON.

## Ficheros tocados

| Fichero | Tipo |
|---|---|
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | producción |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | producción |
| `services/partes-transfer/application/services/parte_abierto.py` | producción (nuevo) |
| `services/partes-front/static/app.js` | producción (JS) |
| `services/partes-transfer/tests/test_f034_{cliente_guarda,parte_abierto,pipeline_cierre}.py` | tests nuevos |
| `services/partes-front/tests/test_f034_resultado_omitidas.py` | test nuevo |
| `services/partes-transfer/tests/dobles.py` (`SigridFake`) | doble |
| `tests/test_f021_cliente_cuenta.py`, `tests/test_f046_cliente_reajuste.py` (sv5) | ampliados |
| `docs/ARCHITECTURE.md`, spec (§9, §11, tasks), `progress/` | documentación |

Enmiendas a tests existentes (ampliadas, nunca relajadas): `test_f021_r14_caaide_es_un_
parametro_del_insert` (texto exacto nuevo + `900, 1` al final), `test_f021_r8_r14_sin_cuenta…`
(índices 13–15 y la guarda en 16–17); `test_f046_r24_r25_actualizar_linea_where_optimista` y
`test_f046_r25_guardia_cuenta_las_lineas_en_su_estado` (con `UPDLOCK, HOLDLOCK`),
`test_f046_r24_insertar_extra_condicionada_a_la_base` (texto con la guarda y `7001, 1` al
final). `test_f046_t22_cliente_bordes.py` no necesitó cambios (índices intactos).

## Decisiones de diseño y desviaciones (justificadas en `progress/current.md`)

1. `parte_abierto.py` importa `synckey_de` de infraestructura (design §5 decía «solo
   `domain`»), como ya hacen `reajuste_lineas.py` y `comprobacion_lineas.py`: es lo que
   permite la firma de design §5 sin duplicar el prefijo `partes:`.
2. `SigridFake.cerrar_tras_sentencias` además de `cerrar_al_escribir`: el doble recibe la
   lista entera, no los lotes de 15, y sin ello no se prueba el cierre entre lotes.
3. El doble trata como cerrado un parte que no existe (como el `EXISTS` real) y deja de
   contar como fila un `insert`/`borrar` que la guarda impide.
4. Pisada «viva» = sigue en Sigrid con `can` distinto de 0 (NULL = 0, como el SQL de R4).
5. Mensajes de log: WARNING `[registro] no escritas por parte no abierto obra=… periodo=
   AAAA/MM partes=<cod> (<estado>) registro_ids=[…]`; ERROR `… sin parte cerrado que lo
   explique … parte=<cod> registro_ids=[…]`. El INFO final añade `no_escritas=`.
6. sv4: un motivo vacío o nulo se agrupa bajo la clave vacía (literal de R19).

## Fase RED (trazas reales, recortadas)

Comandos desde `services/partes-transfer` (T8 desde `services/partes-front`) con
`…/.venv/Scripts/python.exe -m pytest <fichero> -q -p no:cacheprovider`. R15–R18 y R20 son de
caracterización: T1 pasó en verde antes de tocar código (`6 passed`).

**T2 (R9, R11)** · `tests/test_f034_parte_abierto.py`, módulo con firmas sin cuerpo:
```
application\services\parte_abierto.py:27: NotImplementedError
FAILED tests/test_f034_parte_abierto.py::test_f034_r11_motivo_parte_no_abierto_texto_exacto
FAILED tests/test_f034_parte_abierto.py::test_f034_r9_confirmada_si_esta_en_el_parte_elegido
FAILED tests/test_f034_parte_abierto.py::test_f034_r11_la_pisada_viva_en_cerrado_va_primero
20 failed, 1 passed in 1.22s
```
**T3 (R1–R4, R7)** · `tests/test_f034_cliente_guarda.py`, cliente de `dev`:
```
E       assert [4001] == [4001, 4]
E       AssertionError: assert not True
E        +  where True = isinstance(<staticmethod(<function SigridWriteClient.stmt_borrar_linea ...>)>, staticmethod)
E       assert 'DELETE FROM hmores WHERE ide = ? AND ' in 'class SigridWriteClient:\n ...'
FAILED tests/test_f034_cliente_guarda.py::test_f034_r2_insert_linea_texto_y_parametros_exactos
FAILED tests/test_f034_cliente_guarda.py::test_f034_r4_con_pisadas_solo_entra_si_ninguna_sigue_con_horas
14 failed, 1 passed in 2.34s
```
**T4 (R5, R6)** · mismo fichero, tras T3:
```
E        +  where False = <...>.endswith('AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE c.ide = h.hmoide AND c.est = ?)) <> ?)')
E         - ynckey = ?) AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE c.ide = ? AND c.est = ?)
E         + ynckey = ?)
E       AssertionError: assert [5.5, 'partes:990000001'] == [7404, 8]
5 failed, 16 passed in 1.07s
```
**T6 (R4, R12)** · `tests/test_f034_pipeline_cierre.py -k "pisad or borradas"`:
```
E       assert [4001, 5001] == [4001]        # la nueva duplicaba horas
E       assert [] == [4001]                  # el INSERT no llevaba sus pisadas
E       AssertionError: assert 2 == 1        # borradas contadas al construir
5 failed, 2 passed, 13 deselected in 1.78s
```
**T7 (R8–R11, R13)** · `tests/test_f034_pipeline_cierre.py`:
```
E       AssertionError: assert (True and [{'registro_id': 1, 'hmoide': 900, 'parte_cod': 'PT26/00314', ...}] == []
E       ValueError: not enough values to unpack (expected 1, got 0)
FAILED tests/test_f034_pipeline_cierre.py::test_f034_r9_r11_ejemplo_1_cierre_en_la_ventana
FAILED tests/test_f034_pipeline_cierre.py::test_f034_r9_cierre_entre_lotes_decide_linea_a_linea
FAILED tests/test_f034_pipeline_cierre.py::test_f034_r13_warning_sin_nombres
11 failed, 23 passed in 2.02s
```
(Los 23 en verde: T1, el doble y T6; de T7, `r10` y `r14` por synckey/ide ya pasaban:
caracterizan que sin no escritas no se relee y que una excepción ya subía.)

**T8 (R19)** · `services/partes-front/tests/test_f034_resultado_omitidas.py`:
```
E       AssertionError: <p><strong>0</strong> linea(s) registradas en Sigrid.</p><p>4 linea(s) no registradas (reglas).</p>
FAILED tests/test_f034_resultado_omitidas.py::test_f034_r19_agrupa_las_omitidas_por_motivo
FAILED tests/test_f034_resultado_omitidas.py::test_f034_r19_escapa_el_motivo
6 failed, 5 passed in 7.22s
```
GREEN tras cada tarea: T2 `21 passed`, T3 `28 passed` (con F-021), T4 y suite sv5
`704 passed`, T6 `7 passed`, T7 suite sv5 `732 passed`, T8 `11 passed` y
`node --check static/app.js` OK.

**T12 · supervivientes, cada test contra su mutante aplicado a mano** (`pytest tests -k t12`):
```
=== mutante: if float(ls.can or 0) != 0} -> if float(ls.can or 1) != 0}
FAILED tests/test_f034_pipeline_cierre.py::test_f034_t12_pisada_con_can_nulo_no_esta_viva
=== mutante: ... != 0} -> ... != 1}
E  ... 'no_escrita: Sigrid no confirmo la linea en el parte PT26/00400; reaprueba'} != {... 'parte_no_abierto: el parte PT26/00314 ...'}
=== mutante: int(paride or 0) -> int(paride or 1)
E       assert 1 == 0
=== mutante: round(float(can) * float(pre), 2) -> round(..., 3)
E       assert 0.061 == 0.06
```

## Verificaciones MANUAL pendientes (humano)

**Corrección de la review pasada 1 (2026-10-21, solo documental, C4)**: M2–M4 copiadas a
`progress/current.md` (sección F-034) con su comando exacto y el resultado esperado; M3
reformulada en algo observable y alineada en `design.md` §9 y `tasks.md`. Sin cambios de
código. Resumen:

- **M2**: sv5 local (`$env:OBRA_PRUEBAS_FORZAR = 'true'`, `/health` ⇒ `modo_pruebas: True`)
  en un mes sin partes de la 0404 (no 10/2026: PT26/00373 guarda líneas de F-046): preflight
  y `POST /api/registro/ejecutar` de una línea (990000341) ⇒ `escritas`, parte P1 nuevo; un
  reajuste 8 → 6 ⇒ aplicado (R5); luego `.\redeploy_partes.ps1 -Solo sv5` y `-Solo sv4`.
- **M3** (autorización expresa, solo 0404): P1 Cerrado ⇒ reaprobar ⇒ `ya_registradas`
  (R16), reajuste no editable (R17), línea nueva ⇒ complementario P2 (R15). El
  `affected_rows = 0` / `parte_no_abierto` no es observable a mano (ventana de ms): lo fijan
  los tests R2, R4, R9, R11. Limpieza: `limpiar` (DRY-RUN) y `limpiar --ejecutar` dos veces
  (un parte por pasada) y `estado` ⇒ sin parte.
- **M4**: Ctrl+F5 y, en la próxima aprobación con omitidas, «N linea(s) no registradas:» y
  una fila «<motivo> · <n>» por motivo, sin «(reglas)».
- Aviso a `porcentajes`: queda la nota en `azure-apps/partes.md`; su `dedicacion-transfer`
  sigue sin guarda (fuera de alcance de este repositorio).

## Fuera del alcance

«Pisar = poner a 0» (F-053, DA4); el motivo F-046 «(estado 10)» (DA9); la guarda en
`porcentajes`; `prueba_escritura_sigrid.py`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv5 (`services/partes-transfer/tests`) | **736 passed** en 17,1 s (antes de F-034: 698) |
| Tests nuevos de F-034 | sv5: 21 (`parte_abierto`) + 23 (`cliente_guarda`) + 36 (`pipeline_cierre`) = 80; sv4: 11 |
| Tests sv4 (`services/partes-front/tests`) | **2359 passed, 1 skipped** en 1138,9 s (máquina cargada) |
| Tests raíz (`tests/`, con cobertura) | **493 passed, 3 skipped** en 145,6 s |
| Cobertura de líneas cambiadas | **100,0 % de 75 líneas** (75/75, umbral 80 %, nivel crítico) |
| Mutación (campaña completa, 4 workers, sin `--timeout`) | **22 generados, 18 muertos, 4 supervivientes, 0 timeouts**, 227,0 s; línea base 29,5–31,2 s, timeout 300 s. Los 4, huecos reales con test nuevo que los mata: **22/22 detectados**, 0 equivalentes (`progress/mutacion_F-034.md`) |
| JS (`app.js`) | sin mutación ni cobertura de líneas (no es Python): lo cubren 9 tests con `node` |

La herramienta de mutación no muta el texto de las cadenas SQL: ese texto lo fijan, exacto,
`test_f034_cliente_guarda.py` y los tests de F-021/F-046 ampliados.

### Resultado de init.sh

`bash harness/init.sh` tal cual, sobre `HEAD` con este informe: **ENTORNO LISTO** (código 0).
pytest raíz en verde; sv1–sv3 en verde por caché (árbol sin cambios); sv4 `2359 passed, 1
skipped`; sv5 `736 passed`; `PUERTA COBERTURA: 100.0% de 75 líneas cambiadas cubiertas`;
`PUERTA TAMAÑO: … impl 191/220`. Avisos no bloqueantes y previos: ruff (deuda), features
`blocked` (F-014, F-032), infra sin tests y «coverage no pudo escribir coverage.json» (la
puerta de cobertura se calculó igualmente). La primera ejecución de la sesión cayó por un
`0xC0000005` (access violation de Windows) en un subproceso de
`tests/test_f024_borrado_no_congela_gemelos.py`; repetido aislado `4 passed` y la segunda
ejecución completa, en verde: transitorio de la máquina, no de F-034.

# F-040 · informe del implementer

Recursos sin DNI: proponer por nombre, aprender alias por recurso y poder
registrarlos. Rigor **crítico**. Rama `feature/F-040-recursos-sin-dni-por-nombre`
(worktree `partes-wt-f040`), con el `.venv` del repositorio principal
(`C:/Users/pgris/PycharmProjects/partes/.venv`): el worktree no tiene uno.
Un commit local por tarea (T1–T13), sin push.

## Qué cambió

**sv3** (`services/partes-persistencia`)
- `seleccion_sigrid.py`: `PREFIJO_FICHA`/`PREFIJO_RECURSO`; `clave_persona`
  (DNI del recurso, o `emp:<conide>` con ficha en el maestro, o `res:<ide>`);
  `elegir_sin_dni` (R9: `desconocido` → `con_dni` → `solo_baja` →
  `otra_empresa` → `ok`); `casar_por_clave`; `candidatos_nombre` sin exigir
  DNI (R1); rama R10 al principio de `elegir_recurso`.
- `casado_recurso.py`: `_casar_nombre` agrupa por clave y un ganador sin DNI
  da `nombre_sin_dni` sin casar (R2–R4, DA1); `_casar_alias` busca el DNI en
  alias → ficha → recurso de `recurso_ide` y, sin DNI, resuelve por clave
  (`_casar_alias_sin_dni`, R7–R8); `_a_match` guarda `dni` None si vacío (R12).
- `recurso_conciliador.py`: `con_dni` en `MOTIVOS_SIN_RECURSO_A_REVISAR` (R11).
- `sqlalchemy_parte_repository.find_empleado_alias` devuelve `recurso_ide` (R6).
- `medicion_casado.py`: columna `sin_dni_sin_ficha` y categoría
  `propone_sin_dni` antes que el resto (R28); `leer_aliases` sin cambios (R29).
- Solo textos: `empleado_matcher.py`, `sigrid_matcher_provider.py` (INFO «se
  proponen por nombre, no casan solos»), `parte_records.py`,
  `medir_casado_recursos.py`.

**sv4** (`services/partes-front`)
- `sigrid_lookup_client.fetch_recursos_activos`: ofrece los sin DNI con `dni`
  None y los cuenta en el log; el SQL no cambia (R14).
- `parte_repository.upsert_empleado_alias(…, ide: int | None, recurso_ide=None)`:
  sin `ide` ni `recurso_ide` no escribe (R18); snapshots de deshacer con
  `recurso_ide` (snapshot viejo sin la clave ⇒ NULL, R19).
- `app.py`: `conciliacion_confirmar` y `empleado_reasignar` guardan alias con
  ficha **o** con `reside`, pasando `recurso_ide` (R17).
- `static/app.js`: helpers `dniHtml`/`dniSufijo` en los 4 puntos de pintado;
  `templates/conciliacion.html` con `{% else %}` «sin DNI» (R15).
- `recurso_catalog.py`: solo docstrings (`asignacion_de` ya daba `dni` None, R16).

**Esquema (las dos copias de `orm_models.py`, byte-idénticas)**:
`empleado_ide` nullable, `recurso_ide INTEGER NULL` al final de
`EmpleadoAliasOrm`, y `ALTER TABLE empleado_alias ALTER COLUMN empleado_ide
DROP NOT NULL` en `DDL_EXTRA_POSTGRES` (R20, R21). Sin `.sql` ni `UPDATE`.

**sv5**: sin código (DA3); solo `tests/test_f040_sv5_sin_dni.py` (R22).
`git diff dev -- services/partes-transfer` muestra únicamente ese test.

**Documentación** (R27, R30): `CLAUDE.md` (rama sin DNI de `elegir_recurso`,
sin gemela en sv5), `docs/ARCHITECTURE.md` (semánticas 2, 7, 12 y
Herramientas), `docs/referencia/partes-proyecto.md` (§3.3, §4.6, §5.3) y
`azure-apps/partes.md` (viñeta Empleado y §4.3; commit local `ec971c2` en
`azure-apps`: único cambio fuera del worktree, exigido por T13 y por la regla
de `azure-apps` de CLAUDE.md).

## Decisiones y desviaciones

- **Bloqueo y opción A (humano, 2026-10-08)**: en T4 se pusieron rojos tres
  tests de F-023 no declarados; se paró y el humano eligió la opción A.
  `design.md` §8 enmendado. Los tres cambian solo lo esperado:
  `test_f023_r25_persona_sin_recursos_es_desconocido` (⇒ `ok`, más la
  aserción «sin preferido sigue `desconocido`»),
  `test_f023_r24_fichas_sin_dni_no_compiten_por_nombre` (⇒ `nombre_ambiguo`,
  con `ide`/`reside` None y `review`) y
  `test_f023_r24_una_sola_ficha_sin_dni_no_casa_por_nombre` (⇒
  `nombre_sin_dni`, ídem): siguen vigilando que ninguna línea sin DNI case sola.
- **Adaptaciones declaradas** (design §8), solo lo esperado: sv3
  `test_f036_r3_nombre_de_un_recurso_sin_dni_no_casa` (⇒ `nombre_sin_dni`),
  los dos de `candidatos_nombre` de `test_f036_seleccion.py` (uno renombrado
  a `…_solo_persona_de_alta_y_empresa`) y el INFO de `test_f036_maestro.py`;
  sv4 `test_f035_r3_sin_dni_ni_en_la_ficha_no_se_ofrece` (ahora se ofrecen
  con `dni` None) y los dos de `test_f035_endpoints.py` que esperaban «sin
  alias sin ficha»; tests de DDL F-010 (sv3/sv4): exentan de «solo aditivo /
  IF NOT EXISTS» únicamente la sentencia exacta de la relajación
  (`RELAJACIONES_PERMITIDAS`); sv3 gana un test de que es la única y va en
  `DDL_EXTRA_POSTGRES`.
- **Adaptaciones consecuencia directa de R14/R28 (señaladas al reviewer)**:
  `test_f035_r2_una_opcion_por_recurso_que_completa_categoria` (la lista de
  ides gana 904/905: misma regla que el r3 declarado) y dos aserciones de
  `test_f036_medicion.py` (dict exacto del maestro y la línea `|---|` de 7
  columnas: la columna nueva; dentro de la verificación de T12).
- En el alias sin DNI manda `recurso_ide` sobre `ide` (`res:` antes que
  `emp:`, design §4); por el camino de ficha el alias pisa `recurso_ide` a
  NULL (R17 «como hoy»).
- R12 (DNI vacío ⇒ NULL) solo es alcanzable por un alias sin DNI (por nombre
  sin DNI se propone, no se casa): se probó en T6 junto a R7–R8, no en T5.

## Verificación (resultados reales)

`bash harness/init.sh` final: **verde** (`ENTORNO LISTO`): raíz 461 passed /
3 skipped (1 min 56 s), sv3 1109 passed (30 s), sv4 1833 passed / 1 skipped
(9 min 35 s), sv5 537 passed (18 s). Guardianes de la lista cerrada (raíz)
en verde y sin relajar: `test_f010_orm_models_gemelos`,
`test_f023_de_alta_gemelos`, `test_f024_borrado_no_congela_gemelos`,
`test_f036_recurso_persona_gemelos` (69 passed con `test_documentos_del_arnes`);
`test_f017_r22_sin_reescritura_historica` en verde.

El JS se **ejecuta con node**: `tests/test_f040_vistas.py` corre las funciones
reales de `app.js` (`wireConciliacion`, `wireEmpleadoCombo` y las dos
llamadas `_comboSimple`) sobre un DOM falso, más `node --check`; la plantilla
se renderiza con el portal montado.

## Fase RED (trazas reales; comando desde `services/<svc>`, `../../.venv/Scripts/python.exe -m pytest -q --tb=line …`)

T1 y T8 son de **caracterización** (en verde contra el código de antes: 19 y
13 passed). T13 es documentación.

**T2** `tests/test_f040_alias_repo.py`, sv3 y sv4 (4 failed, 1 passed cada uno):
```
E   AssertionError: assert False is True            (empleado_ide nullable)
E   AttributeError: recurso_ide
E   assert 'ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS recurso_ide INTEGER' in (...)
E   AssertionError: assert 'ALTER TABLE empleado_alias ALTER COLUMN empleado_ide DROP NOT NULL' in ('CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active ...',)
```
**T3** `tests/test_f040_elegir_sin_dni.py`: `19 x AttributeError: 'IndicePersonas' object has no attribute 'elegir_sin_dni'` → 19 failed.
**T4** `tests/test_f040_seleccion.py` (18 failed, 4 passed):
```
E   AssertionError: assert 'con_dni' in frozenset({'ambiguo', 'otra_empresa', 'solo_baja'})
E   AssertionError: assert (None, 'sin_recurso') == (903, 'sin_parte')
E   AssertionError: assert [] == [['doc-1']]                      (x3, R11)
E   AttributeError: 'IndicePersonas' object has no attribute 'casar_por_clave'   (x10)
E   AttributeError: 'IndicePersonas' object has no attribute 'clave_persona'
E   assert [900, 901] == [900, 901, 902, 903, 907]
```
**T5** `tests/test_f040_casado.py` (8 failed, 8 passed):
```
E   AssertionError: assert EmpleadoMatch...mbre_ambiguo') == EmpleadoMatch...mbre_sin_dni')   (x7)
FAILED ...test_f040_r3_gana_un_recurso_sin_dni_ni_ficha_se_propone / ..._r5_sin_dni_leido_va_al_nombre[None|''|'   ']
```
**T6** `tests/test_f040_casado.py -k "r7 or r8 or r12"` + `tests/test_f040_alias_repo.py` (9 failed):
```
E   AssertionError: assert (None, None, ...one, 0.0, ...) == (None, 'MO/97...970, 1.0, ...)   (x6, el alias no casaba)
E   AssertionError: assert (None, 'alias_no_valido') == (970, 'recurso_nombre')            (R12)
E   AssertionError: assert {'ide': None,..., 'dni': None} == {'ide': None,...i': None, ...}  (R6, sin recurso_ide)
```
**T7** `tests/test_f036_maestro.py -k r3`: `assert ['[matcher-pr...bre): 3 de 5'] == ['[matcher-pr...los): 3 de 5']` → 1 failed.
**T9** `tests/test_f040_catalogo.py` (3 failed, 3 passed):
```
E   assert [901] == [901, 904, 905]
E   AssertionError: assert '-> 3 recursos (2 sin DNI, ofrecidos marcados)' in '[sigrid-lookup] recursos_activos -> 1 recursos (2 sin DNI, no se ofrecen)'
```
**T10** `tests/test_f040_alias.py` (13 failed, 4 passed):
```
E   AssertionError: assert [] == [('tres solo ...ne, 904, ...)]                (alias sin ficha no se guardaba)
E   TypeError: ParteReviewRepository.upsert_empleado_alias() got an unexpected keyword argument 'recurso_ide'
E   assert (200, True) == (200, False)
```
**T11** `tests/test_f040_vistas.py` (3 failed, 2 passed, 4 errors: `app.js no define dniHtml`).
Y los escenarios **ejecutados con node** contra el `app.js` de antes (sin los
helpers) pintaban el recurso sin DNI **sin ninguna marca**:
```
conciliar[sin]: ss="mi-emp">MO/0004 · CUATRO &lt;SIN&gt; DNI · Porsan</span>
detalle[sin]: MO/0004 · CUATRO &lt;SIN&gt; DNI · Porsan
combos: {"emp-combo": [..., "MO/0004 · CUATRO <SIN> DNI · Porsan"], ...}
```
**T12** `tests/test_f040_medicion.py` (5 failed, 3 passed):
```
E   AssertionError: assert 'mo_no_persona' == 'sin_dni_sin_ficha'
E   AssertionError: assert 'igual' == 'propone_sin_dni'
E   AssertionError: assert 'pierde_casado' == 'propone_sin_dni'
E   KeyError: 'casado_propone_sin_dni'
```

## Fuera de alcance y pendiente

- Fuera de alcance (spec): agrupar por recurso en el portal las líneas sin
  DNI (`worker_key`/`persona_de` siguen por nombre leído), Sesame sin DNI y
  completar DNIs en Sigrid.
- **MANUAL (humano)** — T14/M1 antes de desplegar (solo lectura):
  `cd services/partes-persistencia && ../../.venv/Scripts/python.exe
  medir_casado_recursos.py` desde esta rama; mirar `sin_dni`/
  `sin_dni_sin_ficha` por empresa, `casado_pierde_casado` y
  `casado_propone_sin_dni`. T15: despliegue `-Solo sv3` y luego `-Solo sv4`
  (sv5 no); M2 (`information_schema` ⇒ dos `YES`) y M3 (Porsan
  `MO/0032`/`MO/0033` «sin DNI» en Conciliar, alias con `recurso_ide`, línea
  `recurso_manual`, preflight verificado).
- Nada se ha ejecutado contra producción ni contra la base `partes`.
- Siguiente: reviewer contra `CHECKPOINTS.md`.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz 461 passed / 3 skipped · sv3 1109 passed · sv4 1833 passed / 1 skipped · sv5 537 passed — todo verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 66 líneas cambiadas cubiertas (66/66, umbral 80%, nivel critico)` |
| Mutación | campaña **completa** (sin muestreo), 225 líneas en alcance: **40 generados, 38 muertos, 0 supervivientes, 2 timeouts**. Los dos timeouts (`app.py:1431`) son por la lentitud de la suite de sv4 (base 540 s vs tope 600 s); aplicados a mano, los mata `test_f040_alias.py` (detalle en `progress/mutacion_F-040.md`). Efectivo: 40/40 muertos |
| Tiempo de la suite | sv3 30 s · sv4 9 min 35 s · sv5 18 s · raíz 1 min 56 s; campaña de mutación 3244 s (6 workers, `--timeout 600`) |
| Fuera del mutador | `static/app.js` y `conciliacion.html` (el mutador es solo Python): ejecutados con node y renderizados en `test_f040_vistas.py` |

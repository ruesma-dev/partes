<!-- progress/impl_F-036.md -->
# F-036 · Informe del implementer

Rama `feature/F-036-casado-contra-recursos` (worktree `partes-wt-f036`), un commit por tarea
(T1–T15 + BACKLOG), sin push. Intérprete: el `.venv` del repo principal (el worktree no tiene).
DA1–DA3 aprobadas por el humano el 2026-10-07 (las recomendadas).

## Qué cambió

- **sv3 casa contra recursos persona.** `casado_recurso.casar_trabajador` (nuevo, puro): DNI →
  alias → nombre contra los recursos `res.cla = 1` de alta a la fecha y de la empresa del parte.
  DNI del recurso = `emp.dni` de la ficha enlazada y, si vacío, `res.cif` (DA1). Con ficha se
  guardan sus datos; sin ella `empleado_ide` NULL, código/nombre del recurso y
  `recurso_dni`/`recurso_nombre`; siempre `empleado_reside` = recurso elegido (R13–R14). El
  conciliador lo confirma (R15, probado de punta a punta con SQLite).
- **Maestro**: `res.cla` en `_SQL_RECURSOS` y `RecursoRow.cla`; `IndicePersonas` solo indexa por
  DNI/ficha recursos persona (`CLA_PERSONA`, `es_persona`); nuevos `dni_de_recurso`,
  `ficha_enlazada`, `candidatos_nombre`, `casar_por_dni`; INFO con los persona sin DNI (R3).
- **Nombre por persona** (`EmpleadoMatcher.match_nombre`): máximo entre `con.res` y el nombre de
  la ficha; otra persona que empata → `nombre_ambiguo` (R10–R12).
- **Retirado F-030**: `fichas_de_recurso.py`, `Matchers.recursos`, `fichas_candidatas`,
  `_de_recurso`, `_casar_alias`, `to_match` (R17).
- **sv5**: `AND res.cla = 1` en las dos ramas de `recursos_por_dni` (R18).
- **Guardián** raíz `tests/test_f036_recurso_persona_gemelos.py` (R19) y entrada en la lista
  cerrada de `CLAUDE.md`.
- **Herramienta de solo lectura** `services/partes-persistencia/medir_casado_recursos.py` +
  núcleo puro `application/services/medicion_casado.py` (R23–R28).
- **Docs** (R29): `CLAUDE.md`, `docs/ARCHITECTURE.md` (semánticas 2 y 12, Herramientas de
  consola), `docs/referencia/partes-proyecto.md` (§3.3, §4.6, §7) y `azure-apps/partes.md`
  (commit local `6355a5f` allí; el `dedicacion.md` modificado de ese repo es de otra sesión).

## Ficheros tocados

sv3 (`services/partes-persistencia/`): `domain/models/sigrid_models.py`,
`domain/models/parte_records.py` (comentario), `infrastructure/sigrid/sigrid_api_client.py`,
`application/services/{seleccion_sigrid,empleado_matcher,sigrid_matcher_provider}.py`,
`application/services/casado_recurso.py` (nuevo), `application/services/medicion_casado.py`
(nuevo), `application/services/fichas_de_recurso.py` (borrado),
`application/pipelines/persist_parte_pipeline.py`, `medir_casado_recursos.py` (nuevo).
Tests sv3: nuevos `test_f036_{caracterizacion,maestro,seleccion,casado,pipeline,medicion}.py`;
adaptados `dobles.py` (`recurso_persona`), `test_f003_r26_review_required.py`,
`test_f023_{pipeline_match,recurso_conciliador,seleccion_sigrid}.py`,
`test_f030_{casado_recurso,conciliador_sin_ficha,dni_canonico}.py`.
sv5: `infrastructure/sigrid/sigrid_write_client.py`, `tests/test_f036_recursos_por_dni_persona.py`.
Raíz: `tests/test_f036_recurso_persona_gemelos.py`, `CLAUDE.md`, `docs/…`, `BACKLOG.md`.
**No cambian** (T13, `git diff dev --stat` vacío): sv4 entero, `partes-transfer/application`,
`orm_models.py`; tampoco `recurso_conciliador.py`, `jornada_resolver.py`, `text_match.py`,
`sqlalchemy_parte_repository.py`.

## Decisiones y desviaciones (justificadas)

1. `dni_de_recurso`/`ficha_enlazada` se adelantan de T4 a T3: el INFO de R3 los necesita.
2. T5 dejó un `match_nombre_fichas` transitorio para no romper el pipeline; T7 lo retira.
3. `casar_trabajador` recibe el alias como función (perezoso, R6) y un `candidatos` opcional: el
   pipeline calcula `candidatos_nombre` una vez por parte (memo local, test con espía).
4. R26 con una quinta categoría `otro_recurso` (misma persona, otro `reside`), para no llamar
   «otra persona» a un cambio de recurso.
5. La herramienta **no usa `SessionFactory`** (al construirse crea la base si falta): engine
   propio, `SET TRANSACTION READ ONLY` y `rollback`. `parte_registros` no guarda el DNI leído:
   sale del `raw_extraction_json` con el mismo `ParteNormalizer`, por `numero_linea` o nombre.
6. **R22 es de caracterización**, no RED: el código anterior tampoco re-casaba lo ingerido (el
   único fallo de su traza era del fixture: dos partes de la misma obra y día se sustituyen).

## Tests de F-023/F-030 retirados o adaptados (design §7)

- `test_f030_casado_recurso.py`: **retirados** los de `fichas_de_recurso` (9), proveedor (3),
  logs del respaldo (5) y `_Prohibido` sobre `recursos` (3). **Adaptados**: R12 (código del
  recurso y DNI normalizado, R14); «no hay alias de recurso» →
  `test_f030_r8_alias_de_un_recurso_sin_ficha_casa` (ahora casa, R8); R9 (código del recurso;
  la ficha 11 gana un recurso). 3 renombrados (sin «fichas_de_recurso» en el nombre).
- `test_f023_pipeline_match.py`: recurso 940 para DIANA; `r23_alias_sin_dni_…_no_es_valido` →
  `r23_alias_sin_dni_toma_el_de_su_ficha` (`dni_otra_empresa`, R8) + `r23_alias_sin_dni_ni_ficha_…`;
  fichas sin DNI → `none` (R3) en `r24_fichas_sin_dni_no_compiten_por_nombre` y
  `r24_una_sola_ficha_sin_dni_no_casa_por_nombre`; dos `r24` ganan recursos en el fixture.
- `test_f023_seleccion_sigrid.py`: retirado `r17_fichas_candidatas_de_alta_y_de_la_empresa`.
- Fixtures `RecursoRow` de F-003/F-023/F-030 con `cla=1` vía `recurso_persona` (`tests/dobles.py`).

## Fase RED (trazas reales; `cd services/partes-persistencia` salvo indicación)

**T1 · caracterización R20/R21, en verde antes de tocar código:**
`pytest -q tests/test_f036_caracterizacion.py` → `18 passed in 0.30s`; guardianes
`tests/test_f023_de_alta_gemelos.py tests/test_f024_borrado_no_congela_gemelos.py` → `18 passed`.

**T2 · R1** — `python -m pytest -q tests/test_f036_maestro.py`
```
E       AssertionError: assert 'res.cla AS cla' in 'SELECT res.ide AS ide, res.cif AS cif, ... ORDER BY res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
E       AttributeError: 'RecursoRow' object has no attribute 'cla'      (x2)
3 failed in 0.75s                         -> tras el código: 3 passed; suite sv3 776 passed
```
**T3 · R2, R3** — `python -m pytest -q tests/test_f036_maestro.py`
```
      7 E       AttributeError: 'IndicePersonas' object has no attribute 'dni_de_recurso'
      5 E       AttributeError: module 'application.services.seleccion_sigrid' has no attribute 'es_persona'
      3 E       AssertionError: assert (900, 'ok') == (None, 'desconocido')
      1 E       assert frozenset({1, 28, 31}) == frozenset({28})
      1 E       AttributeError: module '...seleccion_sigrid' has no attribute 'CLA_PERSONA'
      1 E       AttributeError: 'IndicePersonas' object has no attribute 'ficha_enlazada'
      1 E       AssertionError: assert (None, 'ambiguo') == (901, 'ok')
      1 E       AssertionError: assert (901, 'ok') == (902, 'ok')
      1 E       AssertionError: assert [] == ['[matcher-pr...bre): 2 de 4']
21 failed, 4 passed in 1.42s              -> 79 passed (con F-023 selección); suite 798 passed
```
**T4 · R3, R4, R5, R7** — `python -m pytest -q tests/test_f036_seleccion.py`
```
     17 E       AttributeError: 'IndicePersonas' object has no attribute 'casar_por_dni'
      3 E       AttributeError: 'IndicePersonas' object has no attribute 'candidatos_nombre'
20 failed in 0.86s                        -> 20 passed in 0.23s
```
**T5 · R10–R12** — `python -m pytest -q tests/test_f036_casado.py -k nombre`
```
     16 E       TypeError: EmpleadoMatcher.match_nombre() got an unexpected keyword argument 'candidatos'
16 failed in 0.46s                        -> 16 passed; suite 834 passed
```
**T6 · R4–R8, R13, R14** — sin módulo: `ModuleNotFoundError: No module named
'application.services.casado_recurso'`; con un esqueleto que lanza `NotImplementedError`:
```
     37 E       NotImplementedError
37 failed, 16 passed in 2.99s  (los 16 son los de T5) -> 53 passed in 0.69s
```
**T7 · R6, R13–R17** — `python -m pytest -q tests/test_f036_pipeline.py`
```
E  assert (None, None, ...otra_empresa') == (None, 'MO/95...'recurso_dni')   # R7/R14
E  assert (None, None, ...'recurso_dni') == (None, 'MO/96...'recurso_dni')   # R14 código
E  assert (60, 'E60', '...965, 'nombre') == (60, 'E60', '...', 965, 'dni')  # DA1
E  assert (None, None, ...curso_nombre') == (None, 'MO/96...curso_nombre')  # R14
E  assert (None, None, ...mbre_ambiguo') == (None, None, ...'dni_ambiguo')  # R5
E  assert 1 == 0                                                            # R6 alias perezoso
E  assert [] == [(1, 20260915)]                                             # memo por parte
E  assert ModuleSpec(name='application.services.fichas_de_recurso', ...) is None   # R17
E  assert ['tests\\test...didatas', ...] == []                              # R17
E  assert (910, 911) == (911, 911)                                          # R22: fixture (dec. 6)
10 failed, 10 passed in 6.39s             -> 20 passed; suite 871 passed; git grep vacío
```
**T9 · R18** — `cd services/partes-transfer && python -m pytest -q tests/test_f036_recursos_por_dni_persona.py`
```
E   AssertionError: SELECT REPLACE(...emp.dni...) AS dnin, res.ide AS reside FROM res JOIN emp ON emp.ide = res.conide WHERE REPLACE(...) IN (?)
E   assert None   (re.search('\bAND res\.cla = 1\b', ...))
1 failed, 1 passed in 2.90s               -> 2 passed; suite sv5 524 passed
```
**T10 · R19** — guardián copiado **fuera del repo** con los ficheros vigilados,
`pytest -q tests/test_f036_recurso_persona_gemelos.py -k "not falla"`:
```
== dev:      CLA_PERSONA = None, se esperaba 1 | IndicePersonas.__init__ ya no filtra con es_persona
             | _SQL_RECURSOS ya no lee res.cla                     -> 4 failed, 7 deselected
== rota_sv5: una rama de recursos_por_dni perdio res.cla           -> 1 failed, 3 passed
== rota_sv3: IndicePersonas.__init__ ya no filtra con es_persona   -> 1 failed, 3 passed
```
En el repo `11 passed` (7 de ellos estropean una copia en memoria y exigen el fallo).

**T11 · R24–R28** — `python -m pytest -q tests/test_f036_medicion.py` con el módulo vacío:
```
     18 E       AttributeError: module '...medicion_casado' has no attribute 'LineaMedida'
     10 E       AttributeError: module '...medicion_casado' has no attribute 'medir_maestro'
      1 E       AttributeError: module '...medicion_casado' has no attribute 'resumir'
29 failed in 2.25s                        -> 29 passed in 1.41s
```
**T12 · R23** — `python -m pytest -q tests/test_f036_medicion.py -k r23` con el script vacío:
```
      6 E       AttributeError: module 'medir_casado_recursos' has no attribute '_dnis_leidos'
      2 E       AttributeError: <module 'medir_casado_recursos' ...> has no attribute 'Settings'
      4 E       AttributeError: ... has no attribute 'medir' | 'leer_lineas' | 'escribir' | 'solo_lectura'
12 failed, 1 passed (el estático «sin escrituras») -> 42 passed; suite sv3 913 passed
```

**T19 · R6, opción A del humano (2026-10-07)** — DNI de una persona que Sigrid conoce (ficha `emp`
o recurso de cualquier clase) sin ningún recurso persona ⇒ `dni_sin_recurso`, sin alias ni nombre.
`python -m pytest -q tests/test_f036_casado.py tests/test_f036_seleccion.py tests/test_f036_pipeline.py -k r6`:
```
      8 E       AttributeError: 'IndicePersonas' object has no attribute 'dni_conocido'
      3 E       AssertionError: assert (10, 'E10', '...910, 1.0, ...) == (None, None, ...one, 0.0, ...)
      1 E       AssertionError: assert (10, 'E10', '...910, 'nombre') == (None, None, ..._sin_recurso')
12 failed, 15 passed, 78 deselected in 6.06s  -> 27 passed; suite sv3 928 passed
```
(los 3 + 1 casaban por **nombre** a ANA, otra persona: justo el riesgo que señaló el reviewer).
sv4 **no se toca** y ya lo trata como sin casar (comprobado con su código, script en el scratchpad):
`esta_casado(empleado_ide=None, método 'dni_sin_recurso')` → `False`; filtro de la cola
`empleado_ide IS NULL AND (método IS NULL OR método NOT IN ('recurso_dni','recurso_nombre'))`;
la columna es `String(24)` (el método mide 15). Spec (R6, design §4 y T19), `ARCHITECTURE.md`,
`partes-proyecto.md` y `azure-apps/partes.md` (commit local `de0d1b0`) actualizados.

## Verificaciones MANUAL pendientes (humano; comandos exactos en `progress/current.md`)

M1 (medición, solo lectura, **no ejecutada** por los agentes), despliegue
`redeploy_partes.ps1 -Solo sv3,sv5`, M2/M2b (Log Analytics y SQL) y M3 (SQL, parte de Porsan 0678).

## Evidencias

Medidas el 2026-10-07 en el worktree (`bash harness/init.sh` final: **ENTORNO LISTO**, exit 0).

| Evidencia | Valor real |
|---|---|
| Tests sv3 (`services/partes-persistencia`) | **928 passed** en 32,53 s (antes de F-036: 776) |
| Tests sv5 (`services/partes-transfer`) | **524 passed**, 1 warning, en 53,11 s |
| Tests raíz (`tests/`, con cobertura) | **454 passed, 3 skipped** en 232,70 s |
| Tests sv4 / sv1 / sv2 (código sin cambios) | 1682 passed, 1 skipped (1491 s) / 74 passed / 8 passed |
| Tests nuevos de F-036 | sv3 18+25+28+56+21+45 = 193 (caracterización, maestro, selección, casado, pipeline, medición); sv5 2; raíz 11 |
| **PUERTA COBERTURA** | **99,7 %** de 315 líneas cambiadas (314/315, umbral 80 %, crítico); la única línea sin cubrir es el `raise AssertionError` de `_nodo` del guardián raíz, que solo corre si detecta un fallo |
| **Mutación** (`--workers 6 --timeout 600`, campaña completa) | 1.ª: 113 generados, **10 supervivientes** (959 s), resueltos en `eca56bb` (5 huecos con test, 3 equivalentes quitando código muerto, 2 de orden reescrito). 2.ª (`ee2c5d1`): 108/108 muertos. **3.ª tras R6 (`a6eeb64`): 110 generados, 110 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 680,6 s.** Detalle: `progress/mutacion_F-036.md` |
| ruff | avisos del repo ≈ 620 (610 antes): `I001` de los tests nuevos vistos desde la raíz, el patrón de los tests existentes; desde el servicio, limpio |

Review pasada 1 (`progress/review_F-036.md`, CHANGES_REQUESTED documental) atendida: comandos de M1–M3
y del despliegue en `current.md`; `I001` de `seleccion_sigrid.py` corregido; `_METODOS_RECURSO` de
`medicion_casado` se queda (importarlo del pipeline invertiría la dependencia), con test que lo iguala.
Fuera de alcance: sv4 (F-035), re-casar lo ingerido, recursos sin DNI por `reside`, la verificación de
sv5 y la escritura en Sigrid. Falta: nueva pasada del reviewer y M1–M3 del humano.

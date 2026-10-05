<!-- progress/impl_F-030.md -->
# F-030 · Ficha de recurso cuando no hay ficha de empleado — Informe del implementer

Rama `feature/F-030-recurso-sin-ficha`, rigor `critico`, spec v2 aprobada el
2026-10-05 (DA1–DA9 tal cual). Toca sv3 y, al mínimo, sv4; sv5 solo gana
tests. Ni una escritura en Sigrid ni en la base `partes`, sin despliegue,
sin push. Todos los datos de los tests son sintéticos (ni DNIs, ni
nombres, ni códigos reales).

## 1. Qué cambió (commits locales)

| Commit | Tarea | Qué |
|---|---|---|
| `89def08` | T1 | Caracterización en verde **sin tocar código**: conciliador sv3 (R14, R15) y sv5 (R17, R21) |
| `d83f06b` | T2 | `parte_normalizer.dni_canonico` y `trabajador_dni_leido = dni_canonico(...) or None` (R1–R3) |
| `b07c068` | T3 | `RecursoRow.codigo/nombre`; `rc.cod AS codigo`, `rc.res AS nombre` en `_SQL_RECURSOS` y mapeo (R4) |
| `4cf8e2e` | T4 | `application/services/fichas_de_recurso.py` (pura): `PREFIJO_MANO_DE_OBRA`, `fichas_de_recurso` (R4) |
| `a35fd90` | T5 | `Matchers.recursos = IndicePersonas(fichas_de_recurso(empleados, recursos), [])` en `_montar` (vacío en `_empty`) |
| `41d2329` | T6 | Pipeline: `METODOS_RECURSO`, `_de_recurso` y paso DNI → fichas de recurso antes del alias, INFO sin DNI ni nombre (R5–R8, R12) |
| `3070160` | T7 | Nombre: `match_nombre` con fichas de empleado + de recurso candidatas; `recurso_nombre` (R9–R11) |
| `ea38708` | T8 | `_compute_review_required` (R13); comentario de `EmpleadoMatch.method`; docstring del pipeline |
| `74c7041` | T9 | sv4 `parte_repository.py`: `METODOS_RECURSO`, `esta_casado` en los 4 `matched=`, filtro `_sin_casar_en_cola` en la cola y en `backfill_empleado` (R18–R20) |
| `00a8b3b` | T10 | Verificación R16 (sin código) |
| `7aea2c7` | T11 | `docs/ARCHITECTURE.md` (semántica 2 y 12, +6 líneas) y `partes-proyecto.md` (§4.6, §7 y nota de cabecera) |
| `b98fa68` | T12 | `azure-apps/partes.md` (viñetas Empleado y Recurso): commit local **`1c7238c`** en ese repo, sin push |
| `551a1d8` | — | Cero avisos de ruff en los tests nuevos |
| `1280e7a` | T13 | `progress/mutacion_F-030.md` |
| `24a8448` | T14 | Despliegue y M1–M4 en `progress/current.md` |

Tests nuevos (114): sv3 `test_f030_dni_canonico.py` (22),
`test_f030_casado_recurso.py` (59), `test_f030_conciliador_sin_ficha.py` (7);
sv5 `test_f030_coherencia_sin_ficha.py` (5); sv4
`test_f030_portal_recurso.py` (21). **Ningún test existente se ha tocado**
(`git diff dev -- 'services/*/tests/test_f0[0-2]*'` vacío).

## 2. Decisiones y desviaciones

Ninguna desviación de la spec. Decisiones de detalle, dentro de ella:

1. `dni_canonico` usa `re.fullmatch(r"[0-9]{1,7}[A-Z]")` sobre el DNI ya
   normalizado (design §6.1). Un DNI que normaliza a vacío («-», «.») pasa a
   `None` (R2), antes quedaba el texto crudo.
2. `fichas_de_recurso`: «empieza por `MO/`» es literal (sensible a
   mayúsculas, como lo guarda Sigrid); `conide in ides_ficha` sin guarda
   previa de `None` (equivalente y sin mutantes equivalentes). Se devuelven
   de todas las empresas y estados (design §6.2).
3. El paso DNI→recurso se salta si no hay DNI leído (design §6.3 «si fue
   desconocido y hay DNI»). El INFO de R6 lleva `linea`, motivo, empresa y
   fecha; ni DNI ni nombre (comprobado en el test).
4. sv4: el filtro de la cola es una función `_sin_casar_en_cola()` que
   devuelve las dos condiciones (`empleado_ide IS NULL` y método NULL o
   `NOT IN`), usada por `list_unmatched_workers` y `backfill_empleado`, para
   no duplicar la condición. `worker_key_for_registro` y `persona_de` no
   cambian (design §6.4): el casado por recurso se agrupa por nombre leído.
5. Observación (no cambia nada, R20 «como hoy»): reasignar a una ficha una
   línea casada por recurso pone `empleado_ide` y suelta el recurso, pero
   deja `empleado_match_method` = `recurso_*`, igual que hoy deja `nombre`
   o `dni`. Es inocuo: `esta_casado` mira primero `empleado_ide`.
6. sv5 R17: caracterizado a nivel de cliente (`datos_recursos` con `conide`
   0 cae en `res.cif`), de regla (`verificar_recurso`) y de pipeline.

## 3. Fase RED (requisitos centrales, salida real)

Comando de cada servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe
-m pytest -q --tb=line <fichero> [-k ...]`. Trazas recortadas; las líneas son
las reales.

**T2 · R1, R2, R3** (`tests/test_f030_dni_canonico.py`, antes de `dni_canonico`):
```
E   AttributeError: module 'application.services.parte_normalizer' has no attribute 'dni_canonico'   (x15, R1)
tests\test_f030_dni_canonico.py:68: AssertionError: assert ['9876543-b',..., 'X1234567L'] == ['09876543B',..., 'X1234567L']
tests\test_f030_dni_canonico.py:74: AssertionError: assert ['-'] == [None]
tests\test_f030_dni_canonico.py:74: AssertionError: assert ['.'] == [None]
tests\test_f030_dni_canonico.py:121: AssertionError: assert (None, 'none', None, None) == (10, 'dni', '01234567L', 910)
19 failed, 3 passed in 0.30s
```
Después: `22 passed in 0.29s`; suite sv3 `695 passed`.

**T3 · R4 lectura** (`-k lectura`):
```
tests\test_f030_casado_recurso.py:62: TypeError: RecursoRow.__init__() got an unexpected keyword argument 'codigo'
tests\test_f030_casado_recurso.py:79: AttributeError: 'RecursoRow' object has no attribute 'codigo'
2 failed in 0.45s
```
Después, con `test_f023_cliente_sigrid.py` y `test_f023_r3_todo_paginado.py`:
`40 passed` (ningún test de F-023 fijaba las columnas: sin adaptar nada).

**T4 · R4 construcción** (`-k fichas_de_recurso`):
```
E   ModuleNotFoundError: No module named 'application.services.fichas_de_recurso'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```
Después: `11 passed`.

**T6 · R5, R12** (`-k "r5 or r6 or r7 or r8 or r12"`):
```
test_f030_casado_recurso.py:317: AssertionError: assert ('none', None, 0.0) == ('recurso_dni', 950, 1.0)
test_f030_casado_recurso.py:328: AssertionError: assert ('none', None) == ('recurso_dni', 950)
test_f030_casado_recurso.py:334: AssertionError: assert ('alias', 900) == ('recurso_dni', 950)
test_f030_casado_recurso.py:339: AssertionError: assert ('nombre', 900) == ('recurso_dni', 950)
test_f030_casado_recurso.py:345: AssertionError: assert ('none', None) == ('recurso_dni', 950)
test_f030_casado_recurso.py:359: AssertionError: assert EmpleadoMatch...method='none') == EmpleadoMatch...'recurso_dni')
test_f030_casado_recurso.py:388: AssertionError: assert (None, None, ..., 'none', ...) == (None, None, ...rso_dni', ...)
test_f030_casado_recurso.py:406/421/430: ValueError: not enough values to unpack (expected 1, got 0)
10 failed, 9 passed, 13 deselected in 3.52s
```
Los 9 en verde son la **caracterización** de R7 (3, con un doble que
prohíbe mirar `recursos`), R8 (3), R5 «ficha de empleado igual» y R6
«desconocido»/«sin DNI». En R6 el comportamiento (sigue a alias/nombre) ya
pasaba; lo rojo era el INFO (líneas 406/421/430). Después: `78 passed` con
`test_f023_pipeline_match.py`.

**T7 · R9, R10, R11** (`-k "r9 or r10 or r11"`):
```
test_f030_casado_recurso.py:510: AssertionError: assert EmpleadoMatch...thod='nombre') == EmpleadoMatch...curso_nombre')
test_f030_casado_recurso.py:567: AssertionError: assert (20, 920, 'nombre') == (None, None, 'nombre_ambiguo')
test_f030_casado_recurso.py:576: AssertionError: assert (None, 'none') == (None, 'nombre_ambiguo')
test_f030_casado_recurso.py:586: AssertionError: assert 'none' == 'nombre_ambiguo'
test_f030_casado_recurso.py:597: AssertionError: assert ('nombre', 900, 0.8667) == ('recurso_nombre', 950, 1.0)   (x5, R11)
12 failed, 4 passed, 32 deselected in 0.54s
```
Los 4 en verde: baja y otra empresa no compiten, umbral por debajo, y
«sin fichas de recurso el nombre decide igual» (caracterización).

**T8 · R13** (`-k r13`):
```
test_f030_casado_recurso.py:626: AssertionError: assert True is False   (recurso_dni, recurso_nombre)
test_f030_casado_recurso.py:641: AssertionError: assert True is False   (parte casado por recurso)
3 failed, 8 passed, 48 deselected in 0.62s
```

**T9 · R18, R19** (sv4, `tests/test_f030_portal_recurso.py`):
```
:68: AttributeError: module '...parte_repository' has no attribute 'METODOS_RECURSO'
:84: AttributeError: module '...parte_repository' has no attribute 'esta_casado'   (x9)
:91: AssertionError: assert {'Fulano Sin ...PEDRO': False} == {'GOMEZ RUIZ,...Casar': False}   (list_workers x2)
:101: AssertionError: assert ('GOMEZ RUIZ,..., '09876543B') == ('GOMEZ RUIZ,..., '09876543B')   (get_worker)
:111: AssertionError: assert {'Fulano Sin ...PEDRO': False} == {'GOMEZ RUIZ,...Casar': False}   (get_obra)
:118: AssertionError: assert ('GOMEZ RUIZ, PEDRO', False) == ('GOMEZ RUIZ, PEDRO', True)   (get_parte)
:127/:136: AssertionError: assert ['Pedro Gomez...no Sin Casar'] == ['Fulano Sin Casar']   (cola)
:143: assert (2, 0) == (0, 0)   (backfill_empleado)
18 failed, 3 passed in 3.03s
```
Los 3 en verde son R20 (caracterización, 2) y «la confirmación sigue
casando lo sin casar». Después: `21 passed`; suite sv4 `1657 passed`.

**Caracterización (T1), contra el código de hoy**: sv3
`test_f030_conciliador_sin_ficha.py` `7 passed in 0.33s`; sv5
`test_f030_coherencia_sin_ficha.py` `5 passed in 0.30s`, antes de tocar
nada de producción.

## 4. Verificación (resultado real)

- Suites por servicio tras T9: sv3 `754 passed`, sv4 `1657 passed, 1
  warning in 324.32s`, sv5 `362 passed, 1 warning in 12.58s`; sv1/sv2 sin
  cambios (caché).
- R16 (T10): `git diff dev --stat` de `seleccion_sigrid.py`, los dos
  `text_match.py`, `coherencia_recurso.py` y `sigrid_lookup_client.py`:
  **vacío**; tampoco cambian `orm_models.py`, `jornada_resolver.py`,
  `recurso_conciliador.py`, `empleado_matcher.py`, `obra_matcher.py`, sv5,
  sv1, sv2, plantillas ni `app.js`. `tests/test_f023_de_alta_gemelos.py`:
  `14 passed`.
- ruff: los ficheros de producción tocados tienen los mismos avisos que en
  `dev` (0/2/1/86/2/0/44, comparados uno a uno); los nuevos, 0.
- **`bash harness/init.sh`** (HEAD `24a8448` + este informe, T15):
  `1 comprobaciones fallidas`. Todo `[OK]` (sv3 `754 passed`, sv4 `1657
  passed, 1 warning in 493.65s`, sv5 `362 passed`, cobertura y tamaño
  `impl 207/220`, ruff 590 = el de `dev`) **salvo** raíz `1 failed, 141
  passed` (con `-x`), causa ajena (§6). Sin `-x`: `1 failed, 444 passed, 1
  skipped`. Por eso F-030 queda `blocked` en `features.json`.

## 5. Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos | 114 (88 sv3, 21 sv4, 5 sv5), todos en verde |
| Tests ejecutados | raíz `444 passed, 1 skipped, 1 failed` (ajeno, §6); sv3 754; sv4 1657; sv5 362 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 59 líneas cambiadas cubiertas (59/59, umbral 80%, nivel critico)` |
| Mutación | `python -m harness.mutacion --feature F-030 --workers 6 --timeout 600` (HEAD `551a1d8`, 8 ficheros, 199 líneas en alcance, campaña **completa**): **18 generados, 18 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 957.2 s** |
| Tiempo de las suites | raíz 64 s, sv3 ~13–21 s, sv4 324 s, sv5 12.6 s; línea base de mutación sv4 311.7–312.0 s, sv3 9.5–19.0 s |

Mutantes (detalle en `progress/mutacion_F-030.md`): los 4 de
`fichas_de_recurso.py` (`not`, `or/and`, `-`→`+` de conjuntos), los 4 de
`dni_canonico` (`zfill(8→9)`, `n[-1→-2]`, `n[:-1→-2]`, `+`→`-`) y el `or
None`, los 6 del pipeline (`== "ok"`, `!= "desconocido"`, `+` de
candidatas, `is not None` de la ficha de recurso, las dos condiciones de
R13) y los 2 de `esta_casado` en sv4. Ninguno sobrevive: no hay nada que
justificar.

## 6. Pendiente y fuera de alcance

**Bloqueo ajeno de `init.sh`** (anotado en `progress/current.md`): el test
`tests/test_f017_r22_sin_reescritura_historica.py::test_f017_r22_no_hay_ficheros_sql_de_migracion`
hace `rglob("*.sql")` sobre todo el repo y encuentra
`.claude/worktrees/agent-af837e18a30df3345/infra/sql/01_dedicacion_lectura.sql`,
el worktree de **otro agente** (rama `feature/F-031-asiento-analitico`, creado
a las 14:42 durante esta implementación). No es de F-030 y no lo toco ni
cambio el test (es de F-017). Con ese worktree retirado, el resto de
`init.sh` ya sale verde; el líder decide (cerrar el worktree o que el humano
acepte excluir `.claude/worktrees/` en ese test, en otra feature).

**MANUAL (humano)**, con comandos en `progress/current.md`: despliegue sv3 →
sv4 en la misma sesión (sv5 no), M1 (log `recursos=` de sv3), M2 (lectura
`reshor` de la 28 con cuenta ≠ 0 ⇒ 0), M3 (reprocesar los 2 partes de
Porsan de la obra 0724) y M4 (log de cuentas de sv5 con `ok=0
recurso_sin_cuenta=N`, sin aprobar).

Fuera (design §7): recursos sin `res.cif` o con `conide` a una ficha, alias
de recurso, guardar el DNI leído, re-casado en bloque (DA8), alta manual o
jornada de personas sin ficha en sv4, cuenta 0 forzada por empresa (DA9).
No hay mejora del arnés que portar a `arnes-base`.

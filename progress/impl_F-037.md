<!-- progress/impl_F-037.md -->
# F-037 · Informe del implementer — sv3 no duplica la extra automática de una base omitida

Rama `feature/F-037-extras-duplicadas-base-omitida` (worktree `partes-wt-f037`).
Rigor **crítico**. Solo sv3. DA1, DA2 y DA3 aprobadas por el humano el
2026-10-07 (las recomendadas). Intérprete: el worktree no tiene `.venv`; se usó
`C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe`.

## Qué cambió

| Fichero (bajo `services/partes-persistencia/` salvo indicación) | Cambio |
|---|---|
| `application/services/pareja_extra.py` (nuevo) | Núcleo puro: `clave_pareja`, `es_miembro`, `FilaPareja`, `claves_congeladas`, `PlanRevert`, `plan_revert` (design §3). |
| `infrastructure/database/sqlalchemy_parte_repository.py` | `revert_extras_auto` aplica `plan_revert` y loguea con `_log_plan_revert`; `fetch_registros_para_recurso` lee `line_index`, `empleado_line_no`, `extra_auto` y añade `congelada_por_pareja`; helper `_fila_pareja` (congelación por línea = `esta_congelado`). |
| `application/services/recurso_conciliador.py` | Solo `_congelado(reg)` (+ `congelada_por_pareja`) y el comentario de `conciliar_todos`. `esta_congelado` y `ESTADOS_CONGELADOS` intactos. |
| `tests/dobles.py` | `sembrar_lineas` admite por línea `line_index` (defecto: posición), `empleado_line_no` y `recurso_ide` (defecto: None). Compatible con todas las llamadas existentes. |
| `tests/test_f037_pareja.py` (nuevo) | R1–R3 y `plan_revert` caso a caso (27 tests). |
| `tests/test_f037_revert.py` (nuevo) | R4–R9 sobre el repositorio real en SQLite (26 tests). |
| `tests/test_f037_dos_pasadas.py` (nuevo) | R10 (conciliador + `RepositorioFake`) y R11–R16 (conciliador + repositorio real, dos `conciliar_todos`) (15 tests). |
| `docs/ARCHITECTURE.md` (semántica 3), `docs/referencia/partes-proyecto.md` (los dos párrafos de «Cómputo de extras») | R20. |

Commits: `bcc05a9` (in_progress), `edc2aab` T1, `1630e96` T2, `fce22e1` T3,
`9ae3ad0` T4, `4600db4` T5, `7ce8921` T6, `d53ae98` T7, `a86fdaf` y `95c3298` T8,
`60ad036` T9 y el de T10 (este informe).

## Decisiones de diseño (y una desviación menor)

- **Desviación justificada**: `PlanRevert.dobles` es `tuple[tuple[Clave, int], ...]`
  (clave **y** número de extras congeladas) en vez de `tuple[Clave, ...]`. El
  WARNING de R7 lleva ese número (design §4); calcularlo de nuevo en el
  repositorio duplicaría la regla del núcleo.
- `dobles` sale en orden de primer `registro_id` (el plan entero es
  determinista por `registro_id`, design §3).
- Mensajes de log (sin nombres ni DNIs):
  - INFO de siempre: `[repo] revert de extras: N linea(s) CONGELADAS respetadas …` (solo congeladas por sí mismas).
  - INFO: `[repo] revert de extras: N linea(s) protegidas por su pareja congelada (F-037).`
  - WARNING R6: `[repo] revert de extras: N extra(s) automatica(s) DUPLICADA(S) borrada(s): su pareja ya tiene la extra congelada en Sigrid (F-037); ids: a, b, …` (máx. 10 ids).
  - WARNING R7: `[repo] revert de extras: la pareja document_id=X line_index=Y tiene N extras automaticas CONGELADAS; no se borra ninguna, revisar a mano en Sigrid (F-037).`
- `IndiceFijo` es un doble **local** de `test_f037_dos_pasadas.py` (design §6),
  no en `dobles.py`: así el solape con F-036 en `dobles.py` se queda en el
  bloque de `sembrar_lineas`.
- **Matiz del humano** («no debería ni salir la tercera línea»): R11–R14
  comprueban en **cada** pasada `resumen["extras_reclasificadas"] == 0` (el
  conciliador no crea ninguna `extra_auto`, ni transitoria) y que las filas son
  exactamente las de partida (R13: las de partida sin el duplicado). El borrado
  de duplicados (R6/R13) solo limpia lo ya creado en producción.
- R15 se prueba con la línea libre sembrada **antes** y **después** de la
  pareja (parametrizado). Con la libre antes, la base tiene el id mayor y sin
  R10 sería la primera candidata a recorte: es el caso que discrimina `_congelado`
  una vez arreglada la reversión (T3).

## Fase RED (rigor crítico): trazas reales

Todas desde `services/partes-persistencia` con
`../../../partes/.venv/Scripts/python.exe -m pytest -q <fichero>`.

**T2 · R1–R3 y `plan_revert`** — `pytest -q tests/test_f037_pareja.py` antes del módulo:

```
E   ModuleNotFoundError: No module named 'application.services.pareja_extra'
ERROR tests/test_f037_pareja.py
1 error in 1.03s
```

**T3 · R4–R8** — `pytest -q tests/test_f037_revert.py` contra el `revert_extras_auto` de siempre:

```
E       assert (True, 10.0, None, False) == (True, 8.0, 10.0, False)   # R4: la base omitida se restauraba a 10 h
E       assert (True, 4.0, None, False) == (True, 0.0, 4.0, False)     # R4: la base de 0 h volvía a 4 h
E       assert 1 == 0   (revert_extras_auto())                         # R5: borraba la extra de la base registrada
E       StopIteration                                                  # R6: no había WARNING de duplicados
E       AssertionError: assert [] == ['[repo] revert de extras: 2 linea(s) protegidas por su pareja congelada (F-037).']
FAILED …::test_f037_r4_base_omitida_con_su_extra_registrada_no_se_toca
FAILED …::test_f037_r4_base_de_cero_horas_con_su_extra_registrada
FAILED …::test_f037_r4_con_la_extra_encolada_tampoco
FAILED …::test_f037_r4_sin_empleado_line_no_tambien_es_pareja
FAILED …::test_f037_r5_base_registrada_conserva_su_extra_sin_estado
FAILED …::test_f037_r5_base_registrada_conserva_su_extra_en_error
FAILED …::test_f037_r6_el_duplicado_sin_estado_se_borra_y_se_avisa
FAILED …::test_f037_r6_el_aviso_lista_como_mucho_diez_ids
FAILED …::test_f037_r7_dos_extras_congeladas_ninguna_se_borra
FAILED …::test_f037_r7_una_por_pareja_con_dos_parejas_dobles
FAILED …::test_f037_r8_parejas_libres_se_revierten_como_siempre
FAILED …::test_f037_r8_el_info_de_congeladas_cuenta_solo_las_de_por_si
FAILED …::test_f037_r8_revertir_dos_veces_da_lo_mismo
13 failed, 5 passed in 8.24s
```

Los 5 verdes son de caracterización (otro `empleado_line_no`, parte aprobado,
sin duplicados no hay aviso, sin protegidas no hay INFO, extra explícita).

**T4 · R9** — `pytest -q tests/test_f037_revert.py -k r9` antes de la marca:

```
E       KeyError: 'congelada_por_pareja'          (x7)
E       AssertionError: … Extra items in the right set: 'congelada_por_pareja'
8 failed, 18 deselected in 8.94s
```

**T5 · R10–R15** — `pytest -q tests/test_f037_dos_pasadas.py` contra el código
**anterior a F-037** (árbol de `edc2aab` extraído con `git archive` a un
directorio temporal, con el test nuevo copiado):

```
E       AssertionError: assert False is True  (where False = _congelado({'congelada_por_pareja': True}))
E       assert [1, 2] == [2]                                   # R10: re-resolvía el recurso
E       assert [(5, 5.0, 3.0)] == [(1, 0.0, 3.0)]              # R10: recortaba la base marcada
E       assert [(5, 6.0, -2.0)] == [(1, 4.0, -2.0)]            # R10: la base marcada hacía de pivote
>           assert resumen["extras_reclasificadas"] == 0
E           assert 1 == 0                                      # R11, R12, R13 x2: aparece una extra_auto NUEVA
E           AssertionError: … Right contains one more item: (2, 0, 2.0, None, True, None)     # R14: desaparece la extra
E           AssertionError: … Right contains one more item: (2, 0, 2.0, None, True, 'error')  # R14 (error)
E           AssertionError: assert (2, 0, 5.0, 1...se, 'omitido') == (2, 0, 8.0, 1...se, 'omitido')  # R15: recorta la base
E           assert 2 == 1                                      # R15: dos extras nuevas en vez de una
13 failed, 2 passed in 11.30s
```

Los 2 verdes son R16 (caracterización). Contra HEAD tras T4 (reversión ya
arreglada, `_congelado` aún sin tocar) seguían rojos los 5 de R10 y
R15[libre_primero]: `6 failed, 9 passed`. Tras T5: `15 passed`.

**Caracterización R16–R18** (T1, verdes antes y después): R16 (2 tests) en
verde contra el código anterior; `test_f015_r31_*`, `test_f015_r32_*`,
`test_f023_recurso_conciliador.py` (58 tests junto con R16) y el guardián raíz
`tests/test_f024_borrado_no_congela_gemelos.py` (4) en verde antes y después.

## Qué se verificó (resultado real)

- Suites F-037: `70 passed` (pareja 29, revert 26, dos pasadas 15).
- Suite completa de sv3: `825 passed in 29.57s` (antes de F-037: 755 en el
  `init.sh` de arranque, sin los tests nuevos).
- Guardián F-024 (raíz): `4 passed`. `tests/test_documentos_del_arnes.py`: `17 passed`.
- **T6 (R17, R18)**: `git diff dev --stat -- services/partes-front
  services/partes-transfer services/partes-persistencia/infrastructure/database/orm_models.py CLAUDE.md`
  vacío; `git diff dev` de `tests/test_f015_*`, `test_f023_*`, `test_f024_*`
  (sv3 y raíz) vacío; el diff de `recurso_conciliador.py` solo toca `_congelado`
  y un comentario de `conciliar_todos` (ni `ESTADOS_CONGELADOS` ni
  `esta_congelado`). `azure-apps/partes.md` no se toca (R20).
- `bash harness/init.sh`: ver «Evidencias».

## Fuera del alcance / lo que falta

- **MANUAL (humano)**, anotado en `progress/current.md`: M1 antes de desplegar;
  despliegue solo de sv3 (`infra/redeploy_partes.ps1 -Solo sv3`, lo pide el
  humano); M2 = 0 parejas con > 1 `extra_auto` tras la primera pasada (R21);
  M3 en los logs; M4 informativo (DA3: reposición en feature aparte si sale algo).
- No se ejecutó nada contra producción ni contra la base `partes`.
- Riesgo R-b del diseño (base sin `horas_orig` + extra congelada): la lectura la
  marca congelada por pareja (test `test_f037_r9_una_base_sin_horas_orig_tambien_se_marca`);
  la reversión no la ve, como prevé el diseño.
- Merge con F-036: solape esperado solo en `tests/dobles.py` (bloque
  `sembrar_lineas`) y en las altas de `features.json` / `BACKLOG.md` /
  `progress/current.md`.
- Falta: reviewer (APPROVED) y, tras él, `done`.

## Corrección tras la review (pasada 1, CHANGES_REQUESTED documental)

Sin cambios de código. `progress/current.md` lleva ya el comando exacto de
M1–M4 (solo lectura, base `partes`, las lanza el humano): M1 con la regla de
congelación entera `AND (r.sigrid_estado IN ('encolado','registrado','dedicacion')
OR d.approved)`, M2 tal cual, M3 como consulta de Log Analytics de
`ca-sv3-persistencia` con «DUPLICADA(S) borrada(s)» y «revisar a mano en
Sigrid» (workspace leído con `az containerapp env show`, no versionado) y M4
como SQL (`NOT EXISTS` con `IS NOT DISTINCT FROM`). `design.md` §8 alineado
(M1 con `OR d.approved`; remite a `current.md` para los comandos; 249/250
líneas). **M1 ya ejecutada por el líder en producción el 2026-10-07: 0 filas;
los 4 documentos con duplicados no están aprobados**, así que los 7 duplicados
son borrables por la primera pasada (R6) y ninguno cae en R7.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | sv3: **825 passed** (70 de F-037); resto de suites en el `init.sh` final (abajo) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 83 líneas cambiadas cubiertas (83/83, umbral 80%, nivel critico)` (`python -m harness.cobertura --base dev`, tras `coverage run` de sv3) |
| Mutación | campaña **completa** (sin muestreo), `--workers 6 --timeout 600`: **21 generados, 21 muertos, 0 supervivientes, 0 timeouts** en 262.7 s → `progress/mutacion_F-037.md`. La primera pasada dejó 2 supervivientes (`frozen=False` en `FilaPareja` y `PlanRevert`): hueco real, matado con dos tests de inmutabilidad (`a86fdaf`); análisis en el informe de mutación |
| Tiempo de la suite | sv3 completa 29.57 s; suites F-037 8.16 s; línea base de mutación ≈ 40–45 s por worktree |
| `bash harness/init.sh` | **verde, exit 0** (2026-10-07): raíz 443 passed, 3 skipped en 249.97 s; sv3 825 passed en 38.55 s; sv1, sv2, sv4 y sv5 en verde por caché (árbol sin cambios desde el verde del arranque de esta sesión: sv1 74, sv2 8, sv4 1682 + 1 skipped, sv5 522); PUERTA COBERTURA 100.0% (83/83); PUERTA TAMAÑO OK (impl 164/220); avisos previos: ruff 617 (deuda), features blocked F-014 y F-032, infra sin tests |

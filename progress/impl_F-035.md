<!-- progress/impl_F-035.md -->
# F-035 · Informe del implementer

Rama `feature/F-035-selector-recursos-por-empresa`. Rigor **estándar**. Solo
sv4 (+ guardián de la raíz, `docs/ARCHITECTURE.md` y `CLAUDE.md`); sv3, sv5 y
schema sin cambios.

Decisiones del humano (2026-10-07): DA1 y DA2 aprobadas (design §8); DA3/DA4
como en la spec. **Bloqueo y desbloqueo**: el guardián ajeno
`test_f016_r20_f016_no_anade_ni_cambia_ninguna_ruta_de_sigrid` (lista cerrada
de rutas `/api/sigrid/*`) se puso rojo con la ruta de R5; el humano eligió la
opción (a): se añadió `("/api/sigrid/recursos", ("GET",))  # F-035 (R5)` y la
excepción quedó escrita en R22.

## Qué cambió (commits locales, sin push)

| Commit | Tarea | Ficheros (bajo `services/partes-front/` salvo raíz) |
|---|---|---|
| `35cf07c` | arranque | `features.json`, design §8, `current.md` |
| `044b538` | T1 | `infrastructure/sigrid/sigrid_lookup_client.py` (`RecursoOption`, `_SQL_RECURSOS_ACTIVOS`, `fetch_recursos_activos`); `tests/test_f035_recursos_cliente.py`; raíz `tests/test_f023_de_alta_gemelos.py` (+`test_f035_r23_…`) |
| `91b80db` | T2 | `application/services/recurso_catalog.py`; `tests/test_f035_recurso_catalog.py` |
| `d961c69` | T3 | `infrastructure/database/parte_repository.py`; `tests/test_f035_repositorio.py` |
| `1eb933f` | T4 | `interface_adapters/web/app.py`; `tests/test_f035_endpoints.py` |
| `c7703a4` | T5 (RED) | `tests/test_f035_vistas.py` |
| `004ce6b` / `9a77fc8` | bloqueo / desbloqueo | `current.md`; guardián F-016 (1 línea + docstring); R22 y design §4 |
| `5b23ec6` | T5 | `templates/conciliacion.html`, `nuevo_parte.html`, `base.html`, `obra_detail.html`, `static/styles.css` (2 reglas) |
| `34ac53d` | T6 | `static/app.js`; tests JS en `test_f035_vistas.py` |
| `35fcfe4` | T7 | `docs/ARCHITECTURE.md` (semántica 12), `CLAUDE.md` (lista cerrada, DA2) |

## Decisiones de diseño y desviaciones (para el reviewer)

- **`METODOS_RECURSO` no cambia (desviación de design §4, aceptada por el
  humano y anotada en design §4).** El test ajeno
  `test_f030_r18_metodos_de_recurso` fija ese conjunto (espejo de sv3). Mismo
  comportamiento con `METODO_RECURSO_MANUAL` y la lista aparte
  `_METODOS_CASADO_SIN_FICHA = METODOS_RECURSO | {recurso_manual}`, que usan
  `esta_casado` y `_sin_casar_en_cola`.
- **Caché JS**: `fetchRecursos()` (combo de obra/listado) y la caché propia de
  `_comboSimple` (Nuevo parte, modal), que no se modifica por DA11 de F-016.
- La regla R12/R13 vive SOLO en `asignacion_de`; el endpoint la serializa con
  `Asignacion.como_guardar()` (`guardar` de cada item) y el JS copia esos
  valores a los hidden. `_trabajador_pedido` (app.py) resuelve el cuerpo de
  confirmar/reasignar: `recurso_ide` → catálogo de recursos (404 sin tocar
  nada); sin él, el camino de `ide` de siempre (R15). Alias solo con ficha (R14).
- `_jornada_sugerida` se comparte entre `/empleados` y `/recursos`.
- Conciliar: `empresa_defecto` = la única empresa de los partes del grupo; los
  candidatos se calculan sobre los recursos de esa empresa (R7, R8). El botón
  «Casar» lleva `data-recurso-ide` (se quitó `data-ide`: un JS viejo en caché
  enviaría `ide` nulo → 400, nunca un empleado equivocado).
- DA1 en JS: `fijarEmpresa(sel, empresa)` pone la empresa de la obra y
  bloquea el selector (si la empresa no está en `NOMBRES_EMPRESA`, añade la
  opción «Empresa N»); al cambiar obra o empresa se vacía el trabajador de
  otra empresa (lógica F-023). En el modal con trabajador fijado por la
  página, el selector de empresa se oculta.
- Fuera del repo (líder/humano): `azure-apps/partes.md` dice que sv4 no crea
  rutas `/api/sigrid/*` y lista los métodos «casado»: valorar `/recursos` y `recurso_manual`.

## Tests (resultado real)

- F-035: 6 ficheros en sv4 + 1 test en la raíz. `test_f035_vistas.py` → 15
  passed (13 + 2 de cableado JS; +2 en la revisión 1); `test_f035_endpoints.py` → 18 passed
  (16 + 2 añadidos tras la mutación); repositorio 25, catálogo 12, cliente 10.
- **Suite completa de sv4 tras T6: 1761 passed in 1053.57s** (máquina
  compartida con otros dos implementers; tras T3 fue 1730 passed in 534.76s).
- `node --check static/app.js` → sin errores. Parseo Jinja2 de las 4
  plantillas: `test_f035_plantillas_parsean` (4 passed).
- Tests ajenos que leen `app.js` o las vistas tocadas (7 + 7 ficheros): 213 y
  149 passed.
- `bash harness/init.sh`: ver «Evidencias».

## Fase RED (trazas reales, `pytest -q --tb=line`)

Desde `services/partes-front/` salvo R23. En T1/T2 se dejó un esqueleto con
`NotImplementedError` para que cada test falle por sí mismo.

**T1 · R1–R4** — `python -m pytest tests/test_f035_recursos_cliente.py -q --tb=line`
```
E   NotImplementedError: F-035 T1 en RED      (x9)
FAILED tests/test_f035_recursos_cliente.py::test_f035_r1_una_consulta_paginada_por_res_ide_con_alta_a_hoy
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_con_ficha_y_sin_ficha
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_sin_cif_el_dni_es_el_de_la_ficha
FAILED tests/test_f035_recursos_cliente.py::test_f035_r3_sin_dni_ni_en_la_ficha_no_se_ofrece
FAILED tests/test_f035_recursos_cliente.py::test_f035_r4_solo_clase_persona_en_el_sql
(+4 más del mismo fichero)
9 failed, 1 warning in 4.42s
```
**R23** (raíz) — `python -m pytest tests/test_f023_de_alta_gemelos.py -q --tb=line`
```
E   AssertionError: ...\sigrid_lookup_client.py no define `_SQL_RECURSOS_ACTIVOS`
FAILED tests/test_f023_de_alta_gemelos.py::test_f035_r23_el_sql_de_recursos_de_sv4_conserva_la_misma_regla
1 failed, 14 passed in 0.10s
```
**T2 · R5, R6, R12, R13** — `python -m pytest tests/test_f035_recurso_catalog.py -q --tb=line`
```
E   NotImplementedError: F-035 T2 en RED      (x12)
FAILED ...::test_f035_r5_filtra_por_empresa_y_sin_ella_todos
FAILED ...::test_f035_r6_fallo_de_refresco_conserva_la_ultima_lista
FAILED ...::test_f035_r12_con_ficha_se_guarda_la_ficha_y_su_dni
FAILED ...::test_f035_r13_sin_ficha_se_guarda_el_recurso
(+8 más)
12 failed in 0.36s
```
**T3 · R12, R13, R16, R19, R8** — `python -m pytest tests/test_f035_repositorio.py -q --tb=line`
```
E   TypeError: ParteReviewRepository.backfill_empleado() got an unexpected keyword argument 'reside'
E   TypeError: ParteReviewRepository.reassign_empleado_by_registro_ids() got an unexpected keyword argument 'reside'
E   AttributeError: module 'infrastructure.database.parte_repository' has no attribute 'METODO_RECURSO_MANUAL'
E   assert False is True                       (esta_casado con recurso_manual)
E   AssertionError: assert (None, 903, 903, None) == (None, 903, 9...curso_manual')
E   AssertionError: assert (True, None) == (True, 'recurso_manual')
E   KeyError: 'empresas'
15 failed, 10 passed in 3.54s
```
**R16 específico** (quitando a mano los dos campos de `_REG_UNDO_FIELDS` y
restaurando con `git checkout`) — `… tests/test_f035_repositorio.py -q --tb=line -k r16`
```
E   KeyError: 'empleado_reside'
FAILED tests/test_f035_repositorio.py::test_f035_r16_deshacer_restaura_reside_y_metodo
FAILED tests/test_f035_repositorio.py::test_f035_r16_snapshot_antiguo_sin_las_claves_no_falla
2 failed, 23 deselected in 6.35s
```
**T4/T5 · R5, R9, R11–R14, R21, R7, R8, R10, R17, R18, R20** —
`python -m pytest tests/test_f035_endpoints.py tests/test_f035_vistas.py -q --tb=line`
```
E   KeyError: 'ok'                             (GET /api/sigrid/recursos: 404)
E   assert set() == {901, 902, 903}            (buscar sin recursos)
E   assert 400 == 404                          (recurso_ide desconocido)
E   AssertionError: {"ok":false,"error":"Faltan datos: nombre_leido='Tres Solo Recurso', ide=None."}
E   AssertionError: {"ok":false,"error":"Falta o es inválido 'ide' (None)."}
E   assert ('MO/0037' in '<div class="recon-card recon-sin" data-nombre="Tres Solo Recurso">...')
E   AssertionError: la tarjeta no tiene selector de empresa
E   AssertionError: Nuevo parte sin selector de empresa
E   AssertionError: el modal sin selector de empresa
E   assert (['<div class="combo-emp" data-registro-id="4">', ...] and False)
19 failed, 10 passed in 37.78s
```
Los 10 que ya pasaban: caracterización (R15, R19 vía T3, negativo de R7,
parseo Jinja2). Los tests de cableado JS de T6 son de no regresión, no RED.

## Verificaciones MANUALES pendientes (T9, humano, SOLO LECTURA)

Comando exacto y las tres comprobaciones en `progress/current.md` (§ T9).

## Fuera de alcance

Cambios en sv3/sv5 (F-036), alias de recursos, filtro de empresa en el listado
de trabajadores, `jornada_dia` en `/api/sigrid/recursos`, reprocesar líneas ya
casadas.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (suite sv4 en `init.sh`) | **1764 passed**, 1 warning, in 959.07 s (máquina compartida) |
| Tests de la raíz (`init.sh`) | 446 passed, 1 skipped in 127.92 s |
| Tests propios de F-035 | 90 en sv4 (cliente 10, catálogo 13, repositorio 31, endpoints 19, vistas 17) + 1 en la raíz (`test_f035_r23_…`), todos en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 96.9% de 193 líneas cambiadas cubiertas (187/193, umbral 80%, nivel estandar)` |
| Mutación (muestreada, 20 de 69, semilla 20260820) | campaña: 11 muertos, 3 supervivientes, 6 timeouts, 5973.8 s (`--workers 6 --timeout 1200`) |
| Mutación tras análisis | 15 muertos (4 timeouts re-juzgados a mano), 1 equivalente, 2 huecos cerrados con test nuevo, 2 huecos de bajo riesgo/previos sin test. Detalle: `progress/mutacion_F-035.md` |
| Tamaño del papeleo | `PUERTA TAMAÑO: … requirements 142/150, design 248/250, impl …/220` |
| `bash harness/init.sh` | ver bloque siguiente |

**Timeouts de la campaña.** La línea base por worktree fue ~1470 s y fijé el
timeout a 1200 s: los 6 primeros mutantes dieron timeout (no es medición). Se
re-juzgaron aplicando cada mutante y corriendo los 6 ficheros de tests de la
feature (106 tests), restaurando con `git checkout`:
```
sigrid_lookup_client.py:358 -> SUPERVIVIENTE | 106 passed      (hueco real: test nuevo, ahora muere)
sigrid_lookup_client.py:352 -> MUERTO | 6 failed, 100 passed
sigrid_lookup_client.py:347 -> MUERTO | 6 failed, 100 passed
parte_repository.py:3162    -> MUERTO | 2 failed, 104 passed
recurso_catalog.py:73       -> SUPERVIVIENTE | 106 passed      (equivalente: now - 0 >= ttl)
recurso_catalog.py:97       -> MUERTO | 1 failed, 105 passed
```
Tests añadidos tras la campaña (campaña NO relanzada, rigor estándar):
`test_f035_r15_ide_desconocido_404_ok_false` (mata `app.py:1191`: `assert
True is False`, 2 failed) y `test_f035_r2_la_primera_categoria_y_candef_no_nulos_mandan`
(mata `sigrid_lookup_client.py:358`: `('Oficial', 6.0) == ('Oficial', 8.0)`).

## Revisión 1 (CHANGES_REQUESTED, `progress/review_F-035.md`)

| Cambio | Commit | Test (RED → verde) |
|---|---|---|
| Bug: callback de «Nuevo parte» con `e.` tras renombrar a `r` (`ReferenceError`: sin categoría, jornada, calendario ni `updateBtn`) | `1d5cbef` | `test_f035_r17_r19_nuevo_parte_al_elegir_recurso_rellena_todo` y su gemelo del modal: aíslan el `_comboSimple(...)` de app.js y lo **ejecutan con node** con un `document` falso (skip si no hay node) |
| (a) reasignar a una ficha quita `recurso_manual` (otras marcas no se tocan) | `e43a954` | `test_f035_r12_reasignar_a_una_ficha_quita_recurso_manual` (3 reasignaciones × por recurso / por `ide`) |
| (b) `/api/sigrid/recursos` con `ok: false` si Sigrid nunca cargó (`RecursoCatalog.cargado`) | `e43a954` | `test_f035_r5_cargado_distingue_nunca_cargo_de_lista_vacia`, `test_f035_r5_endpoint_recursos_primera_carga_fallida_ok_false` |

T9 con su comando exacto, en `progress/current.md`. No se tocan el orden del
DNI de R2 ni `CLAUDE.md` (los resuelve el líder al mergear con F-036).

RED del bug — `python -m pytest tests/test_f035_vistas.py -q --tb=short -k nuevo_parte_al_elegir`
(el gemelo del modal ya pasaba):
```
E   AssertionError: [eval]:34
E             document.getElementById("categoria").value = e.categoria || "";
E     ReferenceError: e is not defined
E         at [eval]:34:54
FAILED tests/test_f035_vistas.py::test_f035_r17_r19_nuevo_parte_al_elegir_recurso_rellena_todo
1 failed, 16 deselected in 8.75s
```
RED de (a) y (b) — `python -m pytest tests/test_f035_repositorio.py tests/test_f035_recurso_catalog.py tests/test_f035_endpoints.py -q --tb=line -k "quita_recurso_manual or cargado or primera_carga"`:
```
E   AssertionError: assert 'recurso_manual' is None          (x6)
E   AttributeError: 'RecursoCatalog' object has no attribute 'cargado'
E   assert (True is False)                                   (ok del endpoint)
8 failed, 55 deselected in 8.81s
```
Tras el arreglo: los 5 ficheros de F-035 + F-023 + F-030 → 113 passed;
`test_f035_vistas.py` → 17 passed; `node --check static/app.js` sin errores.

## Cierre

CIERRE_R1

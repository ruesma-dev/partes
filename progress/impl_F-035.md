<!-- progress/impl_F-035.md -->
# F-035 · Informe del implementer (PARCIAL: feature `blocked`)

Rama `feature/F-035-selector-recursos-por-empresa`. Rigor **estándar**.
Decisiones del humano (2026-10-07): DA1 y DA2 aprobadas (anotadas en design
§8); DA3/DA4 como en la spec.

**Estado: BLOQUEADA en T5.** Motivo y opciones en `progress/current.md`
(guardián ajeno `test_f016_r20_f016_no_anade_ni_cambia_ninguna_ruta_de_sigrid`
en rojo por la ruta nueva `/api/sigrid/recursos` que exige R5). Este informe
se completa al retomar (T5–T10, cobertura, mutación, «Evidencias» finales).

## Qué cambió (T1–T4, comiteado)

| Commit | Tarea | Ficheros |
|---|---|---|
| `35cf07c` | arranque | `features.json` (in_progress), design §8 (DA1/DA2 aprobadas), `current.md` |
| `044b538` | T1 | `infrastructure/sigrid/sigrid_lookup_client.py` (`RecursoOption`, `_SQL_RECURSOS_ACTIVOS`, `fetch_recursos_activos`); `tests/test_f035_recursos_cliente.py`; raíz `tests/test_f023_de_alta_gemelos.py` (+ `test_f035_r23_...`) |
| `91b80db` | T2 | `application/services/recurso_catalog.py` (`RecursoCatalog`, `Asignacion`, `asignacion_de`); `tests/test_f035_recurso_catalog.py` |
| `d961c69` | T3 | `infrastructure/database/parte_repository.py` (`METODO_RECURSO_MANUAL`, `_poner_trabajador` con `reside` en las 4 asignaciones, undo, `crear_parte_manual`, `empresas` en `list_unmatched_workers`); `tests/test_f035_repositorio.py` |
| `1eb933f` | T4 | `interface_adapters/web/app.py` (catálogo, `/api/sigrid/recursos`, Conciliar por empresa, `buscar?empresa=`, `recurso_ide` en confirmar/reasignar, `empresa_obra`, global `EMPRESAS`); `tests/test_f035_endpoints.py` |
| `c7703a4` | T5 (RED) | `tests/test_f035_vistas.py` (plantillas aún sin tocar) |

Rutas bajo `services/partes-front/` salvo la raíz indicada.

## Decisiones de diseño y desviaciones

- **`METODOS_RECURSO` no cambia (desviación de design §4, justificada).** El
  diseño decía añadirle `recurso_manual`, pero el test ajeno
  `test_f030_r18_metodos_de_recurso` fija ese conjunto (espejo de sv3) y R22
  prohíbe tocar tests ajenos. Mismo efecto con `METODO_RECURSO_MANUAL` +
  `_METODOS_CASADO_SIN_FICHA`, que usan `esta_casado` y `_sin_casar_en_cola`.
- `Asignacion.como_guardar()` serializa los `empleado_*` para el JS (`guardar`
  del endpoint): la regla R12/R13 vive solo en `asignacion_de`.
- `_trabajador_pedido` (app.py) resuelve el cuerpo de confirmar/reasignar:
  `recurso_ide` → catálogo de recursos (404 si no está); sin él, el camino de
  `ide` de siempre (R15). Alias solo si hay ficha (R14).
- `_jornada_sugerida` se extrae a función compartida por `/empleados` y
  `/recursos` (misma regla).
- Conciliar: `empresa_defecto` = la única empresa de los partes del grupo; los
  candidatos se calculan sobre los recursos de esa empresa (R7/R8).

## Tests (resultado real)

- T1: `pytest tests/test_f035_recursos_cliente.py tests/test_f023_catalogo_empresa.py`
  → 38 passed; raíz `pytest tests/test_f023_de_alta_gemelos.py` → 15 passed.
- T2: `test_f035_recurso_catalog.py` → 12 passed.
- T3: `test_f035_repositorio.py` + F-023 + F-030 → 75 passed. Suite completa
  de sv4 tras T3: **1730 passed in 534.76s**.
- T4: `test_f035_endpoints.py` → 16 passed. Batería de sv4 que toca vistas y
  endpoints (20 ficheros): 598 passed, 8 failed = el guardián F-016 (motivo del
  bloqueo) + 7 de `test_f035_vistas.py` (RED esperado de T5).

## Fase RED (trazas reales, salida de `pytest -q --tb=line`)

Comandos lanzados desde `services/partes-front/` (salvo el de la raíz). En T1
y T2 se dejó un esqueleto que lanza `NotImplementedError` para que cada test
falle por sí mismo y no por un `ImportError` de colección.

**T1 · R1–R4** — `python -m pytest tests/test_f035_recursos_cliente.py -q --tb=line`
```
E   NotImplementedError: F-035 T1 en RED      (x9)
FAILED tests/test_f035_recursos_cliente.py::test_f035_r1_una_consulta_paginada_por_res_ide_con_alta_a_hoy
FAILED tests/test_f035_recursos_cliente.py::test_f035_r1_encadena_paginas - N...
FAILED tests/test_f035_recursos_cliente.py::test_f035_r1_la_ficha_enlazada_es_la_de_res_conide
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_con_ficha_y_sin_ficha
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_sin_cif_el_dni_es_el_de_la_ficha
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_el_cif_manda_sobre_la_ficha
FAILED tests/test_f035_recursos_cliente.py::test_f035_r2_una_opcion_por_recurso_que_completa_categoria
FAILED tests/test_f035_recursos_cliente.py::test_f035_r3_sin_dni_ni_en_la_ficha_no_se_ofrece
FAILED tests/test_f035_recursos_cliente.py::test_f035_r4_solo_clase_persona_en_el_sql
9 failed, 1 warning in 4.42s
```
**R23** (raíz) — `python -m pytest tests/test_f023_de_alta_gemelos.py -q --tb=line`
```
E   AssertionError: ...\services\partes-front\infrastructure\sigrid\sigrid_lookup_client.py no define `_SQL_RECURSOS_ACTIVOS`
FAILED tests/test_f023_de_alta_gemelos.py::test_f035_r23_el_sql_de_recursos_de_sv4_conserva_la_misma_regla
1 failed, 14 passed in 0.10s
```
**T2 · R5, R6, R12, R13** — `python -m pytest tests/test_f035_recurso_catalog.py -q --tb=line`
```
E   NotImplementedError: F-035 T2 en RED      (x12)
FAILED ...::test_f035_r5_filtra_por_empresa_y_sin_ella_todos
FAILED ...::test_f035_r6_fallo_de_refresco_conserva_la_ultima_lista
FAILED ...::test_f035_r6_si_nunca_cargo_lista_vacia_y_reintenta
FAILED ...::test_f035_r12_con_ficha_se_guarda_la_ficha_y_su_dni
FAILED ...::test_f035_r13_sin_ficha_se_guarda_el_recurso
(+7 más del mismo fichero)
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
**R16 específico** (con `reside` ya implementado, quitando a mano los dos
campos de `_REG_UNDO_FIELDS` y restaurando después con `git checkout`) —
`python -m pytest tests/test_f035_repositorio.py -q --tb=line -k r16`
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
Los 10 que ya pasaban son de caracterización (R15 por `ide`, R19 por el
endpoint de alta, que ya cubría T3) y el negativo de R7.

## Qué falta (al retomar, tras la decisión del humano)

- Resolver el guardián F-016 según la opción elegida (current.md).
- T5 plantillas (`conciliacion.html`, `nuevo_parte.html`, `base.html`,
  `obra_detail.html`); T6 `app.js` (sin modificar `_comboSimple`); T7
  `docs/ARCHITECTURE.md` y lista cerrada de `CLAUDE.md` (DA2); T8 cobertura,
  mutación e informe completo; T9 verificación MANUAL del humano en local
  (solo lectura); T10 `bash harness/init.sh` en verde.

## Evidencias (parciales; se completan en T8)

| Evidencia | Valor |
|---|---|
| Tests F-035 ejecutados | 76: 75 en sv4 (68 en verde, 7 de vistas en RED esperado de T5; 64.47 s junto al guardián F-016, que falla) + 1 en la raíz (`test_f035_r23_...`, verde) |
| Suite sv4 completa (tras T3) | 1730 passed in 534.76s |
| Cobertura de líneas cambiadas | PENDIENTE: `init.sh` no llega a la puerta (pytest en rojo por el bloqueo) |
| Mutación | PENDIENTE (T8) |
| `bash harness/init.sh` | no ejecutado al bloquear: quedaría en rojo por el guardián F-016 |

Nota del arranque: el primer `bash harness/init.sh` de la sesión (árbol
limpio, antes de tocar nada) cayó en pytest de la raíz (`sF` hacia el 96 %);
`python -m pytest tests -q` justo después dio 445 passed, 1 skipped.
Parece intermitente (había otro implementer en paralelo en `partes-wt-f036`).

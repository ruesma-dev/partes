<!-- progress/impl_F-042.md -->
# F-042 · Informe del implementer (PARCIAL: feature BLOCKED en T4)

Rama `feature/F-042-recalcular-extras-al-cambiar-fecha`, worktree `partes-wt-f042`.
Rigor **crítico**. Estado: **blocked** — motivo y opciones en `progress/current.md`.

## Qué cambió hasta ahora

| Tarea | Estado | Ficheros |
|---|---|---|
| T1 | [x] | sv3 `interface_adapters/workers/{__init__,mensajes,despacho}.py`; `tests/test_f042_despacho.py` |
| T2 | [x] | sv3 `main_worker.py` (usa `construir_handler`, `build_app` una vez, docstring con los dos tipos), `interface_adapters/api/app.py` (`app.state.recurso_conciliador`) |
| T3 | [x] | sv3 `tests/test_f042_domingo_a_jueves.py` (R19–R21, repositorio real sobre SQLite) |
| T4 | implementada, sin `[x]` | sv4 `config/settings.py` (`cola_persistencia`), `infrastructure/persistencia/{__init__,recalculo_publisher}.py`, `interface_adapters/web/app.py` (`build_app(..., recalculo_publisher=None)` y `patch_parte_fecha`), `tests/test_f042_recalculo_fecha.py` |
| T5–T13 | pendientes | — |

## Decisiones de diseño tomadas

- `mensajes.clasificar`: `tipo` ausente o `None` ⇒ ingesta; `"recalcular"` ⇒ recálculo;
  cualquier otro valor (incluidos `""`, `False`, `"RECALCULAR"`) ⇒ `MensajeDesconocido`
  con `repr(tipo)` en el texto; un payload que no es `dict` ⇒ `MensajeDesconocido` con el
  nombre del tipo recibido.
- El WARNING de R17 lleva `motivo`, `document_id` y autor, igual que el INFO de R14.
- `recalculo_publisher.peor_estado` (para T5, deshacer con varios documentos): no está en
  el §3 del diseño con ese nombre, pero es la regla «el peor estado: `fallo` > `sin_cola`
  > `pedido`» que el diseño pide en `undo_apply`; vive junto a los estados.
- `__init__.py` nuevos con la línea de ruta (C3), sin más contenido.

## Bloqueo

`test_f017_punto_unico.py::test_f017_todos_los_puntos_de_escritura_usan_el_helper` cuenta
`_actor(request)` en `app.py` (espera 15). `patch_parte_fecha` firma con `_actor(request)`
(R1, design §3) ⇒ 16; con T5 (`undo_apply`, R7) serían 17. La spec no lo declara
adaptable ⇒ blocked sin tocar el test. Detalle y opciones A/B/C en `progress/current.md`.

## Fase RED (trazas reales)

**T1 · R12–R17** — `cd services/partes-persistencia && python -m pytest -q
tests/test_f042_despacho.py -k "r12 or r13 or r14 or r15 or r16 or r17"`:

```
ImportError while importing test module '...\services\partes-persistencia\tests\test_f042_despacho.py'.
E   ModuleNotFoundError: No module named 'interface_adapters.workers'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.33s
```

**T2 · R18** — mismo directorio, `python -m pytest -q tests/test_f042_despacho.py -k r18`
(con T1 hecho; el worker viejo trata el recálculo como ingesta, que es justo lo que haría
un sv3 sin desplegar):

```
E           AttributeError: 'State' object has no attribute 'recurso_conciliador'
E           AttributeError: 'State' object has no attribute 'recurso_conciliador'
main_worker.py:68: in handler
    pdf = blob.descargar(CONTENEDOR_INPUT, f"{document_id}.pdf")
E       KeyError: ('input', 'doc-9.pdf')
FAILED tests/test_f042_despacho.py::test_f042_r18_build_app_expone_el_conciliador
FAILED tests/test_f042_despacho.py::test_f042_r18_sin_sigrid_el_conciliador_es_none
FAILED tests/test_f042_despacho.py::test_f042_r18_el_worker_despacha_los_dos_tipos
3 failed, 28 deselected in 2.50s
```

**T3 · R19–R21** — nacen VERDES con T1–T2 (son comportamiento del conciliador de hoy
disparado por el handler). RED demostrada en una **copia aislada** del servicio en el
scratchpad (nunca en el árbol real), con `despacho._recalcular` roto a propósito
(`res = recurso_conciliador.conciliar_todos()` → `res = None`); `python -m pytest -q -p
no:cacheprovider tests/test_f042_domingo_a_jueves.py` en la copia:

```
E       AssertionError: assert [(0, 1, 'extr...se, 0.0, 8.5)] == [(0, 1, 'extr...se, 8.0, 8.5)]
E         At index 0 diff: (0, 1, 'extra', True, 8.5, None) != (0, 1, 'extra', True, 0.5, None)
E         At index 2 diff: (1, 1, 'extra', True, 9.0, None) != (1, 1, 'extra', True, 1.0, None)
E       assert [8.5, 8.5, 9.0] == [0.5, 0.5, 5.0]
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r19_el_recalculo_deja_el_reparto_del_jueves
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r20_las_congeladas_no_cambian_y_cuentan[congelacion0]
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r20_las_congeladas_no_cambian_y_cuentan[congelacion1]
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r20_las_congeladas_no_cambian_y_cuentan[congelacion2]
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r20_las_congeladas_no_cambian_y_cuentan[congelacion3]
FAILED tests/test_f042_domingo_a_jueves.py::test_f042_r21_dos_recalculos_dejan_lo_mismo_que_uno
6 failed, 1 passed in 1.51s
```

(el que pasa es `test_f042_r19_sin_recalculo_el_reparto_del_domingo_se_queda`, la
caracterización del defecto, que no depende del handler).

**T4 · R1–R6, R10** — `cd services/partes-front && python -m pytest -q
tests/test_f042_recalculo_fecha.py -k "r1 or r2 or r3 or r4 or r5 or r6 or r10"`.
Primero sin módulo:

```
E   ModuleNotFoundError: No module named 'infrastructure.persistencia'
ERROR tests/test_f042_recalculo_fecha.py
1 warning, 1 error in 3.92s
```

Con el módulo y el publicador ya cableado en `build_app`, antes de tocar
`patch_parte_fecha`:

```
E       AssertionError: assert {'ok': True, ...nt': 20261001} == {'ok': True, ...lo': 'pedido'}
E         Right contains 1 more item:
E         {'recalculo': 'pedido'}
E       KeyError: 'recalculo'
E       AssertionError: assert [] == ['q-persistencia-pruebas']
E       AssertionError: assert [] == ['q-y']
E       AssertionError: assert ['update_parte_fecha'] == ['update_part...ha', 'enviar']
E         {'recalculo': 'fallo'}
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r1_guardar_la_fecha_pide_el_recalculo
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r10_el_publisher_se_monta_sobre_cola_cliente
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r10_respeta_cola_persistencia
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r10_el_publisher_inyectado_manda
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r2_se_publica_despues_de_confirmar_la_fecha
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r3_si_la_cola_falla_la_fecha_queda_guardada
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r4_sin_cola_guarda_y_lo_dice
FAILED tests/test_f042_recalculo_fecha.py::test_f042_r6_volver_a_guardar_la_misma_fecha_publica
8 failed, 15 passed, 1 warning in 8.83s
```

## Resultado real de los tests (2026-10-09, antes de bloquear)

- sv3 suite completa: **1.147 passed** (incluye 31 de `test_f042_despacho.py` y 7 de
  `test_f042_domingo_a_jueves.py`).
- sv4 `tests/test_f042_recalculo_fecha.py -k "r1 or … or r10"`: **23 passed**.
- sv4 suite completa: **1 failed, 1.855 passed, 1 skipped** en 261,6 s — el único rojo es
  el guardián de F-017 descrito arriba.
- Raíz `tests/`: **461 passed, 3 skipped**.
- `bash harness/init.sh`: no se relanza en rojo conocido; pendiente al desbloquear.

## Evidencias

PENDIENTE de completar al desbloquear (cobertura, mutación con 6 workers, tiempos).

<!-- progress/impl_F-049.md -->
# F-049 · Informe del implementer (PARCIAL: feature `blocked`)

**Estado (2026-10-22)**: T1–T16 hechas, un commit por tarea; T17 (mutación) parada por un test
de recuento de F-017 que queda fuera de la lista cerrada de design §3. Motivo y propuesta en
`progress/current.md` (sección F-049, «BLOQUEO»). T18 (este informe completo) y T19 (portero),
pendientes de la decisión. Rama `feature/F-049-editor-calendario-normal-y-extra`, worktree
`partes-wt-f049`, rebasada sobre `dev` 2bfeab7.

## Qué cambió

| Servicio | Fichero | Qué |
|---|---|---|
| sv4 | `application/services/edicion_celda.py` (nuevo) | núcleo puro: `validar_horas`, `plantilla`, `planificar_celda` (R11–R13, R18, R19, R35) |
| sv4 | `infrastructure/database/parte_repository.py` | `"a": 1` en `regs` (R10); `_celda`, `_afectadas`, `contexto_celda`, `otras_de_celda`, `guardar_celda`, `_crear_en_celda`, `marcar/anular_recalculo_pedido_compartido`; `_record_undo(creadas)`, `_REG_UNDO_MARCAS`, `undo_last(actor=…)`, `_deshacer_creadas`, `_celdas_de`; `MOTIVO_REPARTO_APLICANDO` |
| sv4 | `interface_adapters/web/app.py` | `CeldaPayload`, `_pedir_recalculo_compartido`, `POST /api/matriz/celda`, `GET /api/matriz/celda/otras`, rama `celda_edit` de `/api/undo` |
| sv4 | `infrastructure/persistencia/recalculo_publisher.py` | `MOTIVO_EDICION_CELDA`, `MOTIVO_DESHACER_CELDA` |
| sv4 | `static/app.js`, `static/styles.css` | IIFE «Matriz de obra» reescrito: `camposCelda`, `cuerpoCelda`, `textoOtras`, `avisoAfectadas`, `mostrarAfectadas`, `abrirPopupCelda`; una POST, sin `Promise.all` |
| sv4 | `templates/obra_detail.html` | leyenda (R9), `data-obra-key` y `data-wk` (R31) |
| sv3 | `infrastructure/database/recalculo_seguimiento.py` | `marcar_terminado` filtra solo por pedido y devuelve `rowcount >= 1` (R41–R42) |
| tests | lista cerrada | dobles `undo_last(self, **_kw)` de F-042/F-043; `test_f043_r28_…` invertido y renombrado |
| docs | `docs/ARCHITECTURE.md`; `azure-apps/partes.md` (commit local `08b5755`) | semánticas 3 y 10, rutas, motivos, pedido compartido, orden sv3 → sv4 |

Tests nuevos: `services/partes-front/tests/test_f049_plan_celda.py` (82),
`test_f049_guardar_celda.py` (95), `test_f049_editor_js.py` (32), `tests/test_f049_contrato_motivos.py`
(5), sv3 `test_f049_e12_otra_obra.py` (9) y `test_f049_pedido_compartido.py` (8).

Decisiones y desviaciones (justificadas): ver `progress/current.md`, sección F-049.

## Fase RED (salida real, comando exacto)

- T2 · `python -m pytest tests/test_f049_plan_celda.py -q` (sv4):
  `E   ModuleNotFoundError: No module named 'application.services.edicion_celda'` · `1 error in 1.01s`
- T4 · `python -m pytest tests/test_f049_guardar_celda.py -q`:
  `E       AssertionError: assert {'id': 2, 't'....0, 'p': None} == {'id': 2, 't'...p': None, ...}` · `1 failed in 6.88s`
- T5 · `python -m pytest tests/test_f049_contrato_motivos.py -q` (raíz):
  `E       AttributeError: module 'f049_contrato_sv4_recalculo_publisher' has no attribute 'MOTIVO_EDICION_CELDA'` · `5 failed in 0.66s`
- T6 · `python -m pytest tests/test_f049_guardar_celda.py -q`:
  `E   ImportError: cannot import name 'MOTIVO_REPARTO_APLICANDO' from 'infrastructure.database.parte_repository'`;
  con solo esa constante añadida: `73 failed, 1 passed` (p. ej. `test_f049_e2_r20_r21_…`:
  `E       AssertionError: {"detail":"Not Found"}` / `assert 404 == 200`).
- T9 · `python -m pytest tests/test_f049_guardar_celda.py -q -k "r25 or r26 or r27 or r28"`:
  `9 failed, 4 passed` (`test_f049_r26_deshacer_restaura_horas_y_marcas`, `…_creadas_a_la_papelera`,
  `…_r27_deshacer_sin_cola`, `…_r28_undo_last_sin_actor_sigue_valiendo`, …).
- T10 · `python -m pytest tests/test_f049_editor_js.py -q`:
  `E       AssertionError: app.js no define camposCelda` · `31 failed, 1 passed in 1.74s`
- T12 · `python -m pytest tests/test_f049_guardar_celda.py -q -k "r9 or r31"`:
  `E       At index 0 diff: '<table class="matrix filterable">' != '<table class="matrix filterable" data-obra-key="obr-678">'`
- T14 · `python -m pytest tests/test_f049_pedido_compartido.py tests/test_f043_seguimiento_sv3.py -q` (sv3):
  `3 failed, 38 passed` (solo los de R41: `…_marca_y_y_x`, `…_ya_no_lo_lleva`,
  `test_f043_r28_adaptador_marca_todo_documento_con_su_pedido`).

T13 (caracterización de sv3, R40) pasa a la primera a propósito: no toca código de sv3.

## Verificaciones hechas (resultado real)

- sv4 completo sin `-x` (tras `4889e1e`): `1 failed, 2580 passed, 1 skipped in 281.62s` — el
  único fallo es el del bloqueo (`test_f017_…usan_el_helper`, `assert 18 == 17`).
- sv3 completo: `2271 passed in 20.94s`. Raíz: contratos F-042/F-043/F-046/F-049 en verde.
- `node --check services/partes-front/static/app.js`: OK; plantilla parseada con Jinja2.
- Cobertura de las líneas cambiadas con los tests de F-049: 100 % en `edicion_celda.py`;
  las dos líneas sin cubrir de repositorio y `app.py` tienen test desde `b4f61d2`.

## Evidencias (parciales)

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv4 2581 (1 en rojo, el del bloqueo), sv3 2271, raíz de contratos 24 |
| Cobertura líneas cambiadas | PENDIENTE del portero (T19) |
| Mutantes | 167 en alcance; campaña abortada en la línea base (exit 3), PENDIENTE |
| Tiempo de la suite sv4 | 281,6 s |

## Pendiente

Decisión del humano sobre el test de F-017 (`progress/current.md`); después T17 (campaña
completa, análisis de supervivientes en `progress/mutacion_F-049.md`), T18 (este informe
completo) y T19 (`bash harness/init.sh`). MANUAL M2–M8 y despliegue sv3 → sv4: en
`progress/current.md`.

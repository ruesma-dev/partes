<!-- progress/impl_F-049.md -->
# F-049 · Informe del implementer

**Estado (2026-10-23)**: T1–T19 hechas, un commit por tarea; lista para el reviewer. El
bloqueo de T17 (recuento de `_actor` del guardián de F-017) se resolvió por decisión del humano
(opción A, literal «a»): recuento 17 → 18 y test añadido a la lista cerrada de design §3. La
campaña de mutación completa (la lanzó el líder) dejó 2 supervivientes; los dos eran huecos
reales y los mata un test nuevo cada uno (T17, `3a2d296`). Rama
`feature/F-049-editor-calendario-normal-y-extra`, worktree `partes-wt-f049`, rebasada sobre
`dev` 2bfeab7.

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
| tests | lista cerrada | dobles `undo_last(self, **_kw)` de F-042/F-043; `test_f043_r28_…` invertido y renombrado; `test_f017_…usan_el_helper` a 18 (decisión del humano 2026-10-22) |
| docs | `docs/ARCHITECTURE.md`; `azure-apps/partes.md` (commit local `08b5755`) | semánticas 3 y 10, rutas, motivos, pedido compartido, orden sv3 → sv4 |

Tests nuevos: `services/partes-front/tests/test_f049_plan_celda.py` (82),
`test_f049_guardar_celda.py` (97, dos de ellos de T17), `test_f049_editor_js.py` (32), `tests/test_f049_contrato_motivos.py`
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

## T17 · campaña de mutación completa (resultado real)

Comando (lo lanzó el líder): `python -m harness.mutacion --feature F-049 --workers 1` (sin
`--timeout`), sobre HEAD `4f73add`. Detalle por superviviente en `progress/mutacion_F-049.md`.

| Métrica | Valor |
|---|---|
| Alcance | 775 líneas en 5 ficheros (`edicion_celda.py`, `parte_repository.py`, `app.py`, `recalculo_publisher.py` de sv4; `recalculo_seguimiento.py` de sv3) |
| Mutantes generados / evaluados | 164 / 164 (muestreo: no) |
| Muertos / supervivientes / timeouts | 162 / 2 / 0 |
| Tiempo total | 44.292,9 s (base sv4 413,9 s, sv3 37,0 s; timeout por mutante 828 s) |

Supervivientes (los dos, hueco real; test nuevo en `test_f049_guardar_celda.py`):

1. `parte_repository.py:3229` `if reg is not None:` → `if reg is None:` (`_deshacer_creadas`).
   Las afectadas de un deshacer salen también de las líneas del snapshot; todos los tests con
   afectadas no vacías creaban línea y las `creadas` bastaban para hallar la celda. Test:
   `test_f049_r26_r38_deshacer_sin_creadas_da_las_afectadas` (E12 que solo edita). Mutante a
   mano: `E       AssertionError: assert [] == [{'obra_key':...lada': False}]` · `1 failed`.
2. `app.py:2245` `if sigrid_client is None or not reside:` → `... and not reside:`
   (`_hora_extra_celda`). Faltaba la celda con plantilla y sin recurso (clave `emp-`): el
   mutante consulta `fetch_hora_extra_recurso(None)` y la extra nueva sale con un código que no
   es del recurso. Test: `test_f049_r21_extra_nueva_sin_recurso_no_pregunta_a_sigrid`. Mutante
   a mano: `E       AssertionError: assert ('extra', 1.5, 31, 'HE01') == ('extra', 1.5, None, None)`
   · `1 failed`.

Cada mutante se aplicó con `sed` sobre la línea, se lanzó
`python -m pytest tests/test_f049_guardar_celda.py -q -k <test>` (sv4) y se revirtió con
`git checkout --` (diff vacío comprobado); sin mutar, el fichero entero da `97 passed`. No se
relanzó la campaña completa. **0 supervivientes sin resolver.**

## Verificaciones hechas (resultado real)

- **T19** · `bash harness/init.sh` tras `3a2d296` (2026-10-23): `ENTORNO LISTO. Puedes trabajar.`,
  exit 0. Raíz `498 passed, 3 skipped in 48.68s`; sv4 `2583 passed, 1 skipped, 1 warning in
  243.32s`; sv1, sv2, sv3 y sv5 en verde por caché (árbol sin cambios desde su último verde; la
  última pasada real de sv3 dio `2271 passed in 76.73s`); `PUERTA COBERTURA: 100.0% de 362
  líneas cambiadas cubiertas (362/362, umbral 80%, nivel critico)`; `PUERTA TAMAÑO` dentro
  (requirements 149/150, design 250/250, impl dentro de 220); ruff 771 avisos de deuda previa,
  no bloquea. Log completo fuera del repo, en el scratchpad de la sesión (`init_f049_t19.log`).
- Antes (tras `8d383e8`, 2026-10-22): `ENTORNO LISTO`, sv4 `2581 passed, 1 skipped`.
- T17 · cada superviviente: mutante aplicado a mano → su test nuevo falla; revertido → pasa
  (trazas arriba).
- `node --check services/partes-front/static/app.js`: OK; plantilla parseada con Jinja2.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv4 2583 + 1 skipped, raíz 498 + 3 skipped (pasada real de T19); sv3 2271 (última pasada real, caché en T19); sv1, sv2, sv5 por caché: todo en verde |
| Cobertura líneas cambiadas | 100,0 % (362/362, PUERTA COBERTURA de `init.sh`, 2026-10-23) |
| Mutantes | 164 generados, 162 muertos, 2 supervivientes (los dos huecos reales, muertos ahora por tests nuevos), 0 timeouts; `progress/mutacion_F-049.md` |
| Tiempo de la suite | sv4 243,3 s y raíz 48,7 s con cobertura (`init.sh`, T19); línea base de la campaña: sv4 413,9 s, sv3 37,0 s |

## Fuera del alcance

Lo congelado no se edita en el editor (como hoy); sv5, Sigrid y el esquema de `partes` no se
tocan; las rutas `PATCH` y `/extra` del servidor siguen igual (R29). Desviaciones justificadas en
`progress/current.md`, sección F-049.

## MANUAL pendiente (humano; design §10) y despliegue

Con F-049 fusionada en `dev`, el humano despliega **sv3 antes que sv4**
(`.edeploy_partes.ps1 -Solo sv3`, comprobar su revisión nueva ACTIVA, y luego `-Solo sv4`) y
recorre **M2–M8** en el portal (M1 superada el 2026-10-20). Pasos y consultas de solo lectura,
en `progress/current.md` («F-049 · verificaciones MANUAL»). NO ejecutadas.

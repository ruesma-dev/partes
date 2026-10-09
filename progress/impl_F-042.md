<!-- progress/impl_F-042.md -->
# F-042 · Informe del implementer

Rama `feature/F-042-recalcular-extras-al-cambiar-fecha`, worktree `partes-wt-f042`. Rigor
**crítico**. T1–T13 hechas. Estuvo **blocked en T4** (guardián de F-017) y la desbloqueó el
humano con la **opción A** (2026-10-09): `design.md` §6 enmendado (ver «Desviaciones»).

## Qué cambió

**sv3** (`services/partes-persistencia/`)
- `interface_adapters/workers/mensajes.py` (nuevo, solo stdlib): `TIPO_RECALCULAR`,
  `CLASE_INGESTA`, `CLASE_RECALCULO`, `MensajeDesconocido(ValueError)`, `clasificar`.
- `interface_adapters/workers/despacho.py` (nuevo): `construir_handler`; ingesta = cuerpo
  movido sin cambios desde `main_worker.py`; recálculo = `conciliar_todos()` sin try/except;
  sin conciliador = WARNING y consumido; desconocido = ERROR y se relanza.
- `main_worker.py`: `build_app` una vez y handler de `construir_handler`; docstring con los
  dos tipos. `interface_adapters/api/app.py`: `app.state.recurso_conciliador`.

**sv4** (`services/partes-front/`)
- `infrastructure/persistencia/recalculo_publisher.py` (nuevo, solo stdlib): constantes,
  `mensaje_recalculo`, `RecalculoPublisher.pedir` (lanza si la cola falla),
  `pedir_recalculo` (nunca lanza: `pedido`/`fallo`/`sin_cola`, WARNING con `document_id` y
  tipo de error) y `peor_estado` (`fallo` > `sin_cola` > `pedido`).
- `config/settings.py`: `cola_persistencia` (`COLA_PERSISTENCIA`, defecto `q-persistencia`).
- `interface_adapters/web/app.py`: `build_app(..., recalculo_publisher=None)` (sin inyección,
  sobre `cola_cliente`); `patch_parte_fecha` pide el recálculo tras `update_parte_fecha` y
  devuelve `recalculo`; `undo_apply` lo pide solo si se deshizo una `parte_fecha`.
- `infrastructure/database/parte_repository.py::undo_last`: añade `action` y `document_ids`.
- `static/app.js`: `estadoRecalculo` (textos de R11); `wireFechaInput` lo pinta (`fallo`
  persistente con `error`); deshacer con `recalculo: "fallo"` hace `alert` antes de recargar.

**Raíz y documentación**: `tests/test_f042_contrato_recalculo.py` (R22);
`docs/ARCHITECTURE.md` (comunicación y semántica 3); `docs/referencia/partes-proyecto.md`
(diagrama, comunicación y «Cómputo de extras»); `azure-apps/partes.md` (commit local
`be02869` en `azure-apps`, solo ese fichero).

**Tests nuevos**: sv3 `tests/test_f042_despacho.py` (31), `tests/test_f042_domingo_a_jueves.py`
(7); sv4 `tests/test_f042_recalculo_fecha.py` (46, R11 ejecutando `app.js` con node); raíz
`tests/test_f042_contrato_recalculo.py` (11).

## Desviaciones y decisiones

- **Enmienda del humano (opción A)**: `test_f017_punto_unico.py::test_f017_todos_los_puntos_
  de_escritura_usan_el_helper` pasa de 15 a **17** `_actor(request)` y su docstring nombra
  los dos puntos de F-042. Único test existente tocado (T8: el diff de `test_f0[0-3]*`
  contra `dev` es solo ese fichero). Anotado en `design.md` §6 y `progress/current.md`.
- `peor_estado` vive en el módulo del publisher (regla del §3 para `undo_apply`).
- `undo_apply` con una entrada `parte_fecha` sin documentos no añade `recalculo`.
- `clasificar`: `""`, `False` o `"RECALCULAR"` son desconocidos (solo `None`/ausente = ingesta).
- RED de T3 y T7 en **copias aisladas** del scratchpad (nacen verdes por construcción).

## Fase RED (trazas reales)

**T1 · R12–R17** (`cd services/partes-persistencia && python -m pytest -q
tests/test_f042_despacho.py -k "r12 or r13 or r14 or r15 or r16 or r17"`):
```
E   ModuleNotFoundError: No module named 'interface_adapters.workers'
1 error in 0.33s
```
**T2 · R18** (`... -k r18`, con T1 hecho; el worker viejo trata el recálculo como ingesta):
```
E           AttributeError: 'State' object has no attribute 'recurso_conciliador'
main_worker.py:68: in handler
    pdf = blob.descargar(CONTENEDOR_INPUT, f"{document_id}.pdf")
E       KeyError: ('input', 'doc-9.pdf')
3 failed, 28 deselected in 2.50s
```
**T3 · R19–R21** — copia aislada con `despacho._recalcular` roto (`res = None` en vez de
`conciliar_todos()`), `python -m pytest -q -p no:cacheprovider tests/test_f042_domingo_a_jueves.py`:
```
E         At index 0 diff: (0, 1, 'extra', True, 8.5, None) != (0, 1, 'extra', True, 0.5, None)
E         At index 2 diff: (1, 1, 'extra', True, 9.0, None) != (1, 1, 'extra', True, 1.0, None)
E       assert [8.5, 8.5, 9.0] == [0.5, 0.5, 5.0]
6 failed, 1 passed in 1.51s
```
(pasa la caracterización `test_f042_r19_sin_recalculo_el_reparto_del_domingo_se_queda`).

**T4 · R1–R6, R10** (`cd services/partes-front && python -m pytest -q
tests/test_f042_recalculo_fecha.py -k "r1 or r2 or r3 or r4 or r5 or r6 or r10"`), sin módulo:
`E   ModuleNotFoundError: No module named 'infrastructure.persistencia'`. Con el publicador
cableado y `patch_parte_fecha` aún sin tocar:
```
E         {'recalculo': 'pedido'}
E       KeyError: 'recalculo'
E       AssertionError: assert [] == ['q-persistencia-pruebas']
E       AssertionError: assert [] == ['q-y']
E       AssertionError: assert ['update_parte_fecha'] == ['update_part...ha', 'enviar']
E         {'recalculo': 'fallo'}
8 failed, 15 passed, 1 warning in 8.83s
```
**T5 · R7–R9** (`... -k "r7 or r8 or r9"`):
```
E       KeyError: 'action'
E       KeyError: 'action'
E       KeyError: 'recalculo'   (x4)
FAILED ...::test_f042_r9_undo_last_devuelve_la_accion_y_los_documentos
FAILED ...::test_f042_r7_deshacer_la_fecha_pide_el_recalculo
FAILED ...::test_f042_r7_varios_documentos_y_el_peor_estado
6 failed, 13 passed, 23 deselected, 1 warning in 6.12s
```
**T6 · R11** (`... -k r11`), con `estadoRecalculo` ya escrita y sin cablear (JS ejecutado):
```
E         At index 0 diff: '✓ Guardado' != '✓ Guardado · recalculando extras (recarga en 1–2 min)'
E         At index 0 diff: 'reload' != 'alert:Fecha guardada, pero no se pudo pedir el recálculo de extras: vuelve a guardar la fecha'
2 failed, 2 passed, 42 deselected, 1 warning in 4.38s
```
**T7 · R22** — copia aislada con tres roturas (sv4 `TIPO_RECALCULAR = "recalculo"`, sv2 emite
`"tipo": "ingesta"`, `mensajes.py` importa `yaml`):
```
E       AssertionError: assert 'recalculo' == 'recalcular'
E       f042_contrato_sv3_mensajes.MensajeDesconocido: tipo de mensaje desconocido: 'recalculo'
E       AssertionError: assert 'tipo' not in ['document_id', 'filename', 'mime_type', 'tipo', 'context']
E       AssertionError: ...mensajes.py importa fuera de la stdlib: {'yaml'}
9 failed, 2 passed in 0.58s
```

## Resultado real de los tests (2026-10-09)

- sv3: **1.147 passed** (13,7 s). sv4: **1.879 passed, 1 skipped** (304,4 s). Raíz:
  **472 passed, 3 skipped** (63,2 s).
- `node --check services/partes-front/static/app.js`: OK.
- `bash harness/init.sh` (HEAD `13ee0fc`): ENTORNO LISTO, `PUERTA COBERTURA: 100.0% de 105
  líneas cambiadas`, `PUERTA TAMAÑO` dentro (design 250/250). Relanzado al final (T13).

## Fuera de alcance y pendiente

- Fuera (requirements «Fuera de alcance»): recalcular al editar horas/trabajador/obra/
  líneas, bloquear la aprobación (DA4), coalescer (DA2), reencolar `q-persistencia-poison`
  desde el portal y la carrera de pasadas concurrentes de sv3 (§8 R-b).
- **MANUAL (humano)**: M1 (SQL antes de desplegar), despliegue sv3 → sv4, M2 (reguardar
  la fecha, log `[sv3-worker] recalculo` en Log Analytics, SQL de M1) y M3 (peek de
  `q-persistencia-poison`). Comandos exactos en `progress/current.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv3 1.147 passed; sv4 1.879 passed + 1 skipped; raíz 472 passed + 3 skipped; 0 fallos |
| Tests nuevos de F-042 | 95 (31 + 7 sv3, 46 sv4, 11 raíz) |
| Cobertura de líneas cambiadas | **100,0 %** (105/105, umbral 80 %, `PUERTA COBERTURA`) |
| Mutación | **13 generados, 13 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto** (campaña completa) |
| Workers de la mutación | **6** (`--workers 6 --timeout 600`) |
| Tiempo de la campaña | 1.674,7 s; media 128,8 s × 6 = 773 s por mutante ≥ línea base sv4 ~547 s |
| SHA medido | `13ee0fc50d3358852c57baa7be4a34fcbaea80d3` (después solo cambian `progress/` y `tasks.md`) |
| Tiempo de las suites | sv3 13,7 s; sv4 304,4 s; raíz 63,2 s (init.sh: sv4 340,9 s) |

El JS (`static/app.js`) no entra en la mutación (solo Python); R11 lo cubren los tests que
ejecutan `wireFechaInput` y `wireUndo` con node. Informe: `progress/mutacion_F-042.md`.

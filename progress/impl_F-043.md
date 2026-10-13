<!-- progress/impl_F-043.md -->
# F-043 · Informe del implementer

Rama `feature/F-043-fecha-del-parte-confirmar-y-recargar`, worktree `partes-wt-f043`.
Rigor **crítico**. T1–T15 hechas. Estuvo **blocked en T8** (choque con un test de
F-042) y la desbloqueó el humano con la **opción A** (2026-10-13; ver «Desviaciones»).

## Qué cambió

**Esquema** — `orm_models.py` (sv3 y sv4, byte-idénticos): `recalculo_pedido_id`,
`recalculo_pedido_at_utc` (sv4), `recalculo_terminado_id`, `recalculo_terminado_at_utc`
(sv3); nullables, sin índice, fuera de `_DOC_UNDO_FIELDS`.

**sv3** (`services/partes-persistencia/`)
- `infrastructure/database/recalculo_seguimiento.py` (nuevo): `pedido_actual`,
  `marcar_terminado` (UPDATE condicional `WHERE id AND recalculo_pedido_id = :pid`).
- `interface_adapters/workers/despacho.py`: `construir_handler(..., recalculo_seguimiento=None)`;
  lee el pedido antes de `conciliar_todos()` (sin try), marca después; leer/marcar que
  fallan ⇒ WARNING `[sv3-worker]` y mensaje consumido; INFO `recalculo terminado`.
- `interface_adapters/api/app.py` (`app.state.recalculo_seguimiento`) y `main_worker.py`.

**sv4** (`services/partes-front/`)
- `application/services/seguimiento_recalculo.py` (nuevo, puro): estados,
  `ESPERA_MAX_S = 600`, `estado_seguimiento`, `RecalculandoError(CongeladoError)`.
- `parte_repository.py`: `_ahora_utc`, `_exigir_sin_recalculo` (tras las 7 guardas de
  F-004; no en `update_parte_fecha`; deshacer libre), `alcance_parte`,
  `estados_recalculo` (una consulta `IN`), `documentos_en_espera`,
  `marcar_recalculo_pedido`, `anular_recalculo_pedido`.
- `app.py`: closure `_pedir_recalculo_seguido` (marca con commit antes de publicar;
  anula si `fallo`; WARNING `[recalculo]` si marcar/anular lanza), usada por
  `patch_parte_fecha` y `undo_apply` (`_actor(request)` sigue en 17);
  `GET /api/partes/{id}/alcance`, `GET /api/recalculo?ids=` (1–50, 422);
  `recalculando` en el contexto de las tres vistas.
- Plantillas: «Fecha del parte» + `title`/`aria-label` (R1); `data-recalculando` y marca
  en filas; `data-parte-contenido` en dos contenedores del detalle (cabecera `.info-grid`
  y panel «Personal»; el visor del PDF queda fuera para no deshabilitar su botón).
- `static/app.js`: `fmtFechaEs`, `textoConfirmacionFecha`, `wireFechaInput` nuevo
  (guardada = `defaultValue`; confirma con `change` sin foco, `blur` o Enter;
  cancelar/error restauran), `accionPorEstado`, `vistaRestaurable`,
  `textoAvisoRecalculo`, `contenedoresEspera`, `marcarEspera`, `ponerEnEspera`,
  `soltarEspera`, `avisoRecalculo`, `vigilarRecalculo`/`sondearRecalculo`/
  `aplicarEstadoRecalculo`, `actualizarVista`, `restaurarVista`, `esperasDeLaPagina`;
  «Seleccionar visibles» salta el parte en espera; `restaurarVista()` y
  `esperasDeLaPagina()` en `DOMContentLoaded`. `static/styles.css`: estilos de la espera.

**Documentación**: `docs/ARCHITECTURE.md` (semánticas 3, 7, 10),
`docs/referencia/partes-proyecto.md` («Cómputo de extras», «El parte en espera», §5.1),
`azure-apps/partes.md` (§4.1 y nota F-043; commit local `61d1688`, solo ese fichero).

**Tests nuevos (237)**: sv4 `test_f043_alcance_y_seguimiento.py` (83),
`test_f043_guarda_espera.py` (48), `test_f043_portal_fecha.py` (58, JS con node sobre un
DOM mínimo); sv3 `test_f043_seguimiento_sv3.py` (33); raíz
`tests/test_f043_contrato_seguimiento.py` (15).

## Desviaciones y decisiones

- **Opción A del humano (2026-10-13)**: `test_f042_recalculo_fecha.py::test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo`
  adaptado: su doble de DOM gana `window.confirm` (acepta), respuesta del alcance,
  `activeElement`, las funciones y variables nuevas en la lista extraída; cambian el orden
  de peticiones (alcance, PATCH) y los temporizadores (`timer:5000` del sondeo con
  `pedido`). **Textos de `estadoRecalculo` intactos.** design §6/§7 y `acceptance`
  enmendados (commit `3d97454`). Único test existente tocado (T10).
- **T3 · `getattr(app.state, "recalculo_seguimiento", None)`** en `main_worker.py`: el test
  existente `test_f042_despacho.py::test_f042_r18_...` simula `app.state` sin ese atributo;
  sin él, F-042 intacto (R31). **Validado por el coordinador.**
- `marcar_recalculo_pedido(..., ahora_utc=None)`: por defecto usa `_ahora_utc()` del
  repositorio, el mismo reloj con el que se decide el estado.
- `delete_document` (formulario) en espera: redirección con el motivo, por su
  `except CongeladoError` de F-004 R7 (design §3); los JSON dan el 409 exacto de R38.
- Huecos que la spec no fija, resueltos así: `vencido` deja las filas deshabilitadas con
  marca «sin confirmar · pulsa Actualizar» y tarjeta con «Actualizar» (datos viejos);
  `no_existe` quita la tarjeta; hora sin zona = UTC; ilegible = `vencido`.
- `avisoRecalculo` no hace nada sin `document.body` (dobles de DOM sin cuerpo).

## Fase RED (trazas reales; versión larga de T1–T7 en el commit `7c9eecf`)

**T1 · R34** (raíz `pytest -q tests/test_f043_contrato_seguimiento.py`):
```
E   AssertionError: recalculo_pedido_id
E   assert 'ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS recalculo_pedido_id VARCHAR(36)' in (...)
10 failed, 2 passed in 1.75s
```
**T2 · R27/R28/R32** (sv3 `-k adaptador`): `ModuleNotFoundError: No module named
'infrastructure.database.recalculo_seguimiento'` — 1 error in 2.98s.
**T3 · R27–R33** (sv3 `pytest -q tests/test_f043_seguimiento_sv3.py`):
```
  15 E  TypeError: construir_handler() got an unexpected keyword argument 'recalculo_seguimiento'
   1 E  AttributeError: 'State' object has no attribute 'recalculo_seguimiento'
   1 E  AssertionError: assert 'recalculo_seguimiento' in {'blob': 'blob', 'pipeline': ...}
18 failed, 11 passed in 8.03s
```
**T4 · estado, R2–R4, R17** (sv4): sin módulo, `ImportError: cannot import name
'seguimiento_recalculo'`; con el módulo puro y sin repositorio/endpoints:
```
  10 E   +  where 404 = <Response [404 Not Found]>.status_code
   5 E  AttributeError: 'ParteReviewRepository' object has no attribute 'alcance_parte'
   4 E  assert 404 == 422
   3 E  AttributeError: ... no attribute 'estados_recalculo'
20 failed, 33 passed, 1 warning in 9.07s
```
**T5 · R12–R16**:
```
E  TypeError: expected string or bytes-like object, got 'NoneType'   (x3: no hay pedido)
E  AttributeError: ... no attribute 'marcar_recalculo_pedido'        (x2)
E  assert (1 == 1 and None is not None)    (la cola no ve la marca al publicar)
E  AssertionError: assert 1 == 2            (solo el WARNING de F-042)
11 failed, 60 passed, 1 warning in 15.30s
```
**T6 · R38–R39** (`pytest -q tests/test_f043_guarda_espera.py`):
```
   7 E  assert 200 == 409
   7 E  Failed: DID NOT RAISE RecalculandoError
   1 E  assert 'El parte se está recalculando (extras): espera a que termine.' in '/partes?message=Parte movido a la papelera'
16 failed, 32 passed, 1 warning in 14.44s
```
**T7 · R1, R37**:
```
E  assert '<th title="Es la fecha del PARTE: ...">Fecha del parte</th>' in '{% extends "base.html" %}...'  (x2)
E  assert 'data-recalculando="1"' in '<tr data-registro-id="1" data-document-id="doc-f004" ...'      (x2)
E  assert 0 == 2   (no hay [data-parte-contenido])                                                 (x2)
10 failed, 38 passed, 38 deselected, 1 warning in 8.19s
```
**T8 · R5–R11** — contra una copia con `fmtFechaEs`/`textoConfirmacionFecha` nuevas y el
`wireFechaInput` de F-042 (sin ellas: `app.js no define fmtFechaEs`, 16 failed):
```
E  At index 0 diff: ['/api/partes/doc-1/fecha', 'PATCH'] != ['/api/partes/doc-1/alcance', 'GET']  (x4)
E  AssertionError: assert 'antes:1' == 'antes:0'      (x2: guarda con el foco puesto)
E  At index 0 diff: '2026-10-01' != '2026-10-11'      (cancelar/error no restauran)
E  RangeError: Maximum call stack size exceeded       (R11: el change en vuelo reentra)
13 failed, 3 passed, 8 deselected in 2.58s
```
**T9 · R18–R26, R40** (`pytest -q tests/test_f043_portal_fecha.py`):
```
  27 E  assert []
  25 E  AssertionError: ('RECALCULO_', 'VISTA_', 'recalculo')   (no hay constantes ni sondeo)
   1 E  assert 22 == (22 + 1)                                   (falta actualizarVista)
   1 E  assert 'restaurarVista();' in '  document.addEventListener("DOMContentLoaded", ...'
   1 E  assert 'getAttribute("data-recalculando") !== "1"' in 'querySelector("[data-sel-visibles]") ...'
32 failed, 26 passed in 3.24s
```

## Resultado real de los tests (2026-10-13, `bash harness/init.sh`, HEAD `4cbb059`)

- Raíz **487 passed, 3 skipped** (58,5 s); sv3 **1.180 passed** (18,2 s); sv4
  **2.068 passed, 1 skipped** (391,7 s); sv1, sv2, sv5 en verde (caché).
- `node --check services/partes-front/static/app.js`: OK.
- `PUERTA COBERTURA: 99.4% de 161 líneas cambiadas` (160/161); `PUERTA TAMAÑO`
  dentro; **ENTORNO LISTO**. Relanzado tras este informe (T15): mismo resultado.

## Fuera de alcance y pendiente

- Fuera (requirements): mover una línea o trabajador (F-044, design §10); bloquear la
  aprobación del parte en espera (DA12); proteger de la pasada las ediciones de otros
  partes (R-g, previo); refrescar filas sin recargar (DA10-B); cambiar el recálculo de sv3.
- **MANUAL (humano)**: despliegue sv3 → sv4 y M1–M4 (comandos en `progress/current.md`).
- Pendiente: revisión del reviewer.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | raíz 487 + 3 skipped; sv3 1.180; sv4 2.068 + 1 skipped; 0 fallos |
| Tests nuevos de F-043 | 237 (83 + 48 + 58 sv4, 33 sv3, 15 raíz) |
| Cobertura de líneas cambiadas | **99,4 %** (160/161, umbral 80 %, `PUERTA COBERTURA`) |
| Mutación | **60 generados, 50 muertos, 10 supervivientes, 0 timeouts** (campaña completa, 6 workers, `--timeout 600`, SHA `d8d51a5`) |
| Supervivientes resueltos | **10/10 huecos reales**, cazados por 5 tests nuevos (DDL por servicio ×8, esquema OpenAPI ×2), verificado a mano mutante a mutante ⇒ **0 sin resolver** |
| Tiempo de la campaña | 4.014,8 s; media 66,9 s por mutante; línea base sv4 ~446 s, sv3 ~24 s |
| Tiempo de las suites | raíz 58,5 s; sv3 18,2 s; sv4 391,7 s |

Informe de mutación: `progress/mutacion_F-043.md`. El JS y las plantillas no entran en el
mutador (solo Python): los cubre `test_f043_portal_fecha.py` ejecutando `app.js` con node.

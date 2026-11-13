<!-- specs/F-068-conciliar-pide-recalculo/tasks.md -->
# F-068 · Tareas

Rama `feature/F-068-conciliar-pide-recalculo` (desde `dev` 7e5f600), worktree `partes-wt-f068`.
Rigor crítico: fase RED por tarea de código, cobertura y campaña de mutación sobre lo tocado.
Un commit por tarea (`F-068 Tn: …`). Las tareas marcadas (D3-b) / (D4-b) solo si el humano elige
esa opción; si no, se marcan «no aplica» en el informe.

- [x] T1: Tests RED de las constantes de motivo y del contrato raíz ampliado (R20) en `test_f068_conciliar_recalculo.py` y `tests/test_f042_contrato_recalculo.py`  |  Verificación: `python -m pytest tests/test_f042_contrato_recalculo.py` falla por AttributeError (traza RED)
- [x] T2: Añadir los tres motivos a `recalculo_publisher.py` (design §6)  |  Verificación: T1 en verde
- [x] T3: Tests RED del repositorio: `_documentos_de` (orden por id, sin repetir, sin None), colector de `backfill_empleado` (R4, E1–E4) y retorno intacto (R22) en `test_f068_repositorio.py`  |  Verificación: `pytest services/partes-front/tests/test_f068_repositorio.py` falla
- [x] T4: `_documentos_de` y el parámetro `documentos` en `backfill_empleado` (design §4)  |  Verificación: T3 en verde; `test_f004_endpoints_congelados.py`, `test_f023_catalogo_empresa.py`, `test_f030_portal_recurso.py`, `test_f035_repositorio.py` en verde
- [x] T5: Tests RED de la ruta de Conciliar: R1–R3, R5–R8, R10 y E1–E6 con `ColaFake` y repositorio SQLite (patrón de `test_f042_recalculo_fecha.py`)  |  Verificación: `pytest services/partes-front/tests/test_f068_conciliar_recalculo.py -k conciliar` falla
- [x] T6: `_recalculo_de_trabajador` y su uso en `conciliacion_confirmar` tras el alias (design §5)  |  Verificación: T5 en verde; `test_f035_endpoints.py`, `test_f040_alias.py` en verde
- [x] T7: Tests de caracterización R9 (parte del casado en espera: edición 409 `RecalculandoError`) y R11–R13/E7 (aprobar con un id borrado tras el casado ⇒ 422 `inexistentes`, casado y pedido intactos, nada escrito)  |  Verificación: `pytest … -k "r9 or r12 or r13"` en verde (caracterizan; anotar en el informe que pasan sin código nuevo)
- [x] T8: Tests RED de JS con `node`: `textoRecalculoCasado` para `pedido`, `fallo`, `sin_cola`, `null` (R14–R16) en `test_f068_conciliar_js.py`  |  Verificación: falla antes de T9
- [x] T9: `textoRecalculoCasado` y su uso en `_confirmarCasado` (design §7)  |  Verificación: T8 en verde y `node --check services/partes-front/static/app.js`
- [x] T10 (D3-b): Tests RED y colector en `reassign_empleado_by_leido` / `_by_worker_key` / `_by_registro_ids`, ruta `empleado_reasignar` con `MOTIVO_REASIGNACION` y `alert` de `fallo` antes de recargar (R17, R18)  |  Verificación: tests `-k r17 or r18` en verde; `test_f035_*` y `test_f004_endpoints_congelados.py` en verde; `node --check`
- [x] T11 (D4-b): Tests RED y rama `empleado` en `undo_last` (partes de las líneas aplicadas, no las omitidas) y en `undo_apply` con `MOTIVO_DESHACER_TRABAJADOR` (R19)  |  Verificación: tests `-k r19` en verde; `test_f042_recalculo_fecha.py`, `test_f043_alcance_y_seguimiento.py`, `test_f049_guardar_celda.py` en verde
- [x] T12: Guardianes sin cambios (R21): gemelos y suite completa de sv4  |  Verificación: `python -m pytest tests/test_f010_orm_models_gemelos.py tests/test_f024_borrado_no_congela_gemelos.py tests/test_f023_de_alta_gemelos.py tests/test_f036_recurso_persona_gemelos.py tests/test_f015_r19_jornada_resolver_gemelo.py` y `python -m pytest services/partes-front/tests` en verde; `git diff dev --stat` sin sv3/sv5/orm_models/congelacion
- [x] T13: `docs/ARCHITECTURE.md` (semántica 3: Conciliar, reasignar y deshacer `empleado` piden recálculo; motivos) y `azure-apps/partes.md` en su repo (`git -C … pull` antes, commit local allí, sin push)  |  Verificación: `grep -n "F-068" docs/ARCHITECTURE.md` y `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1 --stat`
- [ ] T14: Cobertura y campaña de mutación de rigor crítico sobre `_documentos_de`, el colector, `_recalculo_de_trabajador` y las ramas nuevas; cada superviviente con test o justificación (`progress/mutacion_F-068.md`)  |  Verificación: informe sin `PENDIENTE`
- [ ] T15: M1 tras desplegar sv4 (lo pide el humano), solo lectura  |  Verificación: MANUAL (humano): pasos de M1 en `requirements.md`
- [ ] T16: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

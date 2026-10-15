# F-049 · Tareas (una por línea; cada una, un commit `F-049 Tn: ...`)

- [ ] T1: Fusionar `dev` (con F-046 y F-047 ya integradas) en la rama y releer §3–§7 del design contra lo fusionado; si algo lo contradice, `blocked` y anotar en `progress/current.md`  |  Verificación: `bash harness/init.sh` en verde tras la fusión, sin tocar código de F-049
- [ ] T2: Tests RED del núcleo `edicion_celda` (E1–E8, errores R11–R13 con su `status`, plantilla R19, materializar solo parejas tocadas R18)  |  Verificación: `pytest services/partes-front/tests/test_f049_plan_celda.py` falla por import (traza RED en el informe)
- [ ] T3: Implementar `application/services/edicion_celda.py` (design §4)  |  Verificación: `test_f049_plan_celda.py` en verde
- [ ] T4: `_reg_de_celda` con `"a": 1` en las `extra_auto` (R10) y test  |  Verificación: test R10 nuevo y `test_f004_vistas_candado.py` sin cambios en verde
- [ ] T5: Motivos `edicion_celda` y `deshacer_edicion_celda` en `recalculo_publisher.py` y test de contrato de la raíz (R30)  |  Verificación: `pytest tests/test_f049_contrato_motivos.py tests/test_f042_contrato_recalculo.py`
- [ ] T6: Tests RED de repositorio y ruta (design §9, R11–R24) con SQLite y publicador falso  |  Verificación: `pytest services/partes-front/tests/test_f049_guardar_celda.py` falla (traza RED)
- [ ] T7: `contexto_celda` y `guardar_celda` en `parte_repository.py` (design §5, R11–R20, R25)  |  Verificación: tests de repositorio de T6 en verde
- [ ] T8: `CeldaPayload` y `POST /api/matriz/celda` en `app.py` con códigos de hora y recálculo seguido (design §6, R21–R24)  |  Verificación: tests de ruta de T6 en verde
- [ ] T9: Deshacer `celda_edit`: `_REG_UNDO_MARCAS`, `_apply_reg_snapshot`, `_record_undo(creadas)`, `undo_last(actor=…)`, rama en `/api/undo` y los dos dobles de la lista cerrada (R25–R28)  |  Verificación: tests R25–R28 y suites F-042/F-043 en verde
- [ ] T10: Tests RED del JS (`camposCelda`, `cuerpoCelda`, popup con DOM falso; R1–R8)  |  Verificación: `pytest services/partes-front/tests/test_f049_editor_js.py` falla (traza RED)
- [ ] T11: Reescribir el popup de la matriz en `static/app.js` sobre las dos funciones puras, nota y rótulos; estilos en `styles.css` (design §7)  |  Verificación: `test_f049_editor_js.py` en verde y `node --check services/partes-front/static/app.js`
- [ ] T12: Leyenda de `obra_detail.html` (R9) y test  |  Verificación: test R9 y parseo Jinja2 de la plantilla
- [ ] T13: `docs/ARCHITECTURE.md` (semánticas 3 y 10) y `azure-apps/partes.md` (motivos y ruta; commit local en `azure-apps`)  |  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1` y diff revisado
- [ ] T14: Campaña de mutación completa (rigor crítico) sobre `edicion_celda.py` y lo cambiado en `parte_repository.py` y `app.py`; tests nuevos o justificación por superviviente  |  Verificación: `progress/mutacion_F-049.md` con 0 supervivientes sin resolver
- [ ] T15: Informe `progress/impl_F-049.md` con trazas RED, cobertura y M1–M6 como MANUAL (humano): M1 antes de implementar; despliegue solo de sv4 (`.\redeploy_partes.ps1 -Solo sv4`, lo lanza el humano); M2–M6 tras desplegar (design §10)  |  Verificación: MANUAL (humano)
- [ ] T16: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

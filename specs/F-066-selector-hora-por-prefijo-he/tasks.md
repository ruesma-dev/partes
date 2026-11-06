# F-066 · Tareas

M1 hecha (líder, 2026-11-06, `design.md` §7). Antes de T1: DA1–DA5 y DA7–DA10 aprobadas.

- [ ] T1: RED+GREEN `application/services/clase_hora.py` (constantes, `es_hora_extra` con `HENC`, `tipo_hora_de_codigo`, `condicion_sql_extra`) y reimport en `sincronizacion.py`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_clase_hora.py services/partes-front/tests/test_f052_clasificar.py -q`
- [ ] T2: RED tests R6–R14 en `test_f066_set_registro_hora.py` (fallan: `HEOF`/`ext=0` queda `normal`)  |  Verificación: pytest del fichero en rojo, traza en `progress/impl_F-066.md`
- [ ] T3: GREEN `parte_repository.set_registro_hora` y respuesta de `PATCH /api/registros/{id}/hora`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_set_registro_hora.py services/partes-front/tests/test_f048_traza_portal.py services/partes-front/tests/test_f043_guarda_espera.py services/partes-front/tests/test_f004_endpoints_congelados.py -q`
- [ ] T4: RED tests R15–R17 y R22 en `test_f066_selector_js.py`  |  Verificación: pytest del fichero en rojo, traza en el informe
- [ ] T5: GREEN campo `extra` en `GET /api/sigrid/tipos-hora` y `buildOptions` agrupando por `t.extra`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_selector_js.py -q` y `node --check services/partes-front/static/app.js`
- [ ] T6: RED tests R18–R20 en `test_f066_usos_sv4.py` (`HENC` elegida como extra, DNI con solo `HENC` con extra, `HENC` sumada)  |  Verificación: pytest del fichero en rojo, traza en el informe
- [ ] T7: GREEN `fetch_hora_extra_recurso`, `fetch_dnis_sin_extra` y `franquicia.extras_pendientes` con `clase_hora`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_usos_sv4.py services/partes-front/tests/test_f056_franquicia.py services/partes-front/tests/test_f023_catalogo_empresa.py services/partes-front/tests/test_f049_guardar_celda.py -q`
- [ ] T8: docs: `docs/ARCHITECTURE.md` semántica 3 y docstrings (`tipo_hora_catalog.py`, `franquicia.py`, `sincronizacion.py`)  |  Verificación: revisión del reviewer (R21)
- [ ] T9: mutación completa de las líneas cambiadas (rigor crítico; la lanza el líder) y tratamiento de supervivientes  |  Verificación: `python -m harness.mutacion` según CHECKPOINTS, 0 supervivientes sin test o justificación aceptada
- [ ] T10: M2 tras desplegar sv4 (humano)  |  Verificación: MANUAL (humano), `requirements.md` §Verificaciones manuales
- [ ] T11: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

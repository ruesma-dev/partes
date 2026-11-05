# F-066 · Tareas

Antes de T2: **M1** hecha y anotada por el líder (`design.md` §7) y DA1–DA9 aprobadas.

- [ ] T1: RED+GREEN `application/services/clase_hora.py` (`es_hora_extra` movida, `tipo_hora_de_codigo`) y reimport en `sincronizacion.py`; `franquicia.extras_pendientes` usa `es_hora_extra`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_clase_hora.py services/partes-front/tests/test_f052_*.py services/partes-front/tests/test_f056_*.py -q`
- [ ] T2: RED tests R4–R12 en `test_f066_set_registro_hora.py` (fallan: `HE01`/`ext=0` queda `normal`)  |  Verificación: pytest del fichero en rojo, traza en `progress/impl_F-066.md`
- [ ] T3: GREEN `parte_repository.set_registro_hora` y respuesta de `PATCH /api/registros/{id}/hora` por `tipo_hora_de_codigo`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_set_registro_hora.py services/partes-front/tests/test_f048_traza_portal.py services/partes-front/tests/test_f043_guarda_espera.py services/partes-front/tests/test_f004_endpoints_congelados.py -q`
- [ ] T4: RED tests R13–R15 y R18 en `test_f066_selector_js.py` (node sobre `buildOptions`, fuente)  |  Verificación: pytest del fichero en rojo, traza en el informe
- [ ] T5: GREEN campo `extra` en `GET /api/sigrid/tipos-hora` y `buildOptions` agrupando por `t.extra`  |  Verificación: `python -m pytest services/partes-front/tests/test_f066_selector_js.py -q` y `node --check services/partes-front/static/app.js`
- [ ] T6: (solo si DA8 = B) guardián raíz `tests/test_f066_prefijo_he_gemelos.py` y entrada en la lista de gemelos de `CLAUDE.md`  |  Verificación: `python -m pytest tests/test_f066_prefijo_he_gemelos.py -q`
- [ ] T7: docs: `docs/ARCHITECTURE.md` semántica 3 y docstring de `tipo_hora_catalog.py`  |  Verificación: revisión del reviewer (R17)
- [ ] T8: mutación completa de las líneas cambiadas (rigor crítico; la lanza el líder) y tratamiento de supervivientes  |  Verificación: `python -m harness.mutacion` según CHECKPOINTS, 0 supervivientes sin test o justificación aceptada
- [ ] T9: M2 tras desplegar sv4 (humano) y M3 según DA6  |  Verificación: MANUAL (humano), `design.md` §7
- [ ] T10: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

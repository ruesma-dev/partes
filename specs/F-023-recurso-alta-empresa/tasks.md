<!-- specs/F-023-recurso-alta-empresa/tasks.md -->
# F-023 · Casado de trabajador y recurso por alta y empresa — Tareas

Rama: **`feature/F-023-recurso-alta-empresa`** (ya creada). Un commit **local**
por tarea, `F-023 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push
ni PR. Rigor **`critico`**: fase RED con traza en `progress/impl_F-023.md` para
**R1, R5, R7, R12, R15, R19, R21, R23, R25, R26, R27, R29 y R35**; cobertura de
líneas cambiadas ≥ umbral; campaña de mutación **completa** con **0
supervivientes** sin test o justificación aceptada por el humano.

Reglas que no se negocian:

- **No empezar sin las decisiones DA1–DA10 aprobadas** (`design.md` §8). Si
  DA6 se rechaza, T15–T16 desaparecen y R29–R30 se reescriben antes de seguir.
- **Ningún test toca red, Sigrid ni PostgreSQL**: dobles del puerto y
  `httpx` simulado. Sin DNIs, nombres ni códigos de obra reales en tests e
  informes (usar valores sintéticos).
- **Ni una escritura en Sigrid** desde local. Los datos ya medidos están en
  `progress/explore_F-023_sigrid.md`; no hace falta volver a consultarlos.
- Cero cambios en `orm_models.py` (sv3 y sv4). Si parece necesario: `blocked`.
- Comando de tests por servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [ ] T1: Inventariar los tests existentes que construyen los clientes con `empresa=`, usan `resides_por_dni`, `fetch_obras` deduplicado por código o `EmpleadoMatcher.match` sin empresa, y anotarlos en `progress/impl_F-023.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [ ] T2: DTOs de sv3 (`sigrid_models.py`: `empresa`/`fecbaj`; `parte_records.py`: `ObraMatch.empresa`) con valores por defecto  |  Verificación: suite completa de sv3 en verde sin tocar tests
- [ ] T3: Tests de `seleccion_sigrid` (R1, R5–R8, R10–R17, R19–R21) en rojo, con traza RED de R1, R5, R7, R12, R19 y R21  |  Verificación: `pytest tests/test_f023_seleccion_sigrid.py` falla por ausencia del módulo
- [ ] T4: Implementar `application/services/seleccion_sigrid.py` (design §5.1)  |  Verificación: `pytest tests/test_f023_seleccion_sigrid.py` en verde
- [ ] T5: Tests del cliente de sv3 (R2, R3) en rojo y cambio de `sigrid_api_client.py` (SQL de design §6, sin `empresa`, `truncated`)  |  Verificación: `pytest tests/test_f023_cliente_sigrid.py` en verde
- [ ] T6: Tests de `_match` y `review_required` (R4–R18) en rojo, con traza RED de R15; cambiar `obra_matcher.py`, `empleado_matcher.py`, `sigrid_matcher_provider.py` y `persist_parte_pipeline.py` (design §5.2)  |  Verificación: `pytest tests/test_f023_pipeline_match.py` y los tests adaptados de T1 en verde
- [ ] T7: Tests del conciliador (R19–R24) en rojo, con traza RED de R23; cambiar `recurso_conciliador.py` (`indice_provider`, congeladas sin update, marca de revisión) y `fetch_registros_para_recurso` (+`recurso_ide`)  |  Verificación: `pytest tests/test_f023_recurso_conciliador.py` y suite completa de sv3 en verde
- [ ] T8: Cableado de sv3 (`app.py` sin `empresa`, con `indice_provider`; `settings.py` sin `sigrid_empresa`, DA5)  |  Verificación: suite completa de sv3 en verde, incluido `test_f003_r10_wiring_sv3.py`
- [ ] T9: Tests de `coherencia_recurso` (R29, R30) en rojo, con traza RED de R29, e implementar `application/services/coherencia_recurso.py` en sv5 (design §5.3)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py -k coherencia` en verde
- [ ] T10: Tests del cliente de sv5 (R3, R25–R28) en rojo, con traza RED de R25, R26 y R27; cambiar `sigrid_write_client.py` (design §4 y §6)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py -k cliente` en verde; las sentencias generadas llevan `emp` en `con` y en el `SELECT` del `INSERT INTO hmo`
- [ ] T11: `registro_pipeline.preparar` y `reglas_registro.py` (verificación y resolución por DNI con motivo concreto) y cableado sin `empresa` (`main.py`, `app.py`, `settings.py`)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py` y suite completa de sv5 en verde
- [ ] T12: Tests del cliente y de los endpoints de sv4 (R3, R31–R33) en rojo y cambio de `sigrid_lookup_client.py` y de `app.py`  |  Verificación: `pytest tests/test_f023_catalogo_empresa.py -k "cliente or endpoint"` en verde
- [ ] T13: Tests de R35 en rojo, con traza RED, y helper `_soltar_recurso` en los cuatro métodos de `parte_repository.py` (solo líneas no congeladas)  |  Verificación: `pytest tests/test_f023_catalogo_empresa.py -k soltar` y suite completa de sv4 en verde
- [ ] T14: `static/app.js`: empresa en las etiquetas de los combos y filtro por empresa de la obra en los dos modales de alta manual (R34)  |  Verificación: `node --check services/partes-front/static/app.js`; comprobación en navegador anotada como MANUAL (humano) en el informe
- [ ] T15: Guardián `tests/test_f023_de_alta_gemelos.py` (tabla común para `de_alta` de sv3 y sv5; el SQL de empleados de sv4 conserva los predicados `con.fecbaj IS NULL OR con.fecbaj = 0 OR con.fecbaj > ?` y su equivalente sobre `rescon`) — solo si DA6 está aprobada  |  Verificación: `.venv/Scripts/python.exe -m pytest -q tests/test_f023_de_alta_gemelos.py` en verde, y en rojo si se altera una copia (anotarlo en el informe)
- [ ] T16: Añadir los dos `de_alta` y la elección de recurso por DNI (sv3 `seleccion_sigrid.py`, sv5 `coherencia_recurso.py`) a la lista cerrada de duplicación de `CLAUDE.md`, con fecha y el guardián de T15 — solo si DA6 está aprobada  |  Verificación: lectura del reviewer; `bash harness/init.sh` en verde
- [ ] T17: `docs/ARCHITECTURE.md` (punto 12 de semántica de dominio: alta, empresa del parte, obras gemelas, verificación de sv5; ≤ 12 líneas) y `docs/referencia/partes-proyecto.md` §4.6 y §6.6 (R36)  |  Verificación: lectura del reviewer contra design §8
- [ ] T18: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: `SIGRID_EMPRESA` inerte en sv3 y sv5, regla de alta y empresa (R36); commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1` muestra el commit
- [ ] T19: Cobertura de líneas cambiadas y campaña de mutación completa sobre los ficheros de sv3, sv4 y sv5 tocados, en `progress/mutacion_F-023.md`, con cada superviviente matado por un test nuevo o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T20: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida del comando en verde; pendientes MANUAL (M1–M4 de design §9 y T14) anotados en `progress/current.md`

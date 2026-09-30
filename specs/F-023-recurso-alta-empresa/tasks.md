<!-- specs/F-023-recurso-alta-empresa/tasks.md -->
# F-023 · Casado de trabajador y recurso por alta y empresa — Tareas

Rama: **`feature/F-023-recurso-alta-empresa`** (ya creada). Un commit **local**
por tarea, `F-023 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push
ni PR. Rigor **`critico`**: fase RED con traza en `progress/impl_F-023.md` para
**R1, R3, R4, R7, R9, R10, R11, R13, R19, R22, R25, R27, R30, R32, R33, R34,
R36 y R42**; cobertura de líneas cambiadas ≥ umbral; campaña de mutación
**completa** con **0 supervivientes** sin test o justificación aceptada.

Reglas que no se negocian:

- **No empezar sin DA1–DA12 aprobadas** (`design.md` §8). Si DA6 se rechaza,
  T19–T20 desaparecen y R36–R37 se reescriben antes de seguir.
- **Ningún test toca red, Sigrid, Gemini ni PostgreSQL**: dobles del puerto y
  `httpx` simulado. Sin DNIs, nombres, códigos de recurso ni de obra reales en
  tests e informes: el caso guía MO/0239 se reproduce con valores sintéticos.
- **Ni una escritura en Sigrid** desde local. Los datos ya medidos están en
  `progress/explore_F-023_sigrid.md`.
- El prompt de sv2 solo gana la viñeta y la clave de `empresa_membrete`
  (DA12): cualquier otro cambio de redacción es **F-007**, no esta feature.
- Único cambio de esquema: las tres columnas de DA11, en las **dos** copias de
  `orm_models.py` a la vez (el guardián `tests/test_f010_orm_models_gemelos.py`
  lo vigila).
- Comando de tests por servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [x] T1: Inventariar los tests existentes que construyen los clientes con `empresa=`, usan `resides_por_dni`, `fetch_obras` deduplicado por código, el orden `ORDER BY` de los listados o `EmpleadoMatcher.match` sin empresa, y anotarlos en `progress/impl_F-023.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [x] T2: Crear `services/partes-api/tests/` (conftest) con los tests de R5 en rojo; añadir `CabeceraParte.empresa_membrete` y la viñeta + clave en `config/prompts.yaml` (design §4)  |  Verificación: `pytest tests/test_f023_empresa_membrete.py` en sv2 en verde y `bash harness/init.sh` ya no avisa de sv2 sin tests
- [x] T3: DTOs y puerto de sv3 (`sigrid_models.py`, `parte_records.py`, `fetch_empresas` en el puerto) con valores por defecto  |  Verificación: suite completa de sv3 en verde sin tocar tests
- [x] T4: Tests de `seleccion_sigrid` (R1, R9–R13, R17–R24, R25–R28; incluye el caso guía sintético) en rojo con trazas RED, e implementar `seleccion_sigrid.py` (design §5.1)  |  Verificación: `pytest tests/test_f023_seleccion_sigrid.py` en verde
- [x] T5: Tests de `empresa_membrete` (R7, R8) en rojo, implementar `empresa_membrete.py` y crear `config/empresas_membrete.yaml` (design §5.2)  |  Verificación: `pytest tests/test_f023_empresa_membrete.py` en sv3 en verde
- [x] T6: Tests del cliente de sv3 (R2, R3, R4) en rojo con trazas RED de R3 y R4: páginas encadenadas, `max_rows` = página + 1, `ORDER BY` por clave de design §6, `truncated` ⇒ excepción; cambiar `sigrid_api_client.py`  |  Verificación: `pytest tests/test_f023_cliente_sigrid.py` en verde
- [x] T7: Columnas de DA11 en `orm_models.py` de sv3 **y** sv4 (byte-idénticos), `parte_normalizer.py` (R6) y persistencia en `sqlalchemy_parte_repository.py`  |  Verificación: `tests/test_f010_orm_models_gemelos.py` en verde; test de que `ddl_complementario()` genera los tres `ADD COLUMN IF NOT EXISTS`
- [ ] T8: Tests de `_match` y `review_required` (R6–R24) en rojo; cambiar `obra_matcher.py`, `empleado_matcher.py`, `sigrid_matcher_provider.py` y `persist_parte_pipeline.py` (design §5.3)  |  Verificación: `pytest tests/test_f023_pipeline_match.py` y los tests adaptados de T1 en verde
- [ ] T9: Tests del conciliador (R25–R31; caso guía: la ficha apunta a un recurso de baja y queda el de alta) en rojo; cambiar `recurso_conciliador.py` y `fetch_registros_para_recurso` (+`recurso_ide`, `parte_empresa`)  |  Verificación: `pytest tests/test_f023_recurso_conciliador.py` y suite completa de sv3 en verde
- [ ] T10: Cableado de sv3 (`app.py` sin `empresa`, con `indice_provider` y ruta del YAML; `settings.py` sin `sigrid_empresa`, DA5)  |  Verificación: suite completa de sv3 en verde, incluido `test_f003_r10_wiring_sv3.py`
- [ ] T11: Tests de `coherencia_recurso` (R36, R37) en rojo e implementar `coherencia_recurso.py` en sv5 (design §5.4)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py -k coherencia` en verde
- [ ] T12: Tests del cliente de sv5 (R4, R32–R35) en rojo con trazas RED de R32, R33 y R34; cambiar `sigrid_write_client.py` (design §4 y §6)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py -k cliente` en verde; las sentencias llevan `emp` en `con` y en el `SELECT` del `INSERT INTO hmo`
- [ ] T13: `registro_pipeline.preparar` y `reglas_registro.py` (verificación y resolución por DNI con motivo concreto) y cableado sin `empresa` (`main.py`, `app.py`, `settings.py`)  |  Verificación: `pytest tests/test_f023_escritura_empresa.py` y suite completa de sv5 en verde
- [ ] T14: Tests del cliente de sv4 (R3, R4, R38, R39) en rojo y cambio de `sigrid_lookup_client.py` (paginación y `truncated` como sv3; empresa; obras por `ide`)  |  Verificación: `pytest tests/test_f023_catalogo_empresa.py -k cliente` en verde
- [ ] T15: Tests de los endpoints (R40) en rojo y cambio de `interface_adapters/web/app.py`  |  Verificación: `pytest tests/test_f023_catalogo_empresa.py -k endpoint` en verde
- [ ] T16: Tests de R42 en rojo, con traza RED, y `_soltar_recurso` en los cuatro métodos de `parte_repository.py` (solo líneas no congeladas)  |  Verificación: `pytest tests/test_f023_catalogo_empresa.py -k soltar` y suite completa de sv4 en verde
- [ ] T17: `static/app.js`: empresa en las etiquetas y filtro por empresa de la obra en los dos modales de alta manual (R41)  |  Verificación: `node --check services/partes-front/static/app.js`; comprobación en navegador como MANUAL (humano) en el informe
- [ ] T18: Comprobar que ninguna lectura de listado de sv3 ni de sv4 queda sin `_leer_paginado` (R3) con un test que recorre los `fetch_*` de las dos copias  |  Verificación: `pytest -k paginado` en sv3 y sv4 en verde, y en rojo si se quita la paginación de un `fetch_*` (anotarlo)
- [ ] T19: Guardián `tests/test_f023_de_alta_gemelos.py` (tabla común para `de_alta` de sv3 y sv5; el SQL de empleados de sv4 conserva `con.fecbaj IS NULL OR con.fecbaj = 0 OR con.fecbaj > ?` y su equivalente sobre `rescon`) — solo si DA6  |  Verificación: `.venv/Scripts/python.exe -m pytest -q tests/test_f023_de_alta_gemelos.py` en verde, y en rojo si se altera una copia (anotarlo)
- [ ] T20: Añadir los `de_alta` y la elección de recurso por DNI de sv3 y sv5 a la lista cerrada de duplicación de `CLAUDE.md`, con fecha y el guardián de T19 — solo si DA6  |  Verificación: lectura del reviewer; `bash harness/init.sh` en verde
- [ ] T21: `docs/ARCHITECTURE.md` (punto 12 y columnas en el punto 7; ≤ 14 líneas) y `docs/referencia/partes-proyecto.md` §4.6, §5.1 y §6.6 (R43)  |  Verificación: lectura del reviewer contra design §8
- [ ] T22: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: empresa del membrete, columnas nuevas, `SIGRID_EMPRESA` inerte en sv3 y sv5, paginación (R43); commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1` muestra el commit
- [ ] T23: Cobertura de líneas cambiadas y campaña de mutación completa sobre los ficheros de sv2, sv3, sv4 y sv5 tocados, en `progress/mutacion_F-023.md`, con cada superviviente matado por un test nuevo o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T24: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; pendientes MANUAL (M1–M5 de design §9 y T17) anotados en `progress/current.md`

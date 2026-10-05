<!-- specs/F-031-asiento-analitico/tasks.md -->
# F-031 · El parte registrado acaba en el asiento analítico — Tareas

Rama: **`feature/F-031-asiento-analitico`** (ya creada). Un commit **local**
por tarea, `F-031 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin
push ni PR. Rigor **`critico`**: fase RED con traza en
`progress/impl_F-031.md` para los R de design §10; cobertura de líneas
cambiadas ≥ umbral; campaña de mutación **completa** con **0
supervivientes** sin test o justificación aceptada.

Reglas que no se negocian:
- Decisiones aprobadas (design §8, DA6 v3). DA6-e sigue abierta con el
  humano: R18 se implementa **provisional** y aislado en `origen_subcuenta`;
  si responde antes de T6, se para y se ajusta la spec.
- Ninguna escritura en Sigrid ni en la base `partes`; los tests usan
  `SigridFake` y `httpx` simulado.
- Ningún test ajeno se modifica (tampoco los `test_f021_*`, R25);
  `dobles.py` solo crece. Si un test ajeno se pone rojo, se para.

- [ ] T1: Caracterización en verde contra el código de hoy en `tests/test_f031_pipeline_estado.py` y `tests/test_f031_pipeline_cuenta_partida.py`: R6, R11, R20 (Porsan sin cuenta ni nota), R30, R31, y suite `test_f021_*` en verde (R25)  |  Verificación: `pytest services/partes-transfer/tests/test_f031_pipeline_estado.py services/partes-transfer/tests/test_f031_pipeline_cuenta_partida.py` en verde
- [ ] T2: `dobles.py`: `SigridFake(partidas=...)`, `partes_del_periodo` (`est`, defecto 1), `partidas_de_lineas` + `partidas_leidas`, `partes_existentes` con el de mayor `ide`; `SettingsFake` con `est_parte_imputado=10`, `est_parte_cerrado=3`  |  Verificación: suite completa de sv5 en verde sin tocar otros tests
- [ ] T3: Tests de la regla pura `tests/test_f031_estado_parte.py` (R2, R3 todo Imputado sin parte nuevo, R5, R6, textos de aviso y de los dos motivos con prefijo `parte_contabilizado: `) — en rojo  |  Verificación: traza RED en `progress/impl_F-031.md`
- [ ] T4: `registro_models.py` (`ParteSigrid`, `PartidaCuenta`, campos de `ParteDestino` y `AccionLinea`) y `application/services/estado_parte.py` (design §7.1)  |  Verificación: T3 en verde
- [ ] T5: Tests puros `tests/test_f031_cuenta_partida.py` de `origen_subcuenta`: R17 (cuenta de coste de la partida manda aunque el recurso tenga otra subcuenta), R18 (sin partida, no encontrada, sin cuenta, solo `INGR` ⇒ recurso + nota), R19 (ramas CD, CI y CP con cuenta ⇒ partida, sin nota; `tipcos` no interviene), R20 (sin subcuenta del recurso ⇒ sin nota), notas sin nombres — en rojo  |  Verificación: traza RED
- [ ] T6: `cuenta_analitica.py`: `origen_subcuenta`, constantes y docstring (R7 de F-021 sustituida) (design §7.2)  |  Verificación: T5 y `test_f021_cuenta_analitica.py` en verde
- [ ] T7: Tests del cliente `tests/test_f031_cliente_partes.py`: `partes_del_periodo` (`con.est`, `ORDER BY hmo.ide DESC`, parámetros en lista) y `partidas_de_lineas` (cuenta y rama por `cag`, sin `tipcos`, `IN` con un `?` por partida, sin partidas no lee), `truncated` ⇒ excepción (R1, R13, R22) — en rojo  |  Verificación: traza RED
- [ ] T8: `sigrid_write_client.py`: `partes_del_periodo` y `partidas_de_lineas` (design §9); `partes_existentes` intacto  |  Verificación: T7 en verde
- [ ] T9: Tests de pipeline de la cuenta en `tests/test_f031_pipeline_cuenta_partida.py`: R17 (preflight y `INSERT` con la cuenta de la partida; modo pruebas al centro de pruebas), R18 (recurso + nota), R19 (partida CD con cuenta CD ⇒ esa), R21 (`caa_origen`/`caa_nota` en el JSON), R22 (una lectura de partidas, fuera del lock, fallo ⇒ nada escrito), R23 (una lectura de cuentas con ambas subcuentas), R24 (INFO sin nombres) — en rojo  |  Verificación: traza RED
- [ ] T10: `registro_pipeline.py`: `_resolver_cuentas` con partidas y `origen_subcuenta` (design §7.3)  |  Verificación: T9, T1 y suite `test_f021_*` en verde
- [ ] T11: Tests de pipeline del estado en `tests/test_f031_pipeline_estado.py`: R2, R3 (todo Imputado ⇒ `omitir` con `motivo_reabrir`, sin `stmts_crear_parte`, aviso con nº de retenidas), R4, R5, R8 (mismo lote tras pasar el parte a est 3 ⇒ se escribe), R9, R10 (`pisar_claves` no borra en Imputado), R12, R14 (preflight = ejecutar), R15 (`asdict` de `partes` en preflight y `resultado_a_dict`), R16, R29 (ninguna sentencia sobre `asa`/`apa`/`apu`/`asi` ni `con.est`) — en rojo  |  Verificación: traza RED
- [ ] T12: `settings.py` (`EST_PARTE_IMPUTADO`, `EST_PARTE_CERRADO`) y `registro_pipeline.py`: paso 5 con `partes_del_periodo` + `elegir_parte`, paso 6 bis y `aviso_de_parte`, docstring de pasos (design §7.4)  |  Verificación: T1, T9 y T11 en verde; suite completa de sv5 en verde
- [ ] T13: Test sv4 `services/partes-front/tests/test_f031_preflight_avisos.py`: `/api/aprobar/preflight` reenvía `partes[].aviso/estado/contabilizados` y `acciones[].caa_origen/caa_nota`; `resumenHtml` pinta `esc(p.aviso)` y `notasCuentaHtml` solo si vienen (R26–R28) — en rojo  |  Verificación: traza RED
- [ ] T14: `services/partes-front/static/app.js`: aviso del parte y `notasCuentaHtml` (design §6)  |  Verificación: `node --check services/partes-front/static/app.js`; T13 y suite de sv4 (incluido `test_f021_preflight_cuenta.py`) en verde
- [ ] T15: Tests `tests/test_f031_comprobar_asiento.py`: `comparar` (cuadra, descuadre > 0,01, sin_asiento, varios_asientos), lecturas con cliente simulado, salida sin contrapartidas por persona y sin `escribir` (R33–R36) — en rojo  |  Verificación: traza RED
- [ ] T16: `services/partes-transfer/comprobar_asiento_analitico.py` (design §7.5) con cabecera de uso  |  Verificación: T15 en verde; M1 y M2 (solo lectura) ejecutados por el implementer, salida sin nombres en `progress/impl_F-031.md`
- [ ] T17: `docs/ARCHITECTURE.md` (semántica 16 nueva; la de F-021 corregida: manda la cuenta de coste de la partida; herramienta de consola) y `docs/referencia/partes-proyecto.md` §3.5 (R37)  |  Verificación: lectura del reviewer contra design §1, §2 y §8
- [ ] T18: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5: lectura de `con.est` y de `obrparpar`/`cag`, parte Imputado (reabrir), cuenta de la partida del portal, herramienta (R37); commit local en ese repo, sin push  |  Verificación: `git -C ../azure-apps log -1`
- [ ] T19: Cobertura de líneas cambiadas y mutación completa sobre `estado_parte.py`, `cuenta_analitica.py`, `registro_models.py`, `sigrid_write_client.py`, `registro_pipeline.py`, `settings.py`, `comprobar_asiento_analitico.py` y `app.js` (si la herramienta lo cubre) en `progress/mutacion_F-031.md`  |  Verificación: 0 supervivientes sin test o justificación aceptada
- [ ] T20: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; M0, M3 y M4 (design §11) anotados en `progress/current.md` como MANUAL (humano)

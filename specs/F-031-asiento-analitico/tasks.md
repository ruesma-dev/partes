<!-- specs/F-031-asiento-analitico/tasks.md -->
# F-031 · El parte registrado acaba en el asiento analítico — Tareas

Rama: **`feature/F-031-asiento-analitico`** (ya creada). Un commit **local**
por tarea, `F-031 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin
push ni PR. Rigor **`critico`**: fase RED con traza en
`progress/impl_F-031.md` para **R2, R3, R4, R5, R8, R9, R13, R15 y R22**;
cobertura de líneas cambiadas ≥ umbral; campaña de mutación **completa** con
**0 supervivientes** sin test o justificación aceptada.

Reglas que no se negocian:
- **No empezar sin M0** (design §10): DA1–DA8 aprobadas por el humano y las
  contables (DA1, DA2, DA5, DA6) validadas con Juan Romero. Si la respuesta
  cambia DA1 o DA2, se para y se reescribe la spec.
- Ninguna escritura en Sigrid ni en la base `partes` durante la
  implementación; los tests usan `SigridFake` y `httpx` simulado.
- Ningún test ajeno se modifica; `dobles.py` solo crece (design §5).

- [ ] T1: Tests de caracterización en verde contra el código de hoy: R6 (periodo sin partes o con parte en registro ⇒ mismo resultado que hoy), R10 (synckey en parte Imputado ⇒ `ya_registrado`), R18 (`dedicacion`/`omitir`/`ya_registrado` no abren parte), R19 (empresa 28) en `tests/test_f031_pipeline_estado.py`  |  Verificación: `pytest services/partes-transfer/tests/test_f031_pipeline_estado.py` en verde
- [ ] T2: `dobles.py`: `SigridFake.partes_del_periodo` (con `est`, defecto 1), `partes_existentes` devuelve el de mayor `ide`, `SettingsFake` con `est_parte_imputado=10` y `est_parte_cerrado=3`  |  Verificación: suite completa de sv5 en verde sin tocar otros tests
- [ ] T3: Tests de la regla pura `tests/test_f031_estado_parte.py` (R2, R3, R5, R6, textos de aviso y motivo) — en rojo (módulo inexistente)  |  Verificación: traza RED pegada en `progress/impl_F-031.md`
- [ ] T4: `domain/models/registro_models.py` (`ParteSigrid`, campos nuevos de `ParteDestino`) y `application/services/estado_parte.py` (design §6.1)  |  Verificación: T3 en verde
- [ ] T5: Tests del cliente `tests/test_f031_cliente_partes.py`: SQL de `partes_del_periodo` con `con.est`, `ORDER BY hmo.ide DESC`, parámetros en lista, `truncated` ⇒ excepción (R1, R11) — en rojo  |  Verificación: traza RED
- [ ] T6: `sigrid_write_client.py`: `partes_del_periodo` (design §7); `partes_existentes` intacto  |  Verificación: T5 en verde
- [ ] T7: Tests del pipeline en `tests/test_f031_pipeline_estado.py`: R2, R3 (complementario creado con código nuevo y líneas en él), R4 (ningún insert/borrado contra un `hmoide` Imputado), R5, R8 (choque ⇒ `omitir` con `parte_contabilizado` y `caa_*` limpios), R9 (`pisar_claves` con la clave no borra en Imputado), R12 (preflight = ejecutar), R13 (`asdict` de `partes` en preflight y en `resultado_a_dict`), R14 (INFO sin nombres), R17 (ninguna sentencia sobre `asa`/`apa`/`apu`/`asi` ni `con.est`) — en rojo  |  Verificación: traza RED
- [ ] T8: `settings.py` (`EST_PARTE_IMPUTADO`, `EST_PARTE_CERRADO`) y `registro_pipeline.py`: paso 5 con `partes_del_periodo` + `elegir_parte` + `aviso_de_parte`, paso 6 bis, docstring de pasos (design §6.2)  |  Verificación: T1 y T7 en verde; suite completa de sv5 en verde (R20)
- [ ] T9: Test de sv4 `services/partes-front/tests/test_f031_preflight_aviso_parte.py`: `/api/aprobar/preflight` reenvía `partes[].aviso/estado/complementario/contabilizados` tal cual y `resumenHtml` de `static/app.js` pinta `esc(p.aviso)` solo si viene (R15, R16) — en rojo  |  Verificación: traza RED
- [ ] T10: `services/partes-front/static/app.js`: aviso del parte en `resumenHtml` (design §5)  |  Verificación: `node --check services/partes-front/static/app.js`; T9 y suite de sv4 en verde
- [ ] T11: Tests `tests/test_f031_comprobar_asiento.py`: `comparar` (cuadra, descuadre por > 0,01, sin_asiento, varios_asientos), lecturas con cliente simulado, salida sin cuentas de contrapartida por persona y sin llamadas a `escribir` (R21–R24) — en rojo  |  Verificación: traza RED
- [ ] T12: `services/partes-transfer/comprobar_asiento_analitico.py` (design §6.4), cabecera con uso y el comando de M1  |  Verificación: T11 en verde; M1 y M2 (solo lectura) ejecutados por el implementer con su salida (sin nombres) en `progress/impl_F-031.md`
- [ ] T13: `docs/ARCHITECTURE.md` (semántica 16 + herramienta de consola) y `docs/referencia/partes-proyecto.md` §3.5 (R25)  |  Verificación: lectura del reviewer contra design §1
- [ ] T14: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5: lectura de `con.est` de `hmo`, parte complementario, herramienta (R25); commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1`
- [ ] T15: Cobertura de líneas cambiadas y campaña de mutación completa sobre `estado_parte.py`, `registro_models.py`, `sigrid_write_client.py`, `registro_pipeline.py`, `settings.py`, `comprobar_asiento_analitico.py` y `app.js` (si la herramienta lo cubre), en `progress/mutacion_F-031.md`  |  Verificación: 0 supervivientes sin test o justificación aceptada
- [ ] T16: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; M3 y M4 (design §10) anotados en `progress/current.md` como MANUAL (humano)

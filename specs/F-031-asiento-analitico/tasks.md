<!-- specs/F-031-asiento-analitico/tasks.md -->
# F-031 · El parte registrado acaba en el asiento analítico — Tareas

Rama: **`feature/F-031-asiento-analitico`** (ya creada). Un commit **local**
por tarea, `F-031 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin
push ni PR. Rigor **`critico`**: fase RED con traza en
`progress/impl_F-031.md` para los R de design §10; cobertura de líneas
cambiadas ≥ umbral; campaña de mutación **completa** con **0
supervivientes** sin test o justificación aceptada.

Reglas que no se negocian:
- Decisiones de design §8 (v4). La lectura de «cerrado» (todo lo que no es
  En registro) está pendiente de confirmar por el humano (M0): vive solo en
  el predicado de `elegir_parte`; si la corrige antes de T4, se para.
- Ninguna escritura en Sigrid ni en la base `partes`; los tests usan
  `SigridFake` y `httpx` simulado.
- Ningún test ajeno se modifica (tampoco los `test_f021_*`, R27);
  `dobles.py` solo crece. Si un test ajeno se pone rojo, se para.

- [x] T1: Caracterización en verde contra el código de hoy en `tests/test_f031_pipeline_estado.py` y `tests/test_f031_pipeline_cuenta_partida.py`: R4, R6 (un parte En registro), R10, R20 (la cuenta del recurso manda aunque la línea traiga partida con otra cuenta), R22 (Porsan sin cuenta ni nota), R32, R33, y suite `test_f021_*` en verde (R27)  |  Verificación: `pytest services/partes-transfer/tests/test_f031_pipeline_estado.py services/partes-transfer/tests/test_f031_pipeline_cuenta_partida.py` en verde
- [x] T2: `dobles.py`: `SigridFake(partidas=...)`, `partes_del_periodo` (`est`, defecto 1, orden `ide` desc), `partidas_de_lineas` + `partidas_leidas`, `partes_existentes` con el de mayor `ide`; `SettingsFake` con `est_parte_activo=1`, `est_parte_cerrado=3`, `est_parte_imputado=10`  |  Verificación: suite completa de sv5 en verde sin tocar otros tests
- [x] T3: Tests de la regla pura `tests/test_f031_estado_parte.py`: R2 (mayor `ide` En registro, aunque haya cerrados de `ide` mayor), R3 (todos cerrados ⇒ `existe=False`, `complementario=True`), R4, R7 (nombres de estado y «estado N»), R18 (texto del aviso, nuevo y existente), texto de `motivo_choque` con prefijo `parte_cerrado: ` y sin nombres — en rojo  |  Verificación: traza RED en `progress/impl_F-031.md`
- [x] T4: `registro_models.py` (`ParteSigrid`, `PartidaCuenta`, campos de `ParteDestino` y `AccionLinea`) y `application/services/estado_parte.py` (design §7.1)  |  Verificación: T3 en verde
- [x] T5: Tests puros `tests/test_f031_cuenta_partida.py`: `subcuenta_de_partida` (CI y CD sí; CP, INGR, sin punto, vacía, `None` no) y `origen_subcuenta`: R20 (recurso con subcuenta ⇒ recurso aunque la partida tenga otra), R21 (recurso sin subcuenta + partida CI/CD ⇒ partida con nota sin nombres), R22 (sin partida, no encontrada, sin cuenta, `INGR`, `CP` ⇒ `(None, None, None)`) — en rojo  |  Verificación: traza RED
- [ ] T6: `cuenta_analitica.py`: `SUBCUENTAS_COSTE_PARTIDA`, `OrigenSubcuenta`, `subcuenta_de_partida`, `origen_subcuenta` y docstring (R7 de F-021 matizada) (design §7.2)  |  Verificación: T5 y `test_f021_cuenta_analitica.py` en verde
- [ ] T7: Tests del cliente `tests/test_f031_cliente_partes.py`: `partes_del_periodo` (`con.est`, `ORDER BY hmo.ide DESC`, parámetros en lista, lista de `ParteSigrid`) y `partidas_de_lineas` (`obrparpar` + `con` de `caaide`, `IN` con un `?` por partida, sin partidas no lee), `truncated` ⇒ excepción (R1, R15, R24) — en rojo  |  Verificación: traza RED
- [ ] T8: `sigrid_write_client.py`: `partes_del_periodo` y `partidas_de_lineas` (design §9); `partes_existentes`, `stmts_crear_parte` y `lineas_existentes` intactos  |  Verificación: T7 en verde
- [ ] T9: Tests de pipeline de la cuenta en `tests/test_f031_pipeline_cuenta_partida.py`: R21 (preflight e `INSERT` con la cuenta de la partida en el centro de la obra; modo pruebas al centro de pruebas; obra sin esa cuenta ⇒ `obra_sin_cuenta` de F-021), R23 (`caa_origen`/`caa_nota` en el JSON), R24 (una lectura de partidas solo si hace falta, fuera del lock; fallo ⇒ nada escrito), R25 (una lectura de cuentas con ambos orígenes), R26 (INFO sin nombres) — en rojo  |  Verificación: traza RED
- [ ] T10: `registro_pipeline.py`: `_resolver_cuentas` con respaldo de partida y `origen_subcuenta` (design §7.3)  |  Verificación: T9, T1 y suite `test_f021_*` en verde
- [ ] T11: Tests de pipeline del parte en `tests/test_f031_pipeline_estado.py`: R2 (Cerrado de mayor `ide` + En registro ⇒ el En registro), R3 (Cerrado/Imputado solos ⇒ preflight propone `PT..` nuevo y ejecutar lo crea En registro con `Parte <obra>`; el original sin sentencias), R5 (ninguna sentencia con el `hmoide` cerrado ni `UPDATE`), R8 (segunda aprobación reutiliza el complementario; verde ya hoy, se deja como guarda), R9 (relectura con otro código o no En registro ⇒ nada insertado), R11 (choque con parte cerrado ⇒ `omitir`), R12 (choque en otro parte En registro ⇒ conflicto con su `parte_cod`), R13, R14, R15 (fallo en partes o líneas ⇒ nada escrito), R16 (preflight = ejecutar), R17 (`asdict` de `partes` en preflight y `resultado_a_dict`), R19, R31 (nada sobre `asa`/`apa`/`apu`/`asi` ni `con.est`) — en rojo  |  Verificación: traza RED
- [ ] T12: `settings.py` (`EST_PARTE_CERRADO`, `EST_PARTE_IMPUTADO`) y `registro_pipeline.py`: paso 5 con `partes_del_periodo` + `elegir_parte` + `aviso_de_parte`, paso 7 sobre todos los partes del periodo, paso 8 con relectura por código, docstring de pasos (design §7.4)  |  Verificación: T1, T9 y T11 en verde; suite completa de sv5 en verde
- [ ] T13: Test sv4 `services/partes-front/tests/test_f031_preflight_avisos.py`: `/api/aprobar/preflight` reenvía `partes[].complementario/estado/cerrados/aviso` y `acciones[].caa_origen/caa_nota`; `resumenHtml` rotula «complementario», pinta `esc(p.aviso)` y `notasCuentaHtml` solo si vienen (R28–R30) — en rojo  |  Verificación: traza RED
- [ ] T14: `services/partes-front/static/app.js`: rótulo y aviso del parte y `notasCuentaHtml` (design §6)  |  Verificación: `node --check services/partes-front/static/app.js`; T13 y suite de sv4 (incluido `test_f021_preflight_cuenta.py`) en verde
- [ ] T15: Tests `tests/test_f031_comprobar_asiento.py`: `comparar` (cuadra, descuadre > 0,01, sin_asiento, varios_asientos), lecturas con cliente simulado, varios partes en el periodo, salida sin contrapartidas por persona y sin `escribir` (R35–R38) — en rojo  |  Verificación: traza RED
- [ ] T16: `services/partes-transfer/comprobar_asiento_analitico.py` (design §7.5) con cabecera de uso  |  Verificación: T15 en verde; M1 y M2 (solo lectura) ejecutados por el implementer, salida sin nombres en `progress/impl_F-031.md`
- [ ] T17: `docs/ARCHITECTURE.md` (semántica 16 nueva: complementario y estados; la de F-021 matizada: respaldo de partida `C[ID]`; herramienta de consola) y `docs/referencia/partes-proyecto.md` §3.5 (R39)  |  Verificación: lectura del reviewer contra design §1, §2 y §8
- [ ] T18: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5: lectura de `con.est` y de `obrparpar`, complementario, cuenta del recurso con respaldo de partida, herramienta (R39); commit local en ese repo, sin push  |  Verificación: `git -C ../azure-apps log -1`
- [ ] T19: Cobertura de líneas cambiadas y mutación completa sobre `estado_parte.py`, `cuenta_analitica.py`, `registro_models.py`, `sigrid_write_client.py`, `registro_pipeline.py`, `settings.py`, `comprobar_asiento_analitico.py` y `app.js` (si la herramienta lo cubre) en `progress/mutacion_F-031.md`  |  Verificación: 0 supervivientes sin test o justificación aceptada
- [ ] T20: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; M0, M3, M4 y M5 (design §11) anotados en `progress/current.md` como MANUAL (humano)

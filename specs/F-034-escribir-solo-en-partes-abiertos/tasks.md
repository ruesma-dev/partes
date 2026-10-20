<!-- specs/F-034-escribir-solo-en-partes-abiertos/tasks.md -->
# F-034 · sv5 solo escribe en partes de Sigrid abiertos — Tareas

Rama: **`feature/F-034-escribir-solo-en-partes-abiertos`** (worktree `partes-wt-f034`). Un commit **local** por tarea, `F-034 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni PR. Rigor **`critico`**: fase RED con traza en `progress/impl_F-034.md` para **R1–R6, R9–R13 y R19**; R15–R18 y R20 son de **caracterización** (pasan antes de tocar código); cobertura de líneas cambiadas ≥ umbral; campaña de mutación **completa** con 0 supervivientes sin test o justificación aceptada.

Reglas que no se negocian:

- No se empieza sin el visto bueno del humano a DA1–DA9 (`design.md` §11) y sin M1 medida por el líder. Si una tarea obliga a tocar `estado_parte.py`, `stmts_crear_parte`, `_crear_parte`, `reajuste_lineas.py`, el schema o el contrato JSON sv4↔sv5: `blocked` y se consulta.
- Ninguna escritura contra Sigrid desde los agentes: M2–M4 son del humano.

- [ ] T1: Caracterización (sin tocar código): R15 (complementario y `parte_cerrado`), R16 (reaprobación `ya_registrado` en parte cerrado, 0 sentencias), R17 (reajuste en parte cerrado rechazado) y R18 (alta intacta) en `tests/test_f034_pipeline_cierre.py`  |  Verificación: `pytest services/partes-transfer/tests/test_f034_pipeline_cierre.py` en verde ANTES de T2
- [ ] T2: `parte_abierto.py` (motivos, `confirmar_escritas`, `parte_que_impidio`) con sus tests RED→GREEN en `test_f034_parte_abierto.py` (R9, R11)  |  Verificación: `pytest services/partes-transfer/tests/test_f034_parte_abierto.py`
- [ ] T3: Cliente: `_guarda_parte_abierto` y `stmt_insert_linea` (subconsulta `x`, guarda, `pisadas`) y `stmt_borrar_linea` de instancia con guarda; tests de texto y parámetros exactos RED→GREEN en `test_f034_cliente_guarda.py`; ampliar `test_f021_cliente_cuenta.py` (R14 de F-021) al SQL nuevo (R1–R4, R7)  |  Verificación: `pytest services/partes-transfer/tests/test_f034_cliente_guarda.py services/partes-transfer/tests/test_f021_cliente_cuenta.py`
- [ ] T4: Cliente F-046: `UPDLOCK, HOLDLOCK` en guardia y `UPDATE`, guarda en `stmt_insertar_extra`; ampliar `test_f046_cliente_reajuste.py` y `test_f046_t22_cliente_bordes.py` sin relajarlos (R5, R6)  |  Verificación: `pytest services/partes-transfer/tests/test_f034_cliente_guarda.py services/partes-transfer/tests/test_f046_cliente_reajuste.py services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`
- [ ] T5: `SigridFake`: `cerrar_al_escribir`, guarda y `pisadas` en `insert`, `borrar` de instancia con guarda, `lineas_por_ide` con `_comprobar_lock` (design §6); la suite de sv5 sigue en verde  |  Verificación: `pytest services/partes-transfer/tests`
- [ ] T6: Pipeline paso 9: `pisadas_de`, `pisadas=` en el `INSERT`, `borradas` por relectura (R4, R12); tests del ejemplo 2 RED→GREEN  |  Verificación: `pytest services/partes-transfer/tests/test_f034_pipeline_cierre.py -k "pisad or borradas"`
- [ ] T7: Pipeline relectura: `confirmar_escritas`, `partes_del_periodo` por periodo afectado, motivos, WARNING/ERROR sin nombres, excepción si falla (R8–R11, R13, R14); ejemplo 1, dos periodos, cierre entre lotes, `vigilar_lock`  |  Verificación: `pytest services/partes-transfer/tests/test_f034_pipeline_cierre.py`
- [ ] T8: sv4 `resultadoHtml` agrupa las omitidas por motivo, escapado (R19); test con `node` y R20 en `services/partes-front/tests/test_f034_resultado_omitidas.py`  |  Verificación: `pytest services/partes-front/tests/test_f034_resultado_omitidas.py` y `node --check services/partes-front/static/app.js`
- [ ] T9: Comprobar que no cambian los ficheros vigilados por `porcentajes` (R7, DA6)  |  Verificación: `git diff --quiet dev -- services/partes-transfer/application/services/estado_parte.py services/partes-transfer/application/services/cuenta_analitica.py` (código 0) y `test_f031_cliente_alta.py` en verde
- [ ] T10: Documentación: `docs/ARCHITECTURE.md` semántica 16 y docstrings de los pasos 8–9 de `registro_pipeline.py` (R21)  |  Verificación: `pytest tests/test_documentos_del_arnes.py` y lectura del reviewer
- [ ] T11: `azure-apps/partes.md` (pasos 5–6, «Qué se rompe» y nota a `porcentajes`), commit local en el repositorio `azure-apps` (R21)  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1 --stat` muestra solo `partes.md`
- [ ] T12: Campaña de mutación completa y análisis de supervivientes  |  Verificación: `python -m harness.mutacion --feature F-034` con 0 supervivientes sin test o justificación
- [ ] T13: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
- [x] M1: Líder, solo lectura, antes de T1 (hecha el 2026-10-20; cifras en `design.md` §9): las tres consultas de `design.md` §9 por `sql/read` contra `ruesma`  |  Verificación: MANUAL (líder), cifras en `progress/current.md`
- [ ] M2: Humano, tras desplegar sv5 y sv4: registro en modo pruebas (0404, `PRUEBA-IA`) y, si hay caso, reajuste  |  Verificación: MANUAL (humano), `design.md` §9
- [ ] M3: Humano, con autorización expresa: parte de 0404 cerrado ⇒ complementario; `INSERT` guardado ⇒ 0 filas; limpieza con `prueba_escritura_sigrid.py`  |  Verificación: MANUAL (humano), `design.md` §9
- [ ] M4: Humano: el modal de resultado agrupa los motivos de las omitidas  |  Verificación: MANUAL (humano), Ctrl+F5 en el portal

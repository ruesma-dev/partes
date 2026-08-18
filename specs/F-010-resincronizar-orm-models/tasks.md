<!-- specs/F-010-resincronizar-orm-models/tasks.md -->
# F-010 · Saneamiento: resincronizar `orm_models.py` entre sv3 y sv4 — Tareas

Rama: `feature/F-010-resincronizar-orm-models`. Un commit por tarea
(`F-010 Tn: ...`). Rigor `estandar`: fase RED con traza real en
`progress/impl_F-010.md`, cobertura de líneas cambiadas ≥ umbral, campaña
`python -m harness.mutacion --feature F-010` con supervivientes analizados.
Tests SIEMPRE sin red ni BBDD (SQLite en memoria vía
`services/partes-front/tests/dobles.py`, dobles de `engine` para
`initialize()`, compilación de DDL sin conexión).

Orden: primero los tests (guardián con RED natural —hoy falla porque las
copias divergen— y tests del generador con RED por `ImportError`), después
la resincronización que los pone en verde, después los `initialize()`,
después R11 y la documentación.

- [x] T1: Crear `tests/test_f010_orm_models_gemelos.py` (raíz) con R1, R2,
      R3 (parametrizado con 4 alteraciones en `tmp_path`) y R4 (lista literal
      de las 56 columnas de `parte_registros`, 4 tablas, atributos clave de
      `horas_orig`, `extra_auto`, `sigrid_*`, `UndoLogOrm`).
      | Verificación: `python -m pytest tests -q -k f010` → R1, R2 y R4 en ROJO contra el árbol real (traza pegada en `impl_F-010.md`: es la fase RED de la feature) y R3 en VERDE (las alteraciones se detectan). Commit del test en rojo permitido en esta tarea (el `init.sh` completo se exige en T9).

- [x] T2: Tests del generador en sv3:
      `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py`
      con R6 (a–d), R9 y R10 (sobre `Base.metadata` real y sobre un
      `MetaData` de juguete). Se escriben ANTES de que exista el generador.
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k f010` → ROJO natural (`ImportError: cannot import name 'ddl_complementario'`; traza pegada en `impl_F-010.md`). Commit del test en rojo permitido en esta tarea.

- [x] T3: Escribir el `orm_models.py` canónico (D1, §6.1 del diseño: base
      sv3 + bloque `sigrid_*` de sv4 + `UndoLogOrm` + docstring «cuatro
      tablas» + `DDL_EXTRA_POSTGRES` + `ddl_complementario()`) y copiarlo
      byte a byte a las DOS rutas
      (`services/partes-persistencia/infrastructure/database/orm_models.py`
      y `services/partes-front/infrastructure/database/orm_models.py`).
      | Verificación: `python -m pytest tests -q -k f010` → R1, R2, R3, R4 en VERDE; `python -m pytest services/partes-persistencia/tests -q -k f010` → R6, R9, R10 en VERDE; `cmp`/`fc` de los dos ficheros sin diferencias; las suites completas de sv3 y sv4 siguen en verde (`python -m pytest services/partes-persistencia/tests -q`, `python -m pytest services/partes-front/tests -q`).

- [x] T4: sv3 `SqlAlchemyParteRepository.initialize()` usa
      `ddl_complementario()`; borrar `_DDL_PARTIAL_UNIQUE` y `_DDL_ALTERS`.
      Test `services/partes-persistencia/tests/test_f010_r7_initialize_sv3.py`
      (engine doble grabador; `create_all` antes; sentencias == generador,
      en orden).
      | Verificación: RED (el test exige las sentencias del generador y `initialize()` aún ejecuta la lista a mano) → GREEN; `grep -n "_DDL_ALTERS\|_DDL_PARTIAL_UNIQUE" services/partes-persistencia -r` sin resultados; suite sv3 en verde.

- [x] T5: sv4 `ParteReviewRepository.initialize()` usa
      `ddl_complementario()` dentro del `try/except` actual; borrar los
      `ALTER`, `CREATE TABLE IF NOT EXISTS empleado_alias/undo_log` y el
      parche `undo_log.actor` a mano. Test
      `services/partes-front/tests/test_f010_r8_initialize_sv4.py` (mismo
      doble; `engine.begin()` que lanza → `False` sin propagar y con
      `logger.exception`).
      | Verificación: RED → GREEN; `grep -n "ADD COLUMN IF NOT EXISTS\|CREATE TABLE IF NOT EXISTS" services/partes-front/infrastructure -r` sin resultados fuera de `orm_models.py`; suite sv4 en verde.

- [x] T6: sv4 R11: quitar el `DELETE` masivo previo a `session.delete(doc)`
      en `hard_delete_document` y `vaciar_papelera`. Test
      `services/partes-front/tests/test_f010_r11_borrado_sin_sawarning.py`
      con `warnings.simplefilter("error", SAWarning)`.
      | Verificación: RED real (hoy el test revienta con `SAWarning: DELETE statement on table 'parte_registros' expected to delete 1 row(s); 0 were matched`) → GREEN; `python -m pytest services/partes-front/tests -q -W error::sqlalchemy.exc.SAWarning -k "f004 or f010"` en verde (los R12/R18 de F-004 dejan de avisar).

- [x] T7: Documentación (R12): `docs/ARCHITECTURE.md` punto 7;
      `docs/referencia/partes-proyecto.md` §5 (+ línea de corrección en la
      cabecera, D5); `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`
      §4 (commit local en ese repositorio: «partes: F-010 corrige el
      esquema de la BBDD (cuatro tablas, columnas reales de
      parte_registros)», sin push).
      | Verificación: revisión del reviewer (C3, C3 bis: barrido de datos sensibles sobre `docs/referencia/partes-proyecto.md` con los patrones habituales —correos, IPs, GUID, tokens—; `git -C ../azure-apps log -1 --stat` muestra el commit).

- [x] T8: Campaña de mutación `python -m harness.mutacion --feature F-010`
      y análisis de supervivientes en `progress/mutacion_F-010.md`; informe
      `progress/impl_F-010.md` con «Evidencias» (tests/resultado, cobertura
      de líneas cambiadas, mutantes/supervivientes, tiempo de la suite) y
      las trazas RED de T1, T2, T4, T5, T6.
      | Verificación: `progress/mutacion_F-010.md` existe con totales reales y ninguna sección `PENDIENTE`; puerta de cobertura de `init.sh` en `[OK]`.

- [x] T9: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: exit code 0, incluye la suite de la raíz (guardián) y las de sv3/sv4.

## Verificaciones MANUAL (humano) — requieren BBDD real

- **M1 (D3, R10)**: tras desplegar o arrancar sv3 o sv4 en local con el
  `.env` de desarrollo, comprobar que el único cambio físico es el índice
  nuevo:
  `SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename='parte_registros' ORDER BY 1;`
  → debe listar `ix_parte_registros_deleted_at_utc`, `ix_parte_registros_document_id`,
  `ix_parte_registros_empleado_ide`, `parte_registros_pkey` (antes de F-010
  faltaba el primero). Y que el número de columnas no cambió:
  `SELECT table_name, count(*) FROM information_schema.columns WHERE table_schema='public' GROUP BY 1 ORDER BY 1;`
  → `empleado_alias 7`, `parte_documents 47`, `parte_registros 56`, `undo_log 7`.
- **M2 (R7/R8)**: el arranque de sv3 (`python main.py` o `main_worker.py`)
  y de sv4 (`python main.py`) en local termina sin excepción en
  `initialize()` (log `[parte-repo] esquema inicializado` / portal
  operativo).
- **M3**: al desplegar (cuando el humano lo decida, con
  `redeploy_partes.ps1`), orden seguro habitual sv3 antes que sv4; ambos
  ejecutan el mismo DDL idempotente, así que el orden no es crítico para
  F-010.

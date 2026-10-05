<!-- specs/F-030-recurso-sin-ficha/tasks.md -->
# F-030 · Recurso por DNI sin ficha de empleado — Tareas

Rama: **`feature/F-030-recurso-sin-ficha`** (ya creada). Un commit **local** por tarea, `F-030 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni PR. Rigor **`critico`**: fase RED con traza en `progress/impl_F-030.md` para **R1, R2, R3, R4, R5, R9, R10, R16, R17 y R18**; R6–R8, R11–R15, R19 y R20 son de **caracterización** (verdes ya hoy: se anota que pasan antes de tocar código); cobertura de líneas cambiadas ≥ umbral; campaña de mutación **completa** con 0 supervivientes sin test o justificación aceptada.

Reglas que no se negocian:

- **No empezar sin DA1–DA9 aprobadas** (`design.md` §8). Si DA4 se rechaza, T6–T7 desaparecen; si DA3 se rechaza, R10 se reescribe antes de seguir.
- **Ninguna copia de la lista cerrada se toca** (DA6): si una tarea lo exige, `blocked` y se consulta.
- **Ningún test toca red, Sigrid ni PostgreSQL**; datos **sintéticos** (ni DNIs, ni nombres, ni códigos de recurso reales). Ni una escritura en Sigrid ni en la base `partes`.
- Comando de tests por servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [ ] T1: Tests de caracterización en verde contra el código de hoy, antes de cambiar nada: conciliador (R11, R12) en `services/partes-persistencia/tests/test_f030_conciliador_sin_ficha.py` y sv5 (R14, R15, R20) en `services/partes-transfer/tests/test_f030_coherencia_sin_ficha.py`  |  Verificación: los dos ficheros en verde; anotado en `progress/impl_F-030.md` que pasan sin cambios de código
- [ ] T2: Tests de R1–R3 en rojo (traza RED) e implementar `dni_canonico` en `text_match.py` y su uso en `parte_normalizer.py` (design §6.1)  |  Verificación: `pytest tests/test_f030_dni_canonico.py` y suite completa de sv3 en verde
- [ ] T3: Test de R9 en rojo (traza RED): `rc.res AS nombre` en `_SQL_RECURSOS`, mapeo en `fetch_recursos` y `RecursoRow.nombre`  |  Verificación: `pytest tests/test_f030_casado_recurso.py -k r9` y `tests/test_f023_cliente_sigrid.py` en verde (si un test de F-023 fija las columnas, se adapta al mínimo y se declara como desviación)
- [ ] T4: Tests de R4–R8 en rojo los de R4 y R5 (traza RED) y verdes ya los de R6–R8; paso `_casar_por_recurso` y `METODO_RECURSO_DNI` en `persist_parte_pipeline.py` (design §6.2)  |  Verificación: `pytest tests/test_f030_casado_recurso.py` y `tests/test_f023_pipeline_match.py` en verde
- [ ] T5: Test de R10 en rojo (traza RED) y cambio de `_compute_review_required`; comentario de `EmpleadoMatch.method` en `parte_records.py`  |  Verificación: `pytest tests/test_f030_casado_recurso.py -k r10` y suite completa de sv3 en verde
- [ ] T6: Tests de R16 y R18 en rojo (traza RED): `METODO_RECURSO_DNI`, `esta_casado`, `casado_por_recurso`, `sin_ficha` en las cuatro vistas y filtro de la cola en `parte_repository.py` (design §6.4)  |  Verificación: `pytest tests/test_f030_portal_recurso_dni.py -k "r16 or r18"` en verde
- [ ] T7: Test de R17 en rojo (traza RED, renderizando cada plantilla con Jinja2) y badge en `parte_detail.html`, `obra_detail.html`, `trabajadores_list.html` y `trabajador_detail.html`; test de R19 (reasignar suelta el recurso) en verde  |  Verificación: `pytest tests/test_f030_portal_recurso_dni.py` y suite completa de sv4 en verde
- [ ] T8: Comprobar que la lista cerrada no se ha tocado (R13)  |  Verificación: `git diff dev --stat -- services/partes-persistencia/application/services/seleccion_sigrid.py services/partes-transfer/application/services/coherencia_recurso.py services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` vacío y `.venv/Scripts/python.exe -m pytest -q tests/test_f023_de_alta_gemelos.py` en verde
- [ ] T9: `docs/ARCHITECTURE.md` (semántica 2 y 12, ≤ 6 líneas) y `docs/referencia/partes-proyecto.md` §4.6 y §7 (R21)  |  Verificación: lectura del reviewer contra design §5
- [ ] T10: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`, viñetas Empleado y Recurso (R21); commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1` muestra el commit
- [ ] T11: Cobertura de líneas cambiadas y campaña de mutación completa (`python -m harness.mutacion --feature F-030`) en `progress/mutacion_F-030.md`, con cada superviviente matado por un test nuevo o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T12: Anotar en `progress/current.md` el orden de despliegue (sv3 → sv4) y las verificaciones MANUAL M1–M4 de design §9 como pendientes del humano  |  Verificación: MANUAL (humano) — M3: papelera de los 2 partes de Porsan, mover sus correos de `Procesados` a la bandeja de entrada no leídos y comprobar en el portal «Casado por recurso (sin ficha)» y recurso `ok`/`sin_parte`; M4: logs de `ca-sv5-transfer` con `[registro] cuentas obra=0724 ok=0 recurso_sin_cuenta=N`
- [ ] T13: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde

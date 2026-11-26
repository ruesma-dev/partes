<!-- progress/review_F-084.md -->
Revisión completa (pasada 1, principal) · HEAD 8f559d1 · `git diff dev...HEAD` (merge-base d11d228)

# F-084 · Review (pasada principal)

**Veredicto: CHANGES_REQUESTED** (dos arreglos de documentación y init.sh con exit 0; nada de código: «Cambios requeridos»).

**Nivel de rigor:** `critico`, declarado en `features.json` (disparador 2: sv3 escribe en producción y DDL
en el PostgreSQL compartido). Exige fase RED, cobertura ≥ 90 %, mutación (muestra 60 %, [100, 300], 0
supervivientes salvo justificación aceptada), RM1–RM7. La e2e es informativa y aquí N/A. La mutación (T10)
la lanza el líder después de este veredicto: sus puntos quedan **pendiente: pasada de evidencias**.

## init.sh

Tres ejecuciones en la copia, a HEAD 8f559d1; **ninguna salió con exit 0, y en ningún caso por F-084**:
1. `bash harness/init.sh`: raíz roja con `-x` en `tests/test_f059_ejecucion.py::test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`
   (`FileNotFoundError … nieto.pid`, el inestable conocido; 1571 passed). Los cinco servicios salieron **por caché**.
2. `ARNES_SIN_CACHE=1 bash harness/init.sh`: raíz roja con `-x` en la preparación de
   `tests/test_f024_borrado_no_congela_gemelos.py::test_f024_r13_…` (`TimeoutExpired … after -523.8 seconds`:
   timeout **negativo**, el reloj saltó, probablemente porque el equipo se suspendió; `congelacion.py` no lo toca F-084).
   Servicios **sin caché, todos en verde**: sv1 74 · sv2 579/1 skip · sv3 2966/2 skip · sv4 **4137**/1 skip (26 min) ·
   sv5 1890/1 skip. `PUERTA COBERTURA` [OK] 100,0 % (303/303) · `PUERTA TAMAÑO` [OK] · `CARRIL` N/A (critico) ·
   `CAPA E2E` N/A · rama correcta · ruff 1188 avisos (antes 1184: imports de los tests nuevos, no bloquea).
3. Raíz entera a mano, sin `-x` ni cobertura (`python -m pytest tests -q --tb=short -p no:cacheprovider`):
   **2549 passed, 50 skipped, 0 fallos** (28 min), los dos de arriba incluidos.

Todo lo que mide init.sh se ha visto en verde ejecutándose, pero **no en una misma pasada con exit 0** (cambio 3).

## Checkpoints

**C1** [ ] exit 0 en una sola pasada: no se ha dado (dos inestables ajenos, arriba); no es imputable a F-084, se exige en la pasada 2 · [x] ficheros base existen.
**C2** [x] una sola activa (F-084) · [x] prioridad · [x] rama `feature/F-084-partes-con-problemas` · [x]
`current.md` de la sesión activa · [x] las `done` con resumen en `history.md` (no lo toca).
**C3** [x] hexagonal: módulo puro `application/services/partes_con_problemas.py` sin BBDD/ORM/FastAPI (solo
importa `parte_vacio`); el repositorio (infra) y `app.py` (adaptador) lo consumen. [x] primera línea con ruta
en todo fichero de código nuevo (la plantilla sigue el uso de sus vecinas). [x] sin `print`, TODOs ni
secretos; sin dependencias nuevas. [ ] **reglas de `ARCHITECTURE.md`/documentación al día**: ver cambio 2.
Trampas: (1) empleado≠recurso: no aplica (no registra en Sigrid); (2) incidencias: las horas de la fila
excluyen `es_incidencia`, como `/partes`; (3) esquema: los dos `orm_models.py` **byte-idénticos** (`cmp`),
nullables, sin `server_default`, lectores listados (sv3 escribe, sv4 lee).
**C3 bis** N/A: no toca `docs/referencia/`. **C3 ter** N/A: la única cita del humano («d2, en este caso se
sustituye como hasta ahora…») va con fecha y origen en `features.json` y la spec; no hay más afirmaciones atribuidas.
**C3 quater** [x] `azure-apps` e09fd49 toca solo `partes.md` (`git show --stat`) · [x] commit aparte, SHA en
`impl_F-084.md` · [x] sin push (encima está 19062db, F-020 de otro proyecto, ajeno) · [x] coincide con la
Frontera de design §11 (§3.3, §3.4 con las tres rutas, §4.1 fila nueva y nota de Papelera, §4.5 `actor`, motivos).
**C4** [x] cada R1–R26 con ≥ 1 test `test_f084_rN_*` y en verde (tabla abajo) · [x] unit sin red ni BBDD real
(SQLite en memoria de `dobles.py`, `ColaFake`) · [ ] **MANUAL M1–M3 no están en `progress/current.md` con su
comando exacto** (cambio 1; están en `tasks.md` T11 y design §12, que es donde no lo busca el humano) ·
[x] dobles: `ColaFake.enviar(queue_name, payload)` = `ColaCliente.enviar` (`infrastructure/azure/cola_cliente.py:85`);
`_RepoRoto` hereda del repositorio real.
**C4 bis** [x] rigor declarado · [x] fase RED con salida real (T1, T3, T5, T7) · [x] cobertura 100,0 % ·
mutación, supervivientes, RM1, RM2, RM5, RM6: **pendiente: pasada de evidencias** (T10, por encargo) · [x]
«Evidencias» completa · [x] e2e N/A (`CAPA E2E: N/A`, ningún `(capa: e2e)`) · [x] ningún N/A sin motivo.
**RM7** [x] aplicada a mano en una copia desechable del scratchpad (árbol de trabajo intacto; base sin mutar
61 passed): pedir el recálculo ANTES de `repository.recuperar_parte` ⇒ ROJO (6 de W); mover tras el `commit` el
choque ⇒ ROJO (P r19 ×2, W r19), el sha256 ⇒ ROJO (P r20), la congelación con fecha ⇒ ROJO (P :384, W :256) y la
espera de recálculo ⇒ ROJO (P r21). Todas cazadas por tests de F-084. sv3: rastro en el mismo `commit` (A r1).
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1–T9 y T12 `[x]` con commit `F-084 Tn` cada una (10); T10 y T11 abiertas por diseño · [x] sin
temporales · [x] `features.json` en `in_review`, rigor `critico`, spec aprobada 2026-11-26.

## Lo mirado con cuidado (encargo del líder)

- **sv3**: el diff solo añade, en la rama `old.is_active = False` que ya existía, `sustituido_por_id`,
  `sustituido_at_utc` y el WARNING (ids, `fecha_int`, código/número de obra; sin nombres, con test). La
  condición (`_emp_signals`, `_misma_entrada`, la consulta) no cambia: R4 con los tests anteriores intactos.
  DDL solo por `ddl_complementario()`, que ejecutan sv3 y sv4 al arrancar: **cualquier orden de despliegue
  vale** (sv4 viejo no selecciona las columnas; sv3 viejo no las escribe y sv4 cae en la pista de R8).
  Solo el reemplazo y el retirado de F-061 dejan «inactivo sin papelera» (barrido de `is_active = False`).
- **sv4, clasificación**: orden R6 exacto; `ORDEN_MOTIVOS` deja `sustituido` al final («los que cuentan,
  primero»); papelera fuera de la consulta y retirados fuera por `es_retirado`; contador con `NO_CUENTAN`;
  pista retroactiva coherente con la identidad de obra de sv3 (código del nuevo, o número sin código).
  Un `sustituido_por_id` que apunta a un parte en la papelera da `desactivado_sin_rastro` y cuenta: correcto.
- **`recuperar_parte`**: guardas en el orden de design §6, todas antes de escribir (RM7 arriba); con fecha,
  fecha y líneas como `update_parte_fecha`; conserva el rastro; `undo_log` con `actor` y `reactivados`; el
  recálculo tras el commit y su fallo no deshace (test con la cola rota). Deshacer: snapshots + vuelta a
  inactivo salvo congelado o ya descartado (tests). Rutas bajo Easy Auth de plataforma, como el resto;
  `_actor(request)` firma. Logs: ids, fechas y actor (R24 lo pide; mismo uso que `[reparto] … (por %s)`).
- **Guardianes ajustados**: `test_f017_punto_unico` 23→24 es exactamente la llamada nueva de la ruta de
  recuperar, documentada en el docstring; `test_f047` descuenta en `F084_PROBLEMAS` las tres funciones
  nuevas, como F-052/F-068, y exige que existan. Ninguno afloja lo que vigila: **legítimos**.
- **Decisiones pequeñas**: ninguna contradice un requisito. Agrupar bajo el primer motivo cumple R11 (los
  demás salen como insignias); `None`⇒404 y fecha vacía = conservar cumplen R17/R22; `obra_codigo`/`obra_nombre`
  es lo que pide R11; «Ver PDF» solo con visor es más estricto que R12 pero igual que Conciliar (sin visor el
  botón no abriría nada) → observación 2.
- **Límite de servicio**: sv3 escribe, sv4 lee; gemelos solo importados; la lista cerrada de `CLAUDE.md` no crece.
- **Riesgo §10**: confirmado y aceptado en la spec → observación 1.

## Cobertura requisito → test

Ficheros: sv3 `services/partes-persistencia/tests/test_f084_rastro_reemplazo.py` (A); sv4 `services/partes-front/tests/`
`test_f084_clasificacion.py` (C), `test_f084_recuperar.py` (P) y `test_f084_portal.py` (W). Nombres `test_f084_rN_*`.

| Req | Tests | Req | Tests |
|---|---|---|---|
| R1 | A r1 ×3 (rastro, mismo commit, sin rastro) | R14 | W r14 |
| R2 | A r2 | R15 | W r15, P r15 |
| R3 | A r3 ×4 (WARNING, INFO, sin correo, vacío) | R16 | W r16 |
| R4 | A r4 ×2 + suite sv3 anterior intacta | R17 | P r17 ×2, W r17 ×2 |
| R5 | A r5 ×2, `tests/test_f010_orm_models_gemelos.py` | R18 | W r17_r18, W r18 (cola rota) |
| R6 | C r6 ×8 | R19 | P r19 ×6, W r19 |
| R7 | C r7 ×2 | R20 | P r20, W r20 |
| R8 | C r8 ×8, P r8 | R21 | P r21 ×3, W r21 |
| R9 | C r9 ×2 | R22 | C r22, P r22 ×2, W r22 ×2 |
| R10 | C r10 ×2, P r10 | R23 | P r23 ×5, W r23 ×2 |
| R11 | C r11, P r11 ×3, W r11 ×3 | R24 | P r24 |
| R12 | W r12 ×2 | R25 | W r25 ×4 |
| R13 | W r13 | R26 | W r26 ×2 |

## Cambios requeridos

1. **`progress/current.md`, sección F-084**: listar las verificaciones MANUAL (humano) M1–M3 de design §12 con
   su comando exacto (M1: `SELECT column_name FROM information_schema.columns WHERE table_name =
   'parte_documents' AND column_name LIKE 'sustituido%';` ⇒ 2 filas; M2 y M3 con la ruta y el resultado
   esperado; M3 solo con OK expreso), como hace F-082 en ese mismo fichero (C4).
2. **Documentación que ahora miente sobre `undo_log.actor`**: `docs/ARCHITECTURE.md:473-474` («que no la
   escribe nadie y sigue naciendo `NULL`…») y el docstring de `_actor` en
   `services/partes-front/interface_adapters/web/app.py:907-908` («`undo_log.actor` no participa… porque no
   la escribe nadie»). Desde F-084 `parte_recuperar` la rellena: decirlo, como ya se hizo en `azure-apps/partes.md`
   §4.5. Recomendado (no bloquea, fuera de los ficheros previstos): la cabecera de
   `services/partes-front/interface_adapters/web/identidad.py:10-16` dice lo mismo.

3. **C1**: la pasada 2 necesita `ARNES_SIN_CACHE=1 bash harness/init.sh` con exit 0 (aquí lo impidieron dos
   inestables ajenos; ver «init.sh»).

Sin cambios de código de producción. La pasada 2 será incremental desde 8f559d1.

## Observaciones (no bloquean)

1. Riesgo §10: la clave F-050 es UNA por línea (`rec-` > `emp-` > `nom-`) y sv3 usa un CONJUNTO (ide, DNI,
   nombres): la persona casada en un parte y sin casar en el otro da `rec-X` frente a `nom-…`, sin choque, y
   quedan dos activos. La mitigación de la spec («se ve en la celda») no vale ahí: salen en DOS filas. Si aparecen casos, una feature aparte que cruce también por DNI/nombre en `_choques`.
2. «Ver PDF» solo con `preview_enabled`: más estricto que R12 a la letra, coherente con Conciliar.
3. Insignia «en Sigrid» agrupa encolado, registrado y dedicación (R11 solo ofrece dos insignias).
4. `_choques`: dos líneas sin trabajador (`sin-trabajador`) chocan entre sí: falso 409 en el lado seguro.

## Automejora (propuesta, no aplicada)

- Encargo del líder al reviewer: pedir siempre `ARNES_SIN_CACHE=1 bash harness/init.sh`; sin la variable, las
  suites de servicio salen por caché del verde del implementer y C1 no se puede marcar.

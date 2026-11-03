<!-- specs/F-052-sincronizar-con-sigrid/tasks.md -->
# F-052 · Sincronizar con Sigrid — Tareas

Rama **`feature/F-052-sincronizar-con-sigrid`** (worktree `partes-wt-f052`), con `dev` 69af0f5 fusionado (0be3ef7; **F-050** y lo demás ya dentro). Spec aprobada el 2026-11-02 (`design.md` §8) y M1 hecha (§9); **punto de control obligatorio en T8**. Un commit **local** por tarea (`F-052 Tn: …`), por rutas explícitas; sin push ni PR. Rigor **crítico** (DA8): fase RED con traza en `progress/impl_F-052.md` para R1–R30, cobertura de líneas cambiadas ≥ umbral y mutación completa sin supervivientes sin test o justificación aceptada. Tests sin red, Sigrid ni PostgreSQL (httpx simulado, TestClient, SQLite); datos sintéticos, ni nombres ni DNIs. **Ninguna escritura en Sigrid** en toda la feature (R26). Python: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe`; tests de cada servicio desde su carpeta.

- [x] T1: Fusionar `dev` si avanzó desde 69af0f5 y anotar en `progress/impl_F-052.md` la clave real de persona (`rec-`) y el resultado de M1 (design §9)  |  Verificación: `git merge-base --is-ancestor dev HEAD`; M1 anotada
- [x] T2: Tests en rojo de `origen_de`, `lineas_sincronizar` (pide `SIGRID_API_MAX_ROWS`, otra página con OFFSET/FETCH solo si viene llena, página justa sin error, `truncated` ⇒ excepción, sin `tex`, columnas de R2) y `lineas_sincronizar_por_synckey` (lotes de 200) en `services/partes-transfer/tests/test_f052_leer_sincronizar.py`, y su implementación en `sigrid_write_client.py` + `LineaSincronizar` en `registro_models.py` (R1–R3, R5)  |  Verificación: `pytest tests/test_f052_leer_sincronizar.py` (sv5) en verde
- [x] T3: Tests en rojo de `POST /api/sincronizar/leer` (422 de R6, 502 de R4 también en un corte por tiempo y sin parciales, sin lock ni `/api/sql/write`) en `tests/test_f052_api_sincronizar.py`, ruta en `interface_adapters/api/app.py` y `SINCRONIZAR_MAX_REGISTRO_IDS` (3000) en `config/settings.py`  |  Verificación: `pytest tests/test_f052_api_sincronizar.py` (sv5) en verde
- [x] T4: Suite completa de sv5 y lo que no se toca (R26)  |  Verificación: `pytest -q` (sv5) en verde; `git diff dev --stat -- services/partes-transfer/application` vacío
- [x] T5: Tests en rojo de `clasificar` (las 12 clases con los ejemplos de design §3, `a_cero`, R9 con tolerancia y nota de código, R11 con los motivos de DA14, prioridad de estados), `firma` (estable ante el orden, sensible a valores) y `ACCIONES_POR_CLASE` (tabla de design §4) en `services/partes-front/tests/test_f052_clasificar.py`, y `application/services/sincronizacion.py`  |  Verificación: `pytest tests/test_f052_clasificar.py` (sv4) en verde
- [x] T6: Tests en rojo (SQLite) de `lineas_para_sincronizar` (ámbito obra y `rec-`, periodo nómina y natural, papelera fuera) y `donde_estan` (R12, también `parte_reemplazado`) en `tests/test_f052_repositorio.py`, y los métodos en `parte_repository.py`  |  Verificación: `pytest tests/test_f052_repositorio.py` (sv4) en verde
- [x] T7: Tests en rojo de `SincronizadorAmbito.sincronizar` (flujo de design §2 con dobles: R7, R10 llama a `comprobar_ids` con `forzar` y origen `sincronizar`, R13 sin parciales, R15, R29 candado) en `tests/test_f052_sincronizar_ambito.py`, y de `POST /api/sincronizar` (422 de ámbito, 503 sin `TRANSFER_BASE_URL`, R30) en `tests/test_f052_endpoints.py`; `application/services/sincronizar_ambito.py`, `transfer_client.sincronizar_leer`, ruta, `SINCRONIZAR_TIMEOUT_S` y `SINCRONIZAR_SECO` (DA18: en seco ninguna escritura en `partes` y R10 solo informa; fuera de seco, R10 como F-024)  |  Verificación: `pytest tests/test_f052_sincronizar_ambito.py tests/test_f052_endpoints.py` (sv4) en verde; sin `aplicar` todavía
- [ ] T8: **PUNTO DE CONTROL OBLIGATORIO (DA17 = B)**: parar y pedir M2 (design §9) sobre obras y personas con líneas del portal, con sv4 en modo seco (DA18); no se empieza T9 sin su resultado anotado, y si las clases no cuadran se para y se vuelve a proponer  |  Verificación: MANUAL (humano) — M2 anotada en `progress/impl_F-052.md`
- [x] T8 bis: H-M2-1 (M2 del 2026-11-03, autorizado por el humano): tests en rojo con datos de la M2 y la clase de hora de Sigrid por el prefijo `HE` de `hora_cod` (no `auxhor.ext`) en `sincronizacion.py`; luego el líder repite M2  |  Verificación: `pytest tests/test_f052_clasificar.py` (sv4) en verde; `bash harness/init.sh` en verde
- [x] T9: Tests en rojo (SQLite) de `aplicar_marcar_registrada` (R19, CAS), `aplicar_traer_de_sigrid` (R20, R21, R22; congelada por `registrado` sí, `en espera` y `ESTADOS_BLOQUEAN` descartan) y `documentos_de_los_dias` en `tests/test_f052_repositorio.py`, y los métodos en `parte_repository.py`  |  Verificación: `pytest tests/test_f052_repositorio.py` (sv4) en verde
- [ ] T10: Tests en rojo de `aplicar` (R18 firma distinta ⇒ `descartados`, R23 recálculo compartido y `fallo`) y de `POST /api/sincronizar/aplicar` (ámbito F-022 ⇒ 422, tope de ítems, actor de `_actor`), `MOTIVO_SINCRONIZAR` y `SINCRONIZAR_MAX_ITEMS_ACCION`  |  Verificación: `pytest tests/test_f052_sincronizar_ambito.py tests/test_f052_endpoints.py` (sv4) en verde
- [ ] T11: Tests en rojo de las vistas (botón en obra y persona, deshabilitado con motivo en `emp-`/`nom-`/`sin-trabajador`/obra sin ide, R15; el GET no llama a sv5, R27) en `tests/test_f052_vistas.py` y las plantillas  |  Verificación: `pytest tests/test_f052_vistas.py` (sv4) en verde; parseo Jinja2 de las dos plantillas
- [ ] T12: Tests en rojo del panel con node (filtros por clase, «todas las de esta clase», confirmación con recuento antes de llamar, `esc()` en todo lo pintado, re-sincroniza al terminar, reutiliza el modal de aprobar para `reaprobar`, R16, R17, R24, R25) en `tests/test_f052_panel_js.py`, y `static/app.js` + `static/styles.css`  |  Verificación: `pytest tests/test_f052_panel_js.py` (sv4) en verde; `node --check static/app.js`
- [ ] T13: `tests/test_f052_contrato_motivos.py` (sv3 clasifica `MOTIVO_SINCRONIZAR` como recálculo, como F-049) y guardianes intactos (R28, F-038)  |  Verificación: `pytest tests/test_f052_contrato_motivos.py tests/test_f042_contrato_recalculo.py tests/test_f024_borrado_no_congela_gemelos.py tests/test_f010_orm_models_gemelos.py tests/test_f038_lectores_sigrid.py` (raíz) en verde; `git diff dev --stat -- services/partes-front/application/services/congelacion.py services/partes-persistencia services/partes-front/infrastructure/database/orm_models.py` vacío
- [ ] T14: Suite completa de sv4  |  Verificación: `pytest -q` (sv4) en verde
- [ ] T15: `docs/ARCHITECTURE.md` (doble canal, semántica 10, semántica 22) y `azure-apps/partes.md` (endpoint de sv5, rutas y variables de sv4), commit aparte en `azure-apps`  |  Verificación: `git diff dev -- docs/ARCHITECTURE.md` revisado; `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1`
- [ ] T16: Anotar M3 y M4 (design §9) como pendientes del humano en `progress/current.md`  |  Verificación: MANUAL (humano) — M3 en la 0404 con `PRUEBA-IA` y `prueba_escritura_sigrid.py limpiar --ejecutar` al final; M4 tras desplegar sv5 → sv4
- [ ] T17: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina en verde

## Revalidación 2026-11-01 (contra `dev` 69af0f5, merge 0be3ef7)

Cambios **mecánicos** (mismo comportamiento; detalle en `progress/explore_F-052_revalidacion.md`):

- requirements (cabecera): F-050 ya está en `dev`; la rama lleva `dev` fusionado.
- R10: `comprobar_ids` se llama en proceso; `ORIGENES_COMPROBACION` de la ruta `/api/sigrid/comprobar` (sv4) no cambia.
- R15: las claves de obra sin `obra_ide` son `cod-`, `nom-` y `sin-obra` (`obra_key_for_registro`).
- R21: `_exigir_sin_recalculo` ya cubre el parte nuevo de F-047 (se nombra).
- R24: `restore_registro` responde 409 si el parte se reprocesó (F-061): vuelve como descartado.
- design §1: `ComprobacionSigrid` (sv4) llama a sv5 `/api/registro/comprobar`; `_validar_ambito` es un cierre de `app.py` que exige 1–`MAX_IDS_APROBACION` ids (solo lo usa `/aplicar`); papelera y restaurar son `borrar_linea` / `restore_registro`.
- design §1 y §2: el rango es `period_bounds(*parse_period_key(period), mode)` (la firma recibe año y mes).
- design §1 y §7: `enlazada` reutiliza `_expr_enlazada()` del cliente de sv5 (F-046/F-053), no una expresión nueva sobre `ENLACES_HMORES`.
- design §3: `anulada_en_sigrid` también la produce el pisado de F-053 (la definición no cambia).
- design §5: el guardián de lectores de F-038 no cambia (mismo fichero); T13 lo corre.
- design §5 y T13: el motivo nuevo va en `tests/test_f052_contrato_motivos.py`, como `test_f049_contrato_motivos.py`.
- design §5 y T15: la semántica nueva de `ARCHITECTURE.md` es la 22 (la 18 es F-054).
- design §5: «No se tocan» añade `franquicia_pipeline.py`, `racha_ciz.py`, `pisado.py` (sv5) y `reparto_aviso.py`, `seguimiento_recalculo.py`, `edicion_celda.py` (sv4).
- design §6: la guarda de reparto es `registros_con_reparto(ids)`; `_exigir_sin_recalculo` recibe el documento.
- design §7: lotes por synckey de `LOTE_COMPROBACION` (200).
- design §8: DA9 superada.
- design §10: H1 resuelto por F-053, H2 por F-038.
- T1: ya no hay que rebasar; solo fusionar `dev` si avanzó.

Numeración de tareas: la de la lista de arriba, tras partir T6–T8 por el punto de control.

**Aprobado por el humano el 2026-11-02** (`design.md` §8): DA1–DA8, DA10 y DA12–DA16 con la recomendación, ya aplicadas a R2, R8, R11, R12, R21, R23 y a design §3–§6; DA11 (se lee hasta el límite de la API, 500.000, y solo se pagina a partir de ahí; sin `SINCRONIZAR_MAX_LINEAS`, con cota `SINCRONIZAR_MAX_REGISTRO_IDS` = 3000) y DA17 = B (una sola feature con punto de control en T8).

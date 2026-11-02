<!-- specs/F-052-sincronizar-con-sigrid/tasks.md -->
# F-052 · Sincronizar con Sigrid — Tareas

Rama **`feature/F-052-sincronizar-con-sigrid`** (worktree `partes-wt-f052`), con `dev` 69af0f5 fusionado (0be3ef7; **F-050** y lo demás ya dentro). No se empieza sin el visto bueno del humano a las DA de `design.md` §8 ni sin M1 hecha. Un commit **local** por tarea (`F-052 Tn: …`), por rutas explícitas; sin push ni PR. Rigor **crítico** (DA8): fase RED con traza en `progress/impl_F-052.md` para R1–R30, cobertura de líneas cambiadas ≥ umbral y mutación completa sin supervivientes sin test o justificación aceptada. Tests sin red, Sigrid ni PostgreSQL (httpx simulado, TestClient, SQLite); datos sintéticos, ni nombres ni DNIs. **Ninguna escritura en Sigrid** en toda la feature (R26). Python: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe`; tests de cada servicio desde su carpeta.

- [ ] T1: Fusionar `dev` si avanzó desde 69af0f5 y anotar en `progress/impl_F-052.md` la clave real de persona (`rec-`) y el resultado de M1 (filtro de §7 y tope elegido)  |  Verificación: `git merge-base --is-ancestor dev HEAD`; M1 anotada
- [ ] T2: Tests en rojo de `origen_de`, `lineas_sincronizar` (pide `SIGRID_API_MAX_ROWS`, otra página con OFFSET/FETCH solo si viene llena, página justa sin error, `truncated` y tope ⇒ excepción, sin `tex`, columnas de R2) y `lineas_sincronizar_por_synckey` (lotes de 200) en `services/partes-transfer/tests/test_f052_leer_sincronizar.py`, y su implementación en `sigrid_write_client.py` + `LineaSincronizar` en `registro_models.py` (R1–R3, R5)  |  Verificación: `pytest tests/test_f052_leer_sincronizar.py` (sv5) en verde
- [ ] T3: Tests en rojo de `POST /api/sincronizar/leer` (422 de R6, 502 de R4, `ok: false` por tope, 502 sin parciales en un corte por tiempo, sin lock ni `/api/sql/write`) en `tests/test_f052_api_sincronizar.py`, ruta en `interface_adapters/api/app.py` y `SINCRONIZAR_MAX_LINEAS` en `config/settings.py`  |  Verificación: `pytest tests/test_f052_api_sincronizar.py` (sv5) en verde
- [ ] T4: Suite completa de sv5 y lo que no se toca (R26)  |  Verificación: `pytest -q` (sv5) en verde; `git diff dev --stat -- services/partes-transfer/application` vacío
- [ ] T5: Tests en rojo de `clasificar` (las 11 clases con los ejemplos de design §3, R9 con tolerancia y nota de código, R11, prioridad de estados), `firma` (estable ante el orden, sensible a valores) y `ACCIONES_POR_CLASE` (tabla de design §4) en `services/partes-front/tests/test_f052_clasificar.py`, y `application/services/sincronizacion.py`  |  Verificación: `pytest tests/test_f052_clasificar.py` (sv4) en verde
- [ ] T6: Tests en rojo (SQLite) de `lineas_para_sincronizar` (ámbito obra y `rec-`, periodo nómina y natural, papelera fuera), `donde_estan` (R12), `aplicar_marcar_registrada` (R19, CAS) y `aplicar_traer_de_sigrid` (R20, R21, R22; congelada por `registrado` sí, `en espera` y reparto `pendiente` descartan) en `tests/test_f052_repositorio.py`, y los métodos en `parte_repository.py`  |  Verificación: `pytest tests/test_f052_repositorio.py` (sv4) en verde
- [ ] T7: Tests en rojo de `SincronizadorAmbito` (flujo de design §2 con dobles: R7, R10 llama a `comprobar_ids` con `forzar` y origen `sincronizar`, R13 sin parciales, R15, R18 firma distinta ⇒ `descartados`, R23 recálculo y `fallo`, R29 candado) en `tests/test_f052_sincronizar_ambito.py`, `application/services/sincronizar_ambito.py`, `transfer_client.sincronizar_leer` y `MOTIVO_SINCRONIZAR`  |  Verificación: `pytest tests/test_f052_sincronizar_ambito.py` (sv4) en verde
- [ ] T8: Tests en rojo de `POST /api/sincronizar` y `/api/sincronizar/aplicar` (ámbito F-022 ⇒ 422, tope de ítems, actor de `_actor`, 503 sin `TRANSFER_BASE_URL`, R30) en `tests/test_f052_endpoints.py`, rutas y composición en `app.py` y `SINCRONIZAR_TIMEOUT_S` / `SINCRONIZAR_MAX_ITEMS_ACCION` en `config/settings.py`  |  Verificación: `pytest tests/test_f052_endpoints.py` (sv4) en verde
- [ ] T9: Tests en rojo de las vistas (botón en obra y persona, deshabilitado con motivo en `emp-`/`nom-`/`sin-trabajador`/obra sin ide, R15; el GET no llama a sv5, R27) en `tests/test_f052_vistas.py` y las plantillas  |  Verificación: `pytest tests/test_f052_vistas.py` (sv4) en verde; parseo Jinja2 de las dos plantillas
- [ ] T10: Tests en rojo del panel con node (filtros por clase, «todas las de esta clase», confirmación con recuento antes de llamar, `esc()` en todo lo pintado, re-sincroniza al terminar, reutiliza el modal de aprobar para `reaprobar`, R16, R17, R24, R25) en `tests/test_f052_panel_js.py`, y `static/app.js` + `static/styles.css`  |  Verificación: `pytest tests/test_f052_panel_js.py` (sv4) en verde; `node --check static/app.js`
- [ ] T11: `tests/test_f052_contrato_motivos.py` (sv3 clasifica `MOTIVO_SINCRONIZAR` como recálculo, como F-049) y guardianes intactos (R28, F-038)  |  Verificación: `pytest tests/test_f052_contrato_motivos.py tests/test_f042_contrato_recalculo.py tests/test_f024_borrado_no_congela_gemelos.py tests/test_f010_orm_models_gemelos.py tests/test_f038_lectores_sigrid.py` (raíz) en verde; `git diff dev --stat -- services/partes-front/application/services/congelacion.py services/partes-persistencia services/partes-front/infrastructure/database/orm_models.py` vacío
- [ ] T12: Suite completa de sv4  |  Verificación: `pytest -q` (sv4) en verde
- [ ] T13: `docs/ARCHITECTURE.md` (doble canal, semántica 10, semántica 22) y `azure-apps/partes.md` (endpoint de sv5, rutas y variables de sv4), commit aparte en `azure-apps`  |  Verificación: `git diff dev -- docs/ARCHITECTURE.md` revisado; `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1`
- [ ] T14: Anotar M2–M4 (design §9) como pendientes del humano en `progress/current.md`  |  Verificación: MANUAL (humano) — M2 sincronizar 2 obras y 2 personas reales sin aplicar; M3 en la 0404 con `PRUEBA-IA` y `prueba_escritura_sigrid.py limpiar --ejecutar` al final; M4 tras desplegar sv5 → sv4
- [ ] T15: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh` termina en verde

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
- design §5: el guardián de lectores de F-038 no cambia (mismo fichero); T11 lo corre.
- design §5 y T11: el motivo nuevo va en `tests/test_f052_contrato_motivos.py`, como `test_f049_contrato_motivos.py`.
- design §5 y T13: la semántica nueva de `ARCHITECTURE.md` es la 22 (la 18 es F-054).
- design §5: «No se tocan» añade `franquicia_pipeline.py`, `racha_ciz.py`, `pisado.py` (sv5) y `reparto_aviso.py`, `seguimiento_recalculo.py`, `edicion_celda.py` (sv4).
- design §6: la guarda de reparto es `registros_con_reparto(ids)`; `_exigir_sin_recalculo` recibe el documento.
- design §7: lotes por synckey de `LOTE_COMPROBACION` (200).
- design §8: DA9 superada.
- design §10: H1 resuelto por F-053, H2 por F-038.
- T1: ya no hay que rebasar; solo fusionar `dev` si avanzó.

**Decisiones abiertas nuevas** (`design.md` §8): DA12 synckeys de CIZ hermano y franquicia, DA13 líneas a 0 fuera del portal, DA14 `omitido` según motivo, DA15 recálculo y repartos de `traer_de_sigrid`, DA16 parte reemplazado.

**Decididas por el humano el 2026-11-02**: DA11 (se lee hasta el límite de la API, 500.000, y solo se pagina a partir de ahí; R3, R4, design §5 y §7, T2 y T3) y DA17 (una sola feature, sin corte obligatorio). Pendiente: `SINCRONIZAR_MAX_LINEAS`.

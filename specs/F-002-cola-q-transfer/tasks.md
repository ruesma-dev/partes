<!-- specs/F-002-cola-q-transfer/tasks.md -->
# F-002 · Cola q-transfer — Tareas

Cada tarea = un commit `F-002 Tn: ...`. Tests junto a la implementación;
todos sin red ni BBDD (fakes; SQLite en memoria en el repositorio de sv4).

- [ ] T1: sv5 — adaptadores `infrastructure/azure/` (`cola_cliente.py`,
      `blob_cliente.py`, `credenciales.py`, adaptación del patrón sv3) +
      `services/partes-transfer/tests/` con `test_f002_cola_cliente.py`
      (poison tras `max_dequeue`, no-borrado en fallo, envío JSON) usando
      fakes de QueueClient.
      | Verificación: `python -m pytest services/partes-transfer/tests -q`

- [ ] T2: sv5 — `config/settings.py` con las claves de storage opcionales;
      `build_app(settings, pipeline=None, lock=None)` retrocompatible con
      lock en `ejecutar` (R7 parcial).
      | Verificación: `test_f002_r7_ejecutar_usa_lock` y
      `test_f002_build_app_sin_pipeline_inyectado` (fakes)

- [ ] T3: sv5 — `interface_adapters/queue/transfer_consumer.py`: handler
      que descarga petición, ejecuta pipeline bajo lock y publica resultado
      (blob + mensaje) — R6, R7, R10, R14 (resultado `ok=false` publicado y
      mensaje consumido); fallo de infraestructura relanza (R9).
      | Verificación: `test_f002_r6_...`, `test_f002_r7_...`,
      `test_f002_r10_conflictos_sin_pisar`, `test_f002_r14_error_global`,
      `test_f002_r9_fallo_infra_relanza` con fakes de blob/cola/pipeline

- [ ] T4: sv5 — `main.py`: composición (pipeline + lock compartido, hilo
      consumidor daemon si hay storage; sin storage arranca como hoy).
      Nota R8: la idempotencia por synckey ya la da el pipeline actual; se
      cubre con `test_f002_r8_reentrega_no_duplica` (pipeline fake que
      simula segunda pasada → `ya_registradas`).
      | Verificación: `python -m pytest services/partes-transfer/tests -q`

- [ ] T5: sv4 — adaptadores `infrastructure/azure/` (mismos tres ficheros,
      adaptación sv3) sin tests nuevos propios (cubiertos por T6/T8 vía
      fakes; la lógica de cola ya se testea en T1).
      | Verificación: `python -m pytest services/partes-front/tests -q`
      (la suite existente sigue en verde)

- [ ] T6: sv4 — `TransferQueuePublisher` +
      `parte_repository.marcar_registros_encolado` + extensión de
      `marcar_registros_sigrid` (conflictos, error_global) — R1 (blob +
      mensaje), R2, R12, R13, R14 (marcado).
      | Verificación: `test_f002_r1_publica_blob_y_mensaje`,
      `test_f002_r2_marca_encolado`, `test_f002_r12_marca_resultados`,
      `test_f002_r13_marcado_idempotente`, `test_f002_r14_error_global`
      (SQLite en memoria + fakes)

- [ ] T7: sv4 — endpoint `POST /api/aprobar/encolar` con fallback síncrono
      y rechazo de `pisar_claves` — R1, R3, R5 (el pisado NO pasa por la
      cola); `/api/aprobar/preflight` y `/api/aprobar/ejecutar` intactos
      (R4, R5).
      | Verificación: `test_f002_r1_encolar_responde_asincrono`,
      `test_f002_r3_fallback_sincrono`,
      `test_f002_r5_pisar_claves_rechazado`,
      `test_f002_r4_preflight_intacto` (TestClient + dobles)

- [ ] T8: sv4 — `resultado_consumer` + arranque del hilo daemon en
      `main.py` — R12 aplicado desde mensaje (descarga blob de resultado →
      repositorio).
      | Verificación: `test_f002_r12_consumer_actualiza_sigrid` con fakes
      de blob/cola y SQLite en memoria

- [ ] T9: sv4 — `static/app.js`: modal (encolar sin conflictos; pisar
      sigue síncrono; mensaje «encolado») y badges de
      `encolado`/`conflicto`/`error` — R15.
      | Verificación: `node --check services/partes-front/static/app.js` +
      MANUAL (humano): en local, aprobar un parte y ver el badge tras
      recargar

- [ ] T10: infra — `infra/add_qtransfer_partes.ps1` (colas + `-poison` +
      contenedor `transfer`, idempotente; PS 5.1, sin BOM, CRLF) con los
      `az containerapp update` de variables documentados dentro — R17, R16
      (no toca la escala de sv5).
      | Verificación: MANUAL (humano): ejecutar el script contra
      `rg-partes-dev` y comprobar
      `az storage queue list --account-name stpartespt7m3 --auth-mode login`

- [ ] T11: docs — actualizar `docs/ARCHITECTURE.md` (comunicación sv4↔sv5:
      colas + HTTP) y el documento `partes` de `azure-apps/` (colas y
      contenedor nuevos), en este mismo trabajo.
      | Verificación: revisión del diff por el reviewer (rigor critico)

- [ ] T12: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: `bash harness/init.sh`

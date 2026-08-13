<!-- specs/F-002-cola-q-transfer/tasks.md -->
# F-002 · Cola q-transfer — Tareas

Cada tarea = un commit `F-002 Tn: ...`. Tests junto a la implementación;
todos sin red ni BBDD (fakes; SQLite en memoria en el repositorio de sv4).

Nota de la ampliación (2026-08-13): renumeradas T2+ para que el split del
pipeline (ampliación 1) preceda al consumidor; añadidas T11–T12
(ampliación 2). La numeración es consistente con requirements y design.

- [ ] T1: sv5 — adaptadores `infrastructure/azure/` (`cola_cliente.py`,
      `blob_cliente.py`, `credenciales.py`, adaptación del patrón sv3) +
      `services/partes-transfer/tests/` con `test_f002_cola_cliente.py`
      (poison tras `max_dequeue`, no-borrado en fallo, envío JSON) usando
      fakes de QueueClient.
      | Verificación: `python -m pytest services/partes-transfer/tests -q`

- [ ] T2: sv5 — split del pipeline en fases (ampliación 1):
      `ContextoRegistro` en `domain/models/registro_models.py`;
      `preparar` (pasos 1–4) / `_evaluar` (pasos 5–7) / `registrar`
      (lock + pasos 5–9) en `registro_pipeline.py`, lock en el
      constructor; `preflight` y `ejecutar` recompuestos con firma y
      comportamiento idénticos; `reglas_registro.py` intacto — R7, R19,
      R20.
      | Verificación: `test_f002_r19_registrar_serializa` (fakes con
      latencia), `test_f002_r20_estado_bajo_lock` (dos peticiones a la
      misma obra+mes ⇒ UN parte y UN correlativo),
      `test_f002_regresion_ejecutar_equivalente` (mismo resultado que el
      pipeline previo con cliente fake)

- [ ] T3: sv5 — `config/settings.py` con las claves de storage opcionales
      (incluye `transfer_workers`, default 3, mínimo 1);
      `build_app(settings, pipeline=None)` retrocompatible SIN lock
      explícito en los endpoints (R7 lo garantiza `registrar` desde T2).
      | Verificación: `test_f002_r7_ejecutar_usa_lock` (el endpoint
      serializa vía pipeline) y
      `test_f002_build_app_sin_pipeline_inyectado` (fakes)

- [ ] T4: sv5 — `interface_adapters/queue/transfer_consumer.py`: handler
      que descarga petición, ejecuta `preparar` (fuera del lock) +
      `registrar` (el lock lo adquiere el pipeline) y publica resultado
      (blob + mensaje) — R6, R7, R10, R14 (resultado `ok=false` publicado
      y mensaje consumido); fallo de infraestructura relanza (R9).
      | Verificación: `test_f002_r6_...`, `test_f002_r7_...`,
      `test_f002_r10_conflictos_sin_pisar`, `test_f002_r14_error_global`,
      `test_f002_r9_fallo_infra_relanza` con fakes de blob/cola/pipeline

- [ ] T5: sv5 — `main.py`: composición (lock único + pipeline compartido,
      `TRANSFER_WORKERS` hilos consumidores daemon —cada uno con sus
      propias instancias de clientes— si hay storage; sin storage arranca
      como hoy) — R18, R21, R22.
      Nota R8: la idempotencia por synckey ya la da el pipeline actual; se
      cubre con `test_f002_r8_reentrega_no_duplica` (pipeline fake que
      simula segunda pasada → `ya_registradas`).
      | Verificación: `test_f002_r18_preparacion_solapa` (fakes con
      latencia: dos preparaciones concurrentes tardan menos que en
      serie), `test_f002_r21_orden_no_garantizado` (la petición lenta en
      preparar publica después que la rápida),
      `test_f002_r22_fallo_no_afecta_al_resto`,
      `test_f002_r8_reentrega_no_duplica`;
      `python -m pytest services/partes-transfer/tests -q`

- [ ] T6: sv4 — adaptadores `infrastructure/azure/` (mismos tres ficheros,
      adaptación sv3) sin tests nuevos propios (cubiertos por T7/T9/T11
      vía fakes; la lógica de cola ya se testea en T1).
      | Verificación: `python -m pytest services/partes-front/tests -q`
      (la suite existente sigue en verde)

- [ ] T7: sv4 — `TransferQueuePublisher` +
      `parte_repository.marcar_registros_encolado` + extensión de
      `marcar_registros_sigrid` (conflictos, error_global) — R1 (blob +
      mensaje), R2, R12, R13, R14 (marcado).
      | Verificación: `test_f002_r1_publica_blob_y_mensaje`,
      `test_f002_r2_marca_encolado`, `test_f002_r12_marca_resultados`,
      `test_f002_r13_marcado_idempotente`, `test_f002_r14_error_global`
      (SQLite en memoria + fakes)

- [ ] T8: sv4 — endpoint `POST /api/aprobar/encolar` con fallback síncrono
      y rechazo de `pisar_claves` — R1, R3, R5 (el pisado NO pasa por la
      cola); `/api/aprobar/preflight` y `/api/aprobar/ejecutar` intactos
      (R4, R5).
      | Verificación: `test_f002_r1_encolar_responde_asincrono`,
      `test_f002_r3_fallback_sincrono`,
      `test_f002_r5_pisar_claves_rechazado`,
      `test_f002_r4_preflight_intacto` (TestClient + dobles)

- [ ] T9: sv4 — `resultado_consumer` + arranque del hilo daemon en
      `main.py` — R12 aplicado desde mensaje (descarga blob de resultado →
      repositorio).
      | Verificación: `test_f002_r12_consumer_actualiza_sigrid` con fakes
      de blob/cola y SQLite en memoria

- [ ] T10: sv4 — `static/app.js`: modal (encolar sin conflictos; pisar
      sigue síncrono; mensaje «encolado») y badges de
      `encolado`/`conflicto`/`error` — R15.
      | Verificación: `node --check services/partes-front/static/app.js` +
      MANUAL (humano): en local, aprobar un parte y ver el badge tras
      recargar

- [ ] T11: sv4 — gestión de poison, backend (ampliación 2):
      `cola_cliente.contar_aproximado` y `cola_cliente.mover` (send a la
      principal ANTES de borrar de la poison, tope 32, log de id y
      contenido) + endpoints `GET /api/admin/poison` y
      `POST /api/admin/poison/reencolar` (allowlist de dos colas) —
      R23, R24, R25, R26.
      | Verificación: `test_f002_r23_contador_poison`,
      `test_f002_r24_reencola_max_32`,
      `test_f002_r25_borra_solo_tras_encolar` (el fake falla el delete y
      el mensaje sigue en ambas colas, nunca perdido),
      `test_f002_r26_deshabilitado_sin_colas` (TestClient + fakes de
      QueueClient)

- [ ] T12: sv4 — gestión de poison, UI (ampliación 2): aviso con recuento
      en la cabecera común (`templates/base.html` + `static/app.js`,
      consulta al cargar la página, sin polling continuo) y botón
      «Reencolar (máx. 32)» — R23, R24 (parte visual).
      | Verificación: `node --check services/partes-front/static/app.js` +
      MANUAL (humano): con Azurite y un mensaje en
      `q-transfer-poison`, ver el aviso y reencolarlo desde el portal

- [ ] T13: infra — `infra/add_qtransfer_partes.ps1` (colas + `-poison` +
      contenedor `transfer`, idempotente; PS 5.1, sin BOM, CRLF) con los
      `az containerapp update` de variables documentados dentro (incluye
      `TRANSFER_WORKERS` en sv5) — R17, R16 (no toca la escala de sv5).
      | Verificación: MANUAL (humano): ejecutar el script contra
      `rg-partes-dev` y comprobar
      `az storage queue list --account-name stpartespt7m3 --auth-mode login`

- [ ] T14: docs — actualizar `docs/ARCHITECTURE.md` (comunicación sv4↔sv5:
      colas + HTTP; workers paralelos con escritura serializada en sv5;
      gestión de poison desde el portal) y el documento `partes` de
      `azure-apps/` (colas y contenedor nuevos), en este mismo trabajo.
      | Verificación: revisión del diff por el reviewer (rigor critico)

- [ ] T15: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: `bash harness/init.sh`

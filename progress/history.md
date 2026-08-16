<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-001 · Test de estructura del monorepo (calentamiento) — done 2026-08-13

- Rama `feature/F-001-test-estructura` · rigor estandar · sdd=false ·
  APPROVED del reviewer (`progress/review_F-001.md`).
- Entregado: `tests/conftest.py` y `tests/test_estructura_monorepo.py`
  (6 tests `test_f001_r*` que validan `harness/servicios.json` contra el
  árbol real reutilizando `harness/servicios.py`; R2 con declaración falsa
  en `tmp_path` + 2 tests de control).
- Verificado: init.sh en verde (exit 0, reproducido por el reviewer),
  6/6 tests, ruff limpio en lo nuevo, fase RED con 3 roturas en copia
  aislada (reproducidas de forma independiente por el reviewer), cobertura
  N/A con motivo impreso, mutación 0/0 con prueba de control (9 mutantes al
  ignorar la exclusión ⇒ generador vivo, cero legítimo).
- Observaciones no bloqueantes del reviewer: (1) el test admite
  `pyproject.toml` como punto de entrada alternativo, algo más laxo que
  ARCHITECTURE.md — si un servicio se empaqueta, actualizar doc y test a la
  vez; (2) los 6 AVISOS de servicios sin tests siguen ahí y merecen feature
  propia; (3) propuesta de automejora: añadir a C4 bis de CHECKPOINTS.md la
  prueba de control del cero de mutación (si se acepta, portar a arnes-base
  en el mismo trabajo). Pendiente de decisión del humano.
- Circuito completo del arnés (líder → implementer → reviewer → cierre)
  validado por primera vez en este repositorio.

## F-002 · Cola q-transfer para aprobación asíncrona — done 2026-08-13

- Rama `feature/F-002-cola-q-transfer` (HEAD APPROVED `63b1afe`) · rigor
  critico · sdd=true · spec R1–R26 / T1–T15 aprobada por el humano con dos
  ampliaciones suyas (preparación en paralelo con escritura serializada;
  gestión de poison desde el portal) · 1 ciclo de review.
- Entregado: doble canal sv4↔sv5 (colas `q-transfer`/`q-transfer-result`
  con hand-off por blob en el contenedor `transfer`; HTTP síncrono solo
  para preflight y pisado), split preparar/registrar del pipeline de sv5
  con `TRANSFER_WORKERS=3` y lock inyectado (escritura 1 a 1), endpoint
  `POST /api/aprobar/encolar` con fallback síncrono, consumidor de
  resultados en sv4, estados `encolado`/`conflicto`/`error` sin cambio de
  schema, aviso + reencolado manual de poison en el portal
  (send-antes-de-delete, allowlist), `infra/add_qtransfer_partes.ps1`
  (auth-mode login, sin clave), suite nueva de sv4 (112 tests) y ampliada
  de sv5 (84 + guardián R11), docs y `azure-apps/partes.md` (commit local
  `1440598` + fix posterior en azure-apps).
- Verificado (reviewer, de forma independiente): init.sh verde ×2,
  202 tests, cobertura líneas cambiadas 97,4 % (umbral 80), mutación
  132/0 con muestreo de 19 mutantes, fase RED reproducida (lock
  decorativo ⇒ 3 cabeceras duplicadas PT26/00001 — el daño que la feature
  evita), arranque simulado de la imagen sin `.venv` (el bloqueante de la
  1.ª pasada, corregido declarando azure-* en los manifiestos de sv4/sv5).
- CHANGES_REQUESTED de la 1.ª pasada: paquetes azure-* ausentes de los
  manifiestos (crash-loop en el próximo deploy). Corregido + 2 mejoras del
  reviewer aplicadas. Lección: la suite corre contra el .venv de la raíz,
  el contenedor instala manifests/svN/requirements.txt.
- MANUAL pendiente del humano (comandos exactos en el resumen de cierre y
  en `progress/impl_F-002.md`): ejecutar `add_qtransfer_partes.ps1`,
  verificar colas y escala 1/1 de sv5, badges y poison en navegador,
  redeploy (orden sv5 antes que sv4), merge a dev y push (rama y commits
  de azure-apps).
- Automejoras del arnés propuestas por el reviewer, PENDIENTES de decisión
  del humano: (1) C4 bis — exigir evidencia alternativa cuando un fichero
  del alcance con >N líneas genere 0 mutantes; (2) C3/C4 o init.sh —
  cruzar imports nuevos de terceros contra el requirements del manifiesto
  del servicio. Ambas portables a arnes-base si se aprueban.

## F-003 · Integración sesame-api: festivos y jornada reales — done 2026-08-16

- Rama `feature/F-003-sesame-festivos-jornada` · rigor critico · sdd=true ·
  spec aprobada por el humano con enmienda suya (resiliencia en DOS
  niveles) · 1 ciclo de review · APPROVED en segunda pasada.
- Entregado (APAGADO por defecto, `sesame_enabled=false` = comportamiento
  actual): clientes Sesame gemelos en sv3/sv4 (duplicación tolerada
  AMPLIADA en CLAUDE.md, redacción firmada por el humano el 2026-08-16),
  proveedor con caché DNI×año y stale-while-error, resolutor único de
  jornada (regla candef desduplicada de 4 sitios), festivos por calendario
  del trabajador en avisos/matriz/+Nuevo, aviso festivo/domingo en
  preflight, endpoint GET /api/calendario, y el régimen de resiliencia:
  vistas degradadas con aviso visible; registro BLOQUEADO con Sesame
  activado-pero-caído, override forzar_sin_sesame solo por /ejecutar con
  marca [SIN-SESAME] en sigrid_motivo, y review_required en sv3. CERO
  cambios de schema. Se inaugura la suite de sv3.
- Verificado (reviewer, independiente): init.sh verde, **373 tests**
  (6 raíz + 95 sv3 NUEVOS + 272 sv4, +144), cobertura líneas cambiadas
  **94,5 %** (umbral 80), mutación **211 mutantes / 25 supervivientes,
  todos analizados como equivalentes** (de 57 iniciales: la campaña forzó
  refuerzo real de la suite), fase RED de la enmienda reproducida.
- Hallazgos externos de la feature: sesame-api NO desplegado y sin
  commitear (P2), su /jornada sin horas (P1), sin doc en azure-apps (P3) —
  peticiones al proyecto sesame-api, del humano. F-010 (orm_models
  desincronizado) al backlog. IP de Sigrid redactada en azure-apps
  (deuda previa, commit fe4e977 de ese repo).
- ENCENDIDO futuro (tras P2): variables SESAME_* en sv3 y sv4 A LA VEZ +
  secreto sesame-api-key en kv-partes. OJO: encender contra URL muerta
  bloquea las aprobaciones (por diseño, decisión del humano).
- MANUAL pendiente del humano: merge a dev y push; verificación visual de
  los avisos (R17) cuando se encienda.

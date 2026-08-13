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

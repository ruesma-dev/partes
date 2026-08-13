<!-- progress/current.md -->
# Trabajo en curso

## F-002 · Cola q-transfer para aprobación asíncrona

- Estado: `pending`, spec en redacción · rama `feature/F-002-cola-q-transfer`
  · rigor critico · sdd=true.
- Spec-author lanzado el 2026-08-13. Al terminar: feature a `spec_ready` y
  PARADA obligatoria — la spec la aprueba el humano antes de implementar.

### Spec escrita (2026-08-13, spec-author)

`specs/F-002-cola-q-transfer/` — requirements (R1–R17), design y tasks
(T1–T12). Decisión central del design: el resultado por línea vuelve a las
columnas `sigrid_*` por una **cola de respuesta `q-transfer-result`**
consumida por un hilo de sv4 (descartadas: sv5→PostgreSQL —tercera copia de
orm_models, prohibida—, polling con job id, webhook sv5→sv4 —Easy Auth—).
Hand-off por blob (contenedor `transfer`) porque una obra×mes supera los
64 KB de mensaje. sv5 consume en un hilo del MISMO proceso que su API
(min=1/max=1, lock de proceso; **sin KEDA**). Pisar conflictos y preflight
siguen por HTTP síncrono. Sin cambios de schema (estados nuevos
`encolado`/`conflicto`/`error` en la columna existente).

**Decisiones del humano (2026-08-13, revisión conjunta de la spec):**

1. Fallback síncrono (R3): ACEPTADO tal cual.
2. Poison: AMPLIAR — gestión desde el portal (contador/aviso de las colas
   `-poison` + reencolado manual desde la UI).
3. Topología sv5: ACEPTADA (API + consumidor en un proceso, sin KEDA), pero
   AMPLIAR con preparación en paralelo (N hilos en fase-lectura; fase de
   escritura serializada bajo el lock — MAX(ide)+1 intocable).
4. T10/T11 (infra + azure-apps) como MANUAL: aceptado.
5. Spec APROBADA con esas dos ampliaciones; tras integrarlas el spec-author,
   se pasa directamente a implementación (aprobación ya dada).

Spec-author relanzado para integrar las ampliaciones 1 y 2. Aviso dado: si
el corte lectura/escritura del pipeline deja poco que paralelizar (la
cabecera hmo asigna ides ⇒ fase escritura), debe decirlo en el design con
la ganancia estimada, no forzar el diseño.

### Ampliaciones integradas (2026-08-13, spec-author)

Spec ampliada: requirements R18–R26, design con dos secciones nuevas y
tasks renumeradas a T1–T15 (T2 nuevo = split del pipeline; T11–T12 nuevas
= poison; la última sigue siendo init.sh en verde).

- **Ampliación 1** (R18–R22): corte del pipeline estudiado sobre
  `registro_pipeline.py` — `preparar` = pasos 1–4 (obra, DNI→recurso,
  reshor, reglas: datos maestros que sv5 nunca escribe, paralelizables);
  `registrar` = pasos 5–9 BAJO lock, porque los pasos 5–7 (parte hmo +
  correlativo PT, synckeys, conflictos) leen estado que la propia
  escritura modifica: evaluarlos en paralelo duplicaría correlativos y
  horas. El lock pasa al constructor del pipeline y lo adquiere
  `registrar` (ningún llamante puede olvidarlo); `preflight`/`ejecutar`
  conservan firma. `reglas_registro.py` intacto. **Ganancia estimada con
  honestidad en el design**: fracción serializada ~50–70 % ⇒ con
  `TRANSFER_WORKERS=3` el throughput mejora ×1,4–×2, no ×3 (reshor es lo
  que más crece con el lote; el lock sigue siendo el cuello).
- **Ampliación 2** (R23–R26): aviso con recuento aproximado de
  `q-transfer-poison`/`q-transfer-result-poison` en la cabecera del
  portal + reencolado manual (≤32 por clic, allowlist de dos colas, send
  antes de delete ⇒ nunca se pierde un mensaje, duplicado benigno por
  synckey; log de lo movido).

**Decisiones cerradas por el humano (2026-08-13, segunda ronda):**

1. Paralelismo: MANTENER — confirmado explícitamente que la escritura en
   Sigrid va de una en una (lock) y el paralelo cubre solo la preparación.
2. Reencolado de poison: basta usuario autenticado DE MOMENTO; se añade
   F-008 (modelo de roles en el portal) al backlog para restringirlo.

Spec definitivamente aprobada (R1–R26, T1–T15). F-002 → in_progress;
implementer lanzado. Tareas MANUAL del humano: ejecutar
`infra/add_qtransfer_partes.ps1` y los `az containerapp update`.

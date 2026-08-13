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

**Decisiones abiertas que debe validar el humano:**

1. Fallback síncrono (R3): sin `COLAS_*` configuradas, `/api/aprobar/encolar`
   ejecuta por HTTP como hoy. ¿Se acepta ese doble comportamiento, o se
   prefiere fallar en claro cuando no haya colas?
2. Poison sin reencolado automático: las líneas quedan en `encolado` y el
   humano reaprueba (seguro por synckey). ¿Suficiente para rigor critico, o
   se quiere alarma/gestión de `-poison` dentro de esta feature?
3. sv5 con hilo consumidor en el mismo contenedor que la API (en vez de un
   worker KEDA aparte, imposible con maxReplicas=1 útil). Confirmar que se
   asume ese diseño «API + worker en un proceso».
4. T10/T11 tocan infra y `azure-apps/` — la ejecución del script y los
   `az containerapp update` son MANUAL (humano).

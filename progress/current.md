<!-- progress/current.md -->
# Trabajo en curso

Limpiado el 2026-11-16: las secciones anteriores (2026-08-19 a 2026-11-15) están archivadas
tal cual al final de `progress/history.md` («Archivado de current.md · 2026-11-16»).

Ninguna feature activa (`in_progress`, `in_review` ni `human_review`).

## Abierto fuera del código (2026-11-16)

- **Verificaciones manuales** (líder, por lectura, 2026-11-16 ⇒ `progress/verificacion_manuales_2026-11-16.md`):
  OK F-047 M1 (por indicios), F-050 M2–M3, F-062 M6, F-055 M3. **Del humano**: F-068 M1 (falta un
  casado real), F-064 M2 (dos usuarios en el mismo navegador), F-046 M6 (pulsar «Aplicar»; el caso
  del 14/10 ya no existe; queda una fila `pendiente` en `reparto_pendiente`, recurso 2636243, 09/10).
  Hallazgo: la espera real de F-047 es 41–87 s (mediana 56 s), no 20–40 s: revisar el texto de R19.
- **Obra 0721, adjunto 4936_001.pdf**: reactivar la página 7 (doc 9d453e26) solo después de que
  Administración pase la página 11 al 29/10 (autorización del humano, escritura puntual).
- **Posible bug**: deshacer un cambio de fecha deja líneas con `fecha_int` NULL (doc 5ea328f7).
  En investigación ⇒ `progress/explore_bug_deshacer_fecha.md`.
- Las verificaciones manuales de F-020 a F-045 (septiembre–octubre) se dan por superadas por
  uso en producción (decisión del humano 2026-11-16).

## Siguiente en el backlog

F-072 (prioridad 1, sin spec) · F-057 (`spec_ready` desde 2026-10-24: refrescar contra F-068
antes de implementar) · F-070, F-071, F-073, F-067 sin spec · F-074 (consulta de obra de sv2,
prioridad la más baja).

## F-032 · spec rehecha (2026-11-17, spec-author)

Rama `feature/F-032-sesame-festivos-produccion`. Spec rehecha con el diseño del humano
(festivos guardados en `festivos_trabajador`, Sesame solo al ingerir; DA11 retirada).
Para validar con el humano: DA17 (bloqueo sin fila y encendido escalonado sv3 → sv4),
DA18 (interruptor de sv4), DA19 (fila `*` como respaldo común: cambia el «sin fila ⇒ JSON»
de DA15) y DA20 (cascada gemela en la lista cerrada). Resumen ⇒ `progress/spec_F-032.md`.

## F-032 · implementación en curso (implementer, 2026-11-17)

Rama `feature/F-032-sesame-festivos-produccion`, feature `in_progress`. Tareas por orden, un
commit por tarea. Informe final ⇒ `progress/impl_F-032.md`.

Decisiones y desviaciones (justificadas):

- **T12, `grep SesameCalendarioLaboral` no queda vacío del todo**: queda una mención en el
  docstring de `infrastructure/calendario/json_calendario_laboral.py` (línea 13), fichero que
  design §6 prohíbe tocar. Se respeta §6 (solo es texto); igual con la mención a
  `sesame_calendario_laboral.py` del docstring de `sesame_api_client.py` (§6).
- **T12, tests del cliente de sv3 conservados**: `test_f003_r8_sesame_calendario.py` se retira
  (R17), pero sus tres tests del `SesameApiClient` (contrato real, inmutables, gemelo con sv4)
  se trasladan tal cual a `tests/test_f032_cliente_sesame.py`, con el refresco sobre el cliente
  real: el cliente sigue en uso y no debe quedarse sin cubrir. `transporte_json`,
  `fixtures_sesame.py` y `CalendarioFake(degradados=…)` siguen sirviendo a otros tests (el
  conciliador conserva su duck-typing de `consumir_degradacion`, que no cambia): de
  `tests/dobles.py` solo cambia un docstring.
- `construir_calendario(settings, repositorio)` con Sesame y sin repositorio lanza
  `ValueError` (arranque); `construir_casado_sigrid` gana `calendario=` opcional para que el
  conciliador y el refresco compartan el mismo calendario (la caché que `olvidar` invalida).
- `services/partes-persistencia/.env.example` (no versionado, gitignored) actualizado en local:
  fuera `SESAME_CACHE_TTL_S`, dentro `SESAME_FESTIVOS_MINIMOS=1`.

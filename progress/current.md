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

## F-032 · BLOQUEADA en T17 (implementer, 2026-11-17)

**Motivo.** La regla de tasks.md dice: «Tests existentes que cambian: solo los de T1, T11, T12,
T14, T16, T18 y T20; si cae otro, PARAR». Con T17 hecho tal como manda design §5.10, la suite
completa de sv4 da `5 failed, 3870 passed`. Tres son los rojos esperados de T18
(`test_f032_avisos.py` ×2 y `test_f003_r22_la_vista_trabajador_avisa_si_la_resolucion_degrado`,
que pasan en T19). Los otros **dos no están en la lista**:

1. `tests/test_f047_portal_parte_nuevo.py::test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable`.
   Cuenta las funciones con nombre de `static/app.js` (`== 302` fuera de F-052/F-068). §5.10
   retira `bloqueoSesameHtml`, así que ahora salen 301. Es consecuencia directa de la spec.
   **Propuesta:** bajar el número a 301, con un comentario «F-032 (§5.10) retira
   `bloqueoSesameHtml`».
2. `tests/test_f056_vista.py::test_f056_r45_r6_decidir_ajustar_sin_calendario_es_409`.
   `POST /api/franquicia/decidir` con `CalendarioNoFiable` esperaba un 409 «dia de ajuste».
   R23 (el día de ajuste se calcula aunque el calendario no sea fiable) quita la guarda
   `fiable_para` de `_dia_ajuste`. Es la misma regla que ya cambian a propósito
   `test_f056_decisiones.py::test_f056_r6_*`, pero entra por otro endpoint que la lista no
   recoge. **Propuesta:** reescribirlo como en `test_f056_decisiones`: con calendario no fiable,
   «Ajustar» se decide (200) con el día del calendario resuelto.

No he improvisado: los dos tests siguen como estaban. Decide el líder (o el humano) si se amplía
la lista de T16 con estos dos y con qué contenido.

**Estado de la rama.** Commits por tarea: T1–T18 y T22–T24 hechos y marcados `[x]` en
tasks.md. HEAD = `05712b9` (T24 en rojo, a la espera de T25). Resultados:
- Suite de sv4 tras T15: `3867 passed`.
- Tras T17: los 5 fallos de arriba.
- `test_f032_contraste.py` (sv3): `22 passed`.
- Las trazas RED están guardadas en el scratchpad de la sesión (`red_T1…T24.txt`) y pasarán
  a `progress/impl_F-032.md` al cerrar.

**Pendiente.** T19 (textos de las plantillas), T20–T21 (rejilla de obra por persona), T25
(`add_sesame_partes.ps1`, el bloque de `create_capps_partes.ps1` y `00_vars_partes.ps1`), T26
(docs, CLAUDE.md, `azure-apps`), T27 (cobertura y mutación), T28–T30 (manuales, del humano),
T31 y el informe `impl_F-032.md`.

**Desviaciones a revisar por el líder:**
- **El texto de `aviso_sesame` ya está escrito.** Es `AVISO_SESAME` en `web/app.py` y lleva
  «Sin calendario de Sesame». Por eso `test_f032_r25_aviso_sesame_del_preflight` ya pasa en
  T18; a T19 solo le quedan las plantillas.
- **`test_f003_r25_la_marca_se_ve_en_las_vistas`.** La lista de T16 lo deja fuera de los que
  cambian. Aun así, si no se toca se pone en rojo (nada nuevo se marca). Lo he adaptado para que
  siembre la marca directamente (R24); conserva su intención.
- **`test_f022_aprobar_seleccion.py` ya no manda `forzar_sin_sesame`.** Así queda vacío el
  grep de verificación de T17. El caso «se ignora» lo cubre `test_f032_sin_bloqueo.py`.
- **CSS muerto en `static/styles.css`.** Quedan las reglas `.ap-sesame-bloqueo` y `.ap-forzar`.
  styles.css no está en §5.10 y no lo he tocado.
- **`motivo_ok` se conserva.** El parámetro de `marcar_registros_sigrid` ya no lo pasa nadie;
  solo cambia su docstring, como dice §5.10.
- **El contraste llama a `_get` del cliente.** `contrastar_festivos_sesame.py` usa
  `SesameApiClient._get` para listar los calendarios: el cliente no expone el listado y §6
  prohíbe tocarlo. Además, `--impacto` cuenta solo las líneas del año `--ano`.

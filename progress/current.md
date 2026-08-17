<!-- progress/current.md -->
# Trabajo en curso

## F-013 · Informe de validación de datos Sesame por trabajador

- Estado: `in_progress` desde 2026-08-17 · rama
  `feature/F-013-informe-validacion-sesame` (desde la punta de F-004,
  da7293d) · rigor estandar · sdd=false (los `acceptance` de
  features.json hacen de mini-spec). Propuesta enseñada al humano y
  confirmada («lanzalo»).
- Plan confirmado: script `services/partes-front/validar_datos_sesame.py`
  (patrón `prueba_escritura_sigrid.py`) que lista los empleados que conoce
  sesame-api (`GET /api/v1/empleados`), y por cada uno saca con el
  `SesameApiClient` de F-003 los festivos del año y la jornada; informe
  Markdown + CSV en `services/partes-front/logs/` (NO versionado: DNIs).
  Errores por trabajador como filas del informe. Tests con MockTransport.
  El humano ejecuta el script contra su sesame-api local (localhost:8006)
  y valida los números a mano.
- Fuera: desplegar sesame-api, tocar los servicios, corregir datos.
- IMPLEMENTADO el 2026-08-17 (informe completo en
  `progress/impl_F-013.md`): `services/partes-front/validar_datos_sesame.py`
  + `services/partes-front/tests/test_f013_informe_sesame.py` (40 tests,
  sin red) + sección «Herramientas de consola» en `docs/ARCHITECTURE.md`.
  El listado de empleados se hace en el propio script (no se tocó el
  `SesameApiClient`, gemelo del de sv3), y se usa el cliente en crudo, sin
  `CalendarioProvider`, para que un 404 salga como fila de error.
  `bash harness/init.sh` en verde. Pendiente: reviewer, y la VALIDACIÓN
  MANUAL del humano ejecutando el script contra su sesame-api local
  (`cd services/partes-front && python validar_datos_sesame.py --base-url
  http://localhost:8006 --api-key <clave>`).


## F-004 · Congelar registros aprobados

- Estado: `spec_ready` — spec ESCRITA (2026-08-16) y APROBADA por el
  humano (2026-08-16) en
  `specs/F-004-congelar-aprobados/{requirements,design,tasks}.md` · rama
  `feature/F-004-congelar-aprobados` (creada desde la punta de F-003,
  301cd78, para leer el código con F-003 incluida) · rigor estandar ·
  sdd=true. Implementación pendiente de turno (tras F-013 y F-011).
- Resumen de la spec: congelación en sv4 SOLO. Matriz (R1): congela
  `approved` del documento + `sigrid_estado` en {encolado, registrado};
  `omitido`/`error`/`conflicto` siguen editables (son el camino de
  arreglo). Guarda en el repositorio (`CongeladoError` → 409 con motivo);
  la UI refleja con candados. Desaprobar = el `unapprove` existente;
  bloqueado con líneas `encolado` (petición en vuelo); las `registrado`
  siguen congeladas tras desaprobar (el synckey es estable: reaprobar una
  línea editada NO actualiza Sigrid — hecho verificado en el pipeline de
  sv5). Sin cambios de schema; sin tocar orm_models.py (F-010).
- Decisiones que estaban abiertas (resueltas al aprobar; ver más abajo):
  1. Líneas `registrado`: quedan congeladas PERMANENTEMENTE en el portal
     (corregirlas exige actuar en Sigrid; si se borra allí la línea,
     reaprobar reescribe con valores nuevos). Se descartó un endpoint
     «desvincular de Sigrid». ¿De acuerdo, o se quiere una feature futura
     «anular en Sigrid» vía sv5?
  2. Papelera bloqueada para documentos/líneas con algo registrado (R7,
     R12): ¿de acuerdo?
  3. Undo/reasignaciones/borrados masivos: omiten congeladas y reportan
     recuento, en vez de abortar todo (D5): ¿de acuerdo?
  4. Detectada discrepancia documental: `partes-proyecto.md` §5.2 lista
     `approved*` en `parte_registros`, pero NINGÚN orm_models.py la tiene
     (la aprobación real es por documento). Anotar para F-010/corrección
     del documento maestro; F-004 no añade columnas.

Notas de contexto para la próxima sesión:

- F-003 cerrada el 2026-08-16 (resumen en `progress/history.md`): entregada
  APAGADA; para encenderla hacen falta las peticiones P1/P2 al proyecto
  sesame-api (desplegarlo + exponer horas de jornada) — están en manos del
  humano. Merge a dev y push pendientes del humano.
- F-002 desplegada: sv5 en MODO PRUEBAS (obra 0404, PRUEBA-IA) hasta que
  el humano valide en navegador y ejecute el paso a modo normal.
- Siguiente feature por prioridad: F-004 (congelar registros aprobados).

### Decisiones del humano sobre la spec F-004 (2026-08-16)

Las 3 decisiones abiertas: APROBADAS tal cual la spec (registradas
permanentes, papelera bloqueada, masivas omiten-y-reportan). Spec F-004
APROBADA. La implementación espera su turno: antes van F-013 (informe
Sesame) y F-011 (jornada reducida), por orden del humano.

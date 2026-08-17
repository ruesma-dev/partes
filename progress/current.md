<!-- progress/current.md -->
# Trabajo en curso

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
- F-013 cerrada el 2026-08-18 (resumen en `progress/history.md`). MANUAL
  del humano: ejecutar `validar_datos_sesame.py` contra sesame-api local y
  validar los números.
- Siguiente feature por prioridad: F-011 (jornada reducida por días,
  URGENTE, spec) → F-012 → F-004 (spec aprobada).

### Decisiones del humano sobre la spec F-004 (2026-08-16)

Las 3 decisiones abiertas: APROBADAS tal cual la spec (registradas
permanentes, papelera bloqueada, masivas omiten-y-reportan). Spec F-004
APROBADA. La implementación espera su turno: antes van F-013 (informe
Sesame) y F-011 (jornada reducida), por orden del humano.

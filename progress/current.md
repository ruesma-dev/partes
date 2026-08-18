<!-- progress/current.md -->
# Trabajo en curso

## F-004 · Congelar registros aprobados

- Estado: `in_progress` desde 2026-08-18 (implementer lanzado) — spec
  ESCRITA (2026-08-16) y APROBADA por el humano (2026-08-16) en
  `specs/F-004-congelar-aprobados/{requirements,design,tasks}.md` · rama
  `feature/F-004-congelar-aprobados` (creada desde la punta de F-003,
  301cd78, para leer el código con F-003 incluida) · rigor estandar ·
  sdd=true. La rama se puso al día con la punta de F-013 (191b6ed) antes
  de implementar. En paralelo, el spec-author redacta la spec de F-012 en
  esta misma rama (solo `specs/F-012-*/`).
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

### IMPLEMENTACIÓN TERMINADA (2026-08-18) — pendiente de review

- T1–T8 completas (`specs/F-004-congelar-aprobados/tasks.md`, todas `[x]`),
  un commit por tarea más su commit de fase RED. Informe completo en
  **`progress/impl_F-004.md`**; campaña de mutación en
  `progress/mutacion_F-004.md`.
- `bash harness/init.sh` en verde. sv4: 443 tests (129 nuevos), ruff sin
  avisos nuevos (450, los mismos que antes de la feature),
  `node --check static/app.js` OK.
- Cobertura del diff propio de F-004 (base `9772ba4`, la punta de F-013):
  **100 % (183/183)**. La puerta de `init.sh` mide contra `dev` y da 95,6 %
  porque arrastra F-003 y F-013, que aún no están en `dev`.
- **Verificaciones MANUAL del humano**: las 7 están listadas con sus pasos
  exactos al final de `progress/impl_F-004.md` (parte aprobado, línea
  registrada con `curl`, línea encolada, popup de la matriz, masivas,
  papelera y no regresión del flujo de aprobación). Requieren portal en
  local y sv5 en modo pruebas, y **Ctrl+F5** (cambian `app.js` y
  `styles.css`).
- Anotado para F-010, además de la resincronización del ORM: los
  `SAWarning` de `hard_delete_document`/`vaciar_papelera` (borrado masivo +
  cascada del ORM sobre filas ya borradas). Es código anterior a F-004; los
  tests nuevos lo sacan a la luz, arreglarlo toca `orm_models.py`.

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
- Informe F-013 ejecutado el 2026-08-18 contra sesame-api local (218
  empleados): festivos OK (Madrid 196, Tomares 15, Sevilla 4, Málaga 2,
  Alicante 1 parcial 8/21 — revisar asignación); contratos en Sesame:
  NINGUNO (jornada/reducida sin fuente). Bug daysOff corregido en
  sesame-api (sin commit allí: árbol P2 pendiente). Excel para el humano en
  services/partes-front/logs/festivos_por_trabajador_2026.xlsx (no
  versionado).
- F-011 REPRIORIZADA A BAJA (prio 12) por el humano el 2026-08-18: sin
  contratos en Sesame no hay fuente de jornada reducida.
- Siguiente feature por prioridad: F-012 (estudio candef 9h/viernes) →
  F-004 (spec aprobada) → F-005 …

### Decisiones del humano sobre la spec F-004 (2026-08-16)

Las 3 decisiones abiertas: APROBADAS tal cual la spec (registradas
permanentes, papelera bloqueada, masivas omiten-y-reportan). Spec F-004
APROBADA. La implementación espera su turno: antes van F-013 (informe
Sesame) y F-011 (jornada reducida), por orden del humano.

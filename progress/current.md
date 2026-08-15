<!-- progress/current.md -->
# Trabajo en curso

## F-003 · Integración sesame-api: festivos y jornada reales

- Estado: **spec escrita** (2026-08-15) en
  `specs/F-003-sesame-festivos-jornada/` (requirements 21 R · design ·
  15 tareas), commiteada en la rama `feature/F-003-sesame-festivos-jornada`.
  Rigor critico · sdd=true. **PARADA: la spec la aprueba el humano.**

### Hallazgos clave de la exploración de sesame-api (repo local)

- Es un FastAPI standalone (puerto 8006, `x-api-key`, DNI-first, caché
  TTL propia). **NO está desplegado en Azure** y su código FastAPI **ni
  siquiera está commiteado** (la rama `main` remota solo tiene README).
- `GET /api/v1/jornada` **NO devuelve horas** (solo `tipo`, `reducida`
  heurística, fechas de contrato) ⇒ el `candef` NO puede sustituirse
  numéricamente hoy. La spec prepara el enchufe (resolutor único con
  regresión) y deja la sustitución bloqueada por la petición P1.
- `azure-apps/` no tiene documento de sesame-api (hueco P3, dueño:
  proyecto sesame-api).

### Decisiones CERRADAS por el humano (2026-08-15, revisión conjunta)

- D1: SÍ se amplía la duplicación tolerada del CLAUDE.md con los clientes
  `infrastructure/sesame/` de sv3 y sv4 (tarea de la enmienda).
- D2 CORREGIDA — régimen en DOS niveles: vistas informativas = fail-open
  con aviso visible; cálculo/registro con Sesame ACTIVADO pero caído =
  BLOQUEO del registro con marca (sin cambios de schema) y aprobación
  manual explícita como override, que también queda marcada. Con
  sesame_enabled=false no hay bloqueo (comportamiento actual).
- D3 (al vuelo, sin columnas), D6 (tinte por calendario default): OK.
- P2: implementar APAGADA ya; encendido tras desplegar sesame-api.
- Spec APROBADA con la enmienda de D2. F-010 (resincronizar orm_models)
  añadida al backlog.

Spec-author relanzado para la enmienda. Tras ella: delta al humano e
implementer (aprobación ya dada).

### Decisiones abiertas ORIGINALES del spec-author (histórico)

1. **D1**: pareja de clientes `infrastructure/sesame/` en sv3 y sv4
   (precedente F-002, adaptadores por servicio). Propuesta adicional:
   ampliar la lista de duplicación tolerada del CLAUDE.md con esos dos
   clientes. ¿Se amplía?
2. **D2**: resiliencia fail-open (caché stale → calendario por defecto →
   respaldo `holidays`/JSON con WARNING), nunca KO. ¿De acuerdo, o se
   prefiere KO/aviso duro en alguna vista?
3. **D3**: resolución al vuelo, SIN columnas nuevas ni tocar
   `orm_models.py` (que además ya está desincronizado entre sv3 y sv4 —
   candidata a feature de saneamiento aparte).
4. **D4/P1**: la jornada numérica queda fuera hasta que sesame-api
   exponga horas del contrato. Hay que **pedir P1 al proyecto
   sesame-api** (ampliar `/api/v1/jornada` con `horas_dia`/`horas_semana`).
5. **P2**: para activar en Azure hace falta commitear/desplegar
   sesame-api y meter `sesame-api-key` en `kv-partes-pt7m3`. La feature
   se puede implementar y mergear APAGADA (`sesame_enabled=false` ⇒
   comportamiento idéntico al actual) sin esperar a P2. ¿Se implementa ya
   o se espera al despliegue?
6. **D6**: en la matriz de obra, el tinte de columna festivo usa el
   calendario por defecto; la exactitud por trabajador va en los avisos
   (no celda a celda). ¿Suficiente?

### Siguiente paso

- Humano aprueba/ajusta la spec ⇒ `features.json` F-003 a `spec_ready` ⇒
  implementer.

### Contexto operativo heredado

- F-002 desplegada en Azure; sv5 en MODO PRUEBAS (obra 0404) hasta que el
  humano valide en navegador y pase a normal.

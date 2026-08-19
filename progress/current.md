<!-- progress/current.md -->
# Trabajo en curso

Sesión 2026-08-19. **F-015 `done`** (APROBADA por el reviewer, pendiente de
merge del humano). **F-016** y **F-017** con trabajo hecho y esperando
decisión. **F-014 `blocked`** como deuda aparcada. Ninguna feature
`in_progress`.

Ramas vivas, ninguna mergeada, nada en el remoto:

| Rama | Estado |
|---|---|
| `feature/F-015-jornada-semanal-candef` | **lista para merge a `dev`** |
| `feature/F-016-admin-empleado-jornada` | solo spec (2 commits), pendiente de aprobación |
| `feature/F-014-candef-9-sigrid` | petición lista, aparcada a la espera de RRHH |

`dev` = `cf77e6a`.

## Lo que el humano tiene que decidir o hacer

1. **Mergear F-015 a `dev`** (y desplegar cuando quiera). No espera a F-014.
2. **T12 de F-015**: verificación MANUAL en el portal tras desplegar (detalle
   en «MANUAL pendiente»).
3. **Aprobar la spec de F-016** (`specs/F-016-admin-empleado-jornada/`, 20
   requisitos) para que se implemente. Su puerta de entrada es F-015 en `dev`.
4. **Orden de F-016 y F-017**: las dos órdenes funcionan sin retrabajo. F-017
   antes solo sirve para que las filas de `empleado_jornada` nazcan firmadas
   con el usuario real. Hoy las dos están en `priority` 8.
5. **Dos dudas abiertas de F-016** (`design.md` §13): los tres normalizadores
   de DNI equivalentes que conviven en sv4 (¿feature de limpieza aparte?) y si
   las filas con `origen` `sigrid`/`sesame` serán editables desde la pantalla.
6. **Automejoras del arnés** acumuladas para F-009 (ver abajo).

## F-015 · done (2026-08-19)

Implementada, revisada y aprobada. Resumen completo en `progress/history.md`;
detalle en `progress/impl_F-015.md`, mutación en `progress/mutacion_F-015.md`,
revisión en `progress/review_F-015.md`.

Números verificados por el reviewer, no leídos: `init.sh` verde, **1.195
tests**, cobertura de líneas cambiadas **99,4 %** (520/523), mutación
**259/237/22/0** (91,5 %). Regresión cero: los dorados de F-003 intactos.

**La puerta R35 está INVERTIDA** (decisión del humano): F-015 se mergea y
despliega sin F-014, porque con candef 8 es regresión cero. Lo que NO se puede
es aplicar el `candef = 9` en Sigrid antes de desplegar F-015: eso daría
−3 h/semana de extra negativa a esos 7 recursos.

Correcciones menores del reviewer aplicadas por el líder al cerrar: referencia
cruzada §5.5 → §5.4 en `docs/referencia/partes-proyecto.md`, «16 columnas» →
«19» en T12 de `tasks.md`, y el test `..._la_jornada_es_plana` renombrado a
`..._la_semanal_sale_del_mapa`, que es lo que de verdad fija (14 tests del
fichero en verde tras el renombrado).

## F-016 · spec lista, pendiente de aprobación (2026-08-19)

Pantalla de administración de `empleado_jornada` en sv4: alta, edición, cierre,
desactivación y reactivación de jornadas especiales. **20 requisitos**, solo
sv4, **cero cambios de schema** (vive con las 19 columnas que creó F-015, con
test que lo vigila). Informe: `progress/spec_F-016.md`.

Decisiones del humano ya incorporadas (2026-08-19): acceso a cualquier usuario
autenticado con interruptor `JORNADAS_ADMIN_ENABLED` y puerta única para
enchufar el rol cuando exista F-008; identidad real de Easy Auth (⇒ F-017);
**selector de trabajador con DNI y nombre y autorrelleno**, reutilizando el
`GET /api/sigrid/empleados` y el `_comboSimple` que ya existen; y «Reactivar»
se queda.

Del diseño conviene recordar: el humano **nunca escribe `hasta`** (el
formulario pide «último día incluido» y la web hace el `+1 día`); cerrar ≠
desactivar; un solape se rechaza con 409 nombrando la fila en conflicto y
**nunca se resuelve solo**; y la pantalla avisa de que el cambio tarda en
aplicarse porque sv3 cachea la tabla (`JORNADA_CACHE_TTL_S`).

## F-017 · alta nueva (2026-08-19)

«Identidad real de Easy Auth en el portal (sv4)». Hallazgo del spec-author de
F-016, verificado por el líder: **sv4 no lee hoy la identidad del usuario**.
Cero referencias a `X-MS-CLIENT-PRINCIPAL` en el repositorio; las **once**
escrituras de auditoría (`approved_by`, `deleted_by` y cuatro entradas de
`undo_log`, todas en `services/partes-front/interface_adapters/web/app.py`) se
firman con `DEFAULT_REVIEWER`, igual para todos.

Decisión del humano: se introduce y **se extiende a todo el portal**, no solo a
las columnas de F-016. Material de partida en
`specs/F-016-admin-empleado-jornada/design.md` §14. Los **roles** siguen siendo
F-008: F-017 responde a «quién hizo esto», no a «quién puede hacerlo».

## F-014 · DEUDA IMPORTANTE, aparcada (2026-08-19)

Decisión del humano: lo que falta **no es crítico**, lo ejecuta RRHH en Sigrid
y lleva tiempo; él avisará cuando se pueda retomar. La petición está redactada,
revisada y **APROBADA** en `progress/peticion_F-014.md` (rama
`feature/F-014-candef-9-sigrid`), con un ⛔ en la cabecera: **no se envía hasta
que F-015 esté desplegada**.

Cuando se retome: enviar el correo (§7) → RRHH cambia el `candef` de 7 fichas y
el DNI de `MO/0037` → responde qué decide con `MO/0007` (de alta pero sin
partes desde 2026-02-04) → ejecutar V1/V2/V3 en solo lectura → segunda revisión
→ `done` → merge.

Hallazgos que no conviene perder: los códigos `MO/NNNN` **no identifican una
sola ficha** (bajo MO/0006, MO/0007 y MO/0008 hay homónimas de alta, misma
categoría, misma hora por defecto y también con `candef = 8`: solo las separa
`res.ide`); `MO/0031` tiene dos fichas de alta que registran en 2026 y ahí
desempata la categoría; y `MO/0037` sigue sin DNI (`res.conide = 0`).

## Orden del backlog

1. **F-016** (spec lista) y **F-017** (alta nueva), en el orden que decida el
   humano; F-016 necesita F-015 en `dev`.
2. **F-014** — `blocked`, solo la desbloquea RRHH.
3. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-009 automejoras del arnés · F-011 jornada reducida
   (última; fuente candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-015 · T12 (NUEVO)**, tras desplegar sv3 y sv4: en el log de arranque de
  ambos, «esquema inicializado (N sentencias complementarias)» con N mayor que
  el de F-010; en la base `partes`, la tabla `empleado_jornada` con sus **19**
  columnas y el índice `ix_empleado_jornada_dni_norm`; en el portal, un
  trabajador de la cuadrilla con un viernes de 6 h **sin** aviso de jornada
  incompleta y el KPI «9 h · 42 h/sem · último laborable 6 h»; y que un parte
  ya aprobado/registrado **no** cambie su desglose tras la primera pasada de
  sv3. Ojo: los 7 de la cuadrilla siguen con `candef = 8` hasta que se haga
  F-014, así que ese punto solo se ve del todo después.
- **F-014**: enviar la petición **solo cuando F-015 esté desplegada**.
- **F-002 (Azure):** validar en navegador la aprobación asíncrona (⏳ encolado →
  ✓ PT26/…, obra 0404 en modo pruebas), limpiar 0404 (`python
  prueba_escritura_sigrid.py limpiar --ejecutar` en sv5) y pasar sv5 a modo
  normal (`az containerapp update -n ca-sv5-transfer -g $RG --set-env-vars
  OBRA_PRUEBAS_FORZAR=false`).
- **F-003:** encendido cuando sesame-api esté desplegado (P2) — variables
  SESAME_* en sv3 y sv4 a la vez + secreto `sesame-api-key` en kv-partes. Ojo:
  encender contra URL muerta bloquea aprobaciones por diseño.
- **F-004:** 7 comprobaciones en navegador con Ctrl+F5 (pasos al final de
  `progress/impl_F-004.md`).
- **F-010:** M1/M2 — arrancar sv3 y sv4 en local, «esquema inicializado (118
  sentencias complementarias)» en ambos, índice
  `ix_parte_registros_deleted_at_utc` en `pg_indexes`, columnas 7/47/56/7
  (`progress/impl_F-010.md` §6). M3 redeploy cuando decida. **Se cumple de paso
  al hacer T12 de F-015.**
- **F-013:** validar el Excel `services/partes-front/logs/
  festivos_por_trabajador_2026.xlsx` (no versionado): Alicante 8/21 y
  asignaciones por centro.
- **sesame-api (otro repo, del humano):** commitear el árbol P2 (incluye el fix
  `daysOff` del 2026-08-18), desplegar, doc en azure-apps (P3);
  `contract_not_found` → 404 en vez de 502.
- **Sesame HR (RRHH):** completar el calendario Alicante; contratos vacíos
  (0/218) — decidir si se cargan.
- **Cambio de modelo Gemini** en sv2 (comando dado; actualizar
  `infra/create_capps_partes.ps1:38`).

## Automejoras del arnés pendientes (F-009 ⇒ genéricas a `arnes-base`)

- **La más rentable, ya confirmada con datos por F-015 y anotada desde F-010**:
  `harness/mutacion.py` ejecuta solo la suite del servicio dueño del fichero
  mutado, así que **el guardián de una copia gemela nunca mata mutantes** (vive
  en `tests/` de la raíz). Produjo **27 de los 48 supervivientes** de la 2.ª
  campaña de F-015, todos falsos «equivalentes». Arreglo: ejecutar también la
  suite de la raíz (~4 s aquí) o, mínimo, avisar cuando el fichero mutado tenga
  copia gemela declarada en `CLAUDE.md`. El reviewer de F-015 propone además
  una línea en `.claude/agents/reviewer.md`: desconfiar por defecto de los
  supervivientes de una copia duplicada.
- **El presupuesto de mutación por mutante es engañoso** (F-015): con 16
  evaluadores concurrentes y una suite de ~80 s, el timeout de 120 s de
  `rigor.json` convirtió 100 mutantes en «timeout», que **no es una medición**.
  Debería escalar con la concurrencia o avisar cuando los timeouts superen un
  porcentaje del total.
- **Del reviewer de F-014**: (A) checkpoint para features cuyo entregable es
  una **petición a un tercero** (clave unívoca verificada, apartado «qué NO se
  toca», verificación escrita ANTES con control de daños, resultado esperado en
  TODOS los escenarios, barrido de datos sensibles); (B) generalizar la regla
  «si el entregable es una medición, el reviewer la **re-ejecuta** en vez de
  leerla» — es lo que destapó el defecto D1 de F-014.
- Las anteriores de F-013 (AM-1..3), F-004 y F-010 siguen en `history.md`.

## Notas de contexto

- **Deuda detectada el 2026-08-19 (fuera de alcance de F-014)**:
  `services/partes-front/consulta_reshor_recursos.py` tiene 4 DNIs y nombres de
  personas reales **hardcodeados y versionados** (líneas 27-31) y apunta a una
  ruta `.env` de otro repositorio. Pendiente de decisión del humano.
- F-013 (2026-08-18): 218 empleados; festivos OK (Madrid 196, Tomares 15,
  Sevilla 4, Málaga 2, Alicante 1 parcial); contratos en Sesame: NINGUNO ⇒
  jornada/reducida sin fuente en Sesame; F-011 repriorizada a baja por eso.
- F-012 (2026-08-18): decisiones firmes del humano sobre la jornada semanal
  (mapa 8→40 / 9→42, resto en el último laborable, excepciones en
  `empleado_jornada`), ya implementadas por F-015.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano); no proponer
  push.

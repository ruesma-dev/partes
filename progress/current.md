<!-- progress/current.md -->
# Trabajo en curso

Sesión 2026-08-19/20. **F-015 y F-016 `done`**, las dos APROBADAS por el
reviewer, mergeadas, publicadas y **DESPLEGADAS**. **F-014 `blocked`** como
deuda aparcada, pero su puerta ya está abierta (ver abajo). Ninguna feature
`in_progress`.

| Rama | Estado |
|---|---|
| `feature/F-016-admin-empleado-jornada` | mergeada a `dev` y borrada |
| `feature/F-014-candef-9-sigrid` | petición lista, aparcada a la espera de RRHH |

`dev` = merge de F-016 (`5606954`), publicado, con F-015 dentro.

## Despliegue del 2026-08-20 (00:10)

`redeploy_partes.ps1 -Solo sv3,sv4` desde el árbol en `dev`. Ambos servicios en
la revisión **`r20260820000737`**:

| Servicio | Estado comprobado |
|---|---|
| `ca-sv4-front` | `Running`, 1 réplica. Arranque limpio: «esquema inicializado (137 sentencias complementarias)» → `Application startup complete` → Uvicorn en 8014. `HTTP 401` sin cookie ⇒ Easy Auth en pie. |
| `ca-sv3-persistencia` | `ScaledToZero` (KEDA min 0, normal). Su log de arranque **ya está verificado** (2026-08-20 por la mañana): ver la sección siguiente. |

Con esto queda aplicado también el DDL pendiente de **F-010** (M1/M2).

Dos tropiezos, ninguno de código y los dos ya conocidos:

1. `RequestDisallowedByAzure` (MFA) en el primer intento: el `az login` normal
   vale para el build en el ACR pero no para `containerapp update`. Se resuelve
   con el `--claims-challenge` de `infra/README_partes.md:28`.
2. `getaddrinfo failed` de DNS en el **paso final informativo**, ya creadas las
   dos revisiones: solo dejó vacío el «Portal sv4: https://». FQDN real:
   `ca-sv4-front.yellowplant-2add9c3e.spaincentral.azurecontainerapps.io`.

Aprendizaje operativo: `az containerapp logs show --tail` ya no alcanza el
arranque —el polling de colas llena el buffer en minutos—. Los logs de arranque
salen con `az monitor log-analytics query -w <workspace de log-partes-dev>`
filtrando por `RevisionName_s`.

## Verificación del despliegue (2026-08-20, mañana)

Dos verificaciones lanzadas a subagentes. Informes:
`progress/verif_sv3_arranque_20260820.md` y
`progress/verif_esquema_partes_20260820.md`.

### 1. Arranque de sv3 — VERDE

Sin `Traceback`, sin `ERROR` y **sin ningún WARNING de jornada** (ni candef
fuera del mapa, ni fallo leyendo `empleado_jornada`). Esquema inicializado con
**137 sentencias complementarias**, las mismas que reportó sv4. Wiring
correcto: `[jornada][wiring] mapa candef -> jornada semanal: 8:40, 9:42`, más
calendario, Sigrid, SharePoint y consumo de `q-persistencia`. Misma imagen del
despliegue (`sv3-partes:latest`, digest `sha256:b3b533c5…`). Devuelto a **0
réplicas**, confirmado `ScaledToZero`.

Dos aprendizajes operativos:

- **La revisión `r20260820000737` YA había arrancado** entre 22:09 y 22:14 UTC
  de anoche y su log estaba en Log Analytics desde entonces. Forzar réplicas no
  era necesario: antes de hacerlo, mirar si la revisión ya tiene filas en
  `ContainerAppConsoleLogs_CL`.
- **Cada cambio de `--min-replicas` crea una revisión nueva.** La activa ya no
  se llama `r2026…` sino `ca-sv3-persistencia--0000010`. El código se rastrea
  por **digest del ACR**, no por el nombre de la revisión.
- El `az containerapp update` pasó a la primera: el `--claims-challenge` no
  llegó a hacer falta (el humano había reautenticado con MFA en su consola).

### 2. Esquema en PostgreSQL — BLOQUEADO por firewall

No se pudo consultar la base real: la IP pública del puesto no figura en
ninguna regla de `psql-albaranes-rs9k2` (`connection timeout expired`). **No se
tocó nada del servidor**, que es compartido. Queda pendiente de que el humano
añada la regla (`datamart-puesto-pgris-<fecha>`) y se relance; el SQL exacto
está listo en el informe, incluida la **M1 de F-010**.

Lo verificable sin base salió **CONFORME**: 19 columnas declaradas, índice
`ix_empleado_jornada_dni_norm` sobre `(dni_norm)` declarado, y las **dos copias
de `orm_models.py` (sv3 y sv4) byte-idénticas** — el defecto que F-010 vino a
arreglar sigue sano. `ddl_complementario()` genera 137 sentencias, 19 de ellas
de `empleado_jornada`: **cuadra con el log de arranque de los dos servicios**.

Sin CHECKs de horas 0–24 ni de vigencias en la base, y eso es **correcto**: la
spec los pone en la aplicación (F-016/R27), no en el schema.

Dos correcciones que salieron de aquí:

- **Errata en `specs/F-015-jornada-semanal-candef/design.md` §8**: dice «las 16
  columnas». La tabla normativa §6, el ORM y el guardián dicen **19**. El texto
  está mal, no el código. Pendiente de corregir.
- **F-010 no tiene «migraciones M1/M2»**: M1/M2/M3 son sus *verificaciones
  manuales*. M2/M3 se dan por cumplidas con las 137 sentencias; **M1 sigue
  pendiente** (índice `ix_parte_registros_deleted_at_utc` y los recuentos
  7/47/56/7) y necesita acceso a la base.

## Lo que el humano tiene que decidir o hacer

1. **Verificaciones MANUAL del despliegue, pendientes**: lo que queda de T12
   de F-015 (las 19 columnas de `empleado_jornada`, el KPI «9 h · 42 h/sem ·
   último laborable 6 h», el viernes de 6 h sin aviso, y que un parte ya
   aprobado no cambie su desglose) y las 6 de
   `specs/F-016-admin-empleado-jornada/design.md` §8.2. La 6 —el combo en el
   navegador— es la única funcionalidad que ningún test cubre.
2. **Enviar la petición de F-014 a RRHH**: la condición ya se cumple (F-015
   desplegada). Texto aprobado en `progress/peticion_F-014.md`.
3. **F-017** (identidad real de Easy Auth): es la siguiente natural. No la
   necesita nadie para funcionar, pero mientras no exista, todas las filas de
   auditoría del portal siguen firmadas con `DEFAULT_REVIEWER`.
4. **Dos dudas abiertas de F-016** (`design.md` §13): los tres normalizadores
   de DNI equivalentes de sv4 (¿feature de limpieza aparte?) y si las filas con
   `origen` `sigrid`/`sesame` serán editables cuando existan.
5. **Automejoras del arnés** acumuladas para F-009 (lista abajo). Ya son ocho,
   varias con evidencia medida.

## F-015 · done, en `dev` (2026-08-19)

Jornada del día por jornada semanal derivada del candef y último día laborable.
Resumen en `progress/history.md`; detalle en `progress/impl_F-015.md`,
`progress/mutacion_F-015.md` y `progress/review_F-015.md`.

Verificado por el reviewer: 1.195 tests, cobertura **99,4 %** (520/523),
mutación **259/237/22/0** (91,5 %). Regresión cero: con `candef = 8` —que hoy
son todos— no cambia el comportamiento de nadie. Por eso se puede desplegar
sin F-014.

## F-016 · done, en `dev` y desplegada (2026-08-19/20)

Pantalla `/admin/jornadas` en sv4: crear, editar, cerrar, desactivar y
reactivar las excepciones de jornada. Resumen en `progress/history.md`; detalle
en `progress/impl_F-016.md`, `progress/mutacion_F-016.md` y
`progress/review_F-016.md`.

Verificado por el reviewer ejecutando y recalculando: 799 tests en sv4 (134
nuevos) + 92 en la raíz, cobertura **98,5 %** (326/331), mutación **93/79/14/0**
(85 %). Cero cambios de schema, cero ficheros fuera de sv4, cero rutas nuevas
de catálogo, cero `DELETE`.

## F-014 · DEUDA IMPORTANTE, aparcada (2026-08-19)

Decisión del humano: no es crítico, lo ejecuta RRHH en Sigrid y lleva tiempo;
él avisará. La petición está redactada y **APROBADA** en
`progress/peticion_F-014.md` (rama `feature/F-014-candef-9-sigrid`), con un ⛔
en la cabecera.

**El orden importa**: primero F-015 desplegada, después el correo. Aplicar el
`candef = 9` en Sigrid con sv3/sv4 sin F-015 daría **−3 h/semana** de extra
negativa a esos 7 recursos; al revés no pasa nada. **Desde el despliegue del
2026-08-20 esa condición se cumple**: el correo ya se puede enviar en cuanto el
humano quiera.

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

1. **F-017** — identidad real de Easy Auth en sv4 (`pending`, prioridad 8).
   Material listo en `specs/F-016-admin-empleado-jornada/design.md` §14, con
   los once puntos exactos que hoy firman con `DEFAULT_REVIEWER`.
2. **F-014** — `blocked`, solo la desbloquea RRHH.
3. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-009 automejoras del arnés · F-011 jornada reducida
   (última; fuente candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-016 (NUEVO)**: las 6 verificaciones de
  `specs/F-016-admin-empleado-jornada/design.md` §8.2, con el portal levantado
  y PostgreSQL. La 6 (comportamiento del combo de trabajador en el navegador)
  no la cubre ningún test.
- **F-015 · T12** (desplegado el 2026-08-20; los logs de esquema de sv4 **y de
  sv3** ya están comprobados, los dos con 137 sentencias y sin errores): la tabla
  `empleado_jornada` con sus **19** columnas y el índice
  `ix_empleado_jornada_dni_norm`; un trabajador de la cuadrilla con viernes de
  6 h **sin** aviso de jornada incompleta y el KPI «9 h · 42 h/sem · último
  laborable 6 h»; y que un parte ya aprobado **no**
  cambie su desglose tras la primera pasada de sv3. Ojo: la cuadrilla sigue con
  `candef = 8` hasta F-014, así que ese punto solo se ve del todo después.
- **F-010:** M2/M3 cumplidas (137 sentencias en sv3 y sv4). **M1 pendiente**:
  índice `ix_parte_registros_deleted_at_utc` y recuentos 7/47/56/7, a la espera
  de la regla de firewall de PostgreSQL.
- **F-014**: la puerta ya está abierta (F-015 desplegada el 2026-08-20); queda
  enviar la petición cuando el humano decida.
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

1. **La más rentable, confirmada con datos por F-015 y anotada desde F-010**:
   `harness/mutacion.py` ejecuta solo la suite del servicio dueño del fichero
   mutado, así que **el guardián de una copia gemela nunca mata mutantes**
   (vive en `tests/` de la raíz). Fueron **27 de los 48 supervivientes** de la
   2.ª campaña de F-015, todos falsos «equivalentes». Arreglo: ejecutar también
   la suite de la raíz (~4 s aquí) o, mínimo, avisar cuando el fichero mutado
   tenga copia gemela declarada en `CLAUDE.md`.
2. **El presupuesto de mutación por mutante es engañoso** (F-015): con 16
   evaluadores y una suite de ~80 s, el timeout de 120 s de `rigor.json`
   convirtió 100 mutantes en «timeout», que **no es una medición**. Debería
   escalar con la concurrencia o avisar cuando los timeouts pasen de un umbral.
3. **`progress/mutacion_*.md` debería registrar qué suite se ejecutó** por
   fichero (reviewer de F-016): sin eso, en una feature que toque dos servicios
   el hueco de (1) no se detecta sin recalcular.
4. **C4 de `CHECKPOINTS.md` podría pedir un recuento mecánico
   test-por-requisito** sobre los nombres `test_fXXX_rN_*`, en vez de fiarse de
   la tabla de trazabilidad de la spec (reviewer de F-016).
5. **Checkpoint para features cuyo entregable es una petición a un tercero**
   (reviewer de F-014): clave unívoca verificada, apartado «qué NO se toca»,
   verificación escrita ANTES con control de daños, resultado esperado en TODOS
   los escenarios, barrido de datos sensibles porque el documento sale del
   repositorio.
6. **Generalizar «si el entregable es una medición, el reviewer la re-ejecuta
   en vez de leerla»** (reviewer de F-014): es lo que destapó su defecto D1.
7. **Desconfiar por defecto de los supervivientes de una copia duplicada**, en
   `.claude/agents/reviewer.md` (reviewer de F-015).
8. **Fixture de app compartida en sv4** (deuda transversal, no del arnés): la
   suite pasó de ~52 s a ~114 s porque cada test de endpoint levanta `build_app`
   entera. Patrón heredado de F-002/F-003/F-004.

Las anteriores de F-013 (AM-1..3), F-004 y F-010 siguen en `history.md`.

## Notas de contexto

- **Deuda detectada el 2026-08-19**: `services/partes-front/
  consulta_reshor_recursos.py` tiene 4 DNIs y nombres de personas reales
  **hardcodeados y versionados** (líneas 27-31) y apunta a una ruta `.env` de
  otro repositorio. Pendiente de decisión del humano.
- **`JORNADAS_ADMIN_ENABLED` no está en ningún fichero versionado**: el
  `.gitignore` de sv4 ignora `*.example`. Default `True` en el código y
  documentada en `azure-apps/partes.md`. No es un olvido: el implementer evitó
  un `git add -f` y el reviewer le dio la razón.
- F-013 (2026-08-18): 218 empleados; festivos OK (Madrid 196, Tomares 15,
  Sevilla 4, Málaga 2, Alicante 1 parcial); contratos en Sesame: NINGUNO ⇒
  jornada/reducida sin fuente en Sesame; F-011 repriorizada a baja por eso.
- F-012 (2026-08-18): decisiones firmes del humano sobre la jornada semanal, ya
  implementadas por F-015.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano); no proponer
  push.

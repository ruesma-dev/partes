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

### 2. Esquema en PostgreSQL — CONFORME (verificado contra la base real)

Al primer intento el subagente reportó `connection timeout expired` y **acusó
al firewall**. Era un diagnóstico sin evidencia: la IP pública del puesto
(`nslookup myip.opendns.com`) YA tenía regla en `psql-albaranes-rs9k2`, y
`Test-NetConnection ... -Port 5432` responde `TcpTestSucceeded: True` en 0,01 s.
Al reintentar, `psycopg` conectó en 0,1 s con el mismo host, puerto y usuario.
**Lección** (candidata a automejora del arnés): un timeout no basta para
acusar al firewall sin probar antes el TCP crudo.

Verificado contra PostgreSQL 16.14, base `partes`:

- **19/19 columnas** en `empleado_jornada`: nombre, orden ordinal, tipo,
  nulabilidad y `DEFAULT` coinciden con el ORM y con la spec.
- **`ix_empleado_jornada_dni_norm`** presente sobre `(dni_norm)`, no único, más
  la PK con secuencia. **Cero CHECKs**, que es lo correcto: F-015 §6 delega esas
  validaciones a la aplicación (F-016/R27).
- **M1 de F-010 ✅**: `ix_parte_registros_deleted_at_utc` presente, recuentos
  exactos **7/47/56/7**, `ux_parte_documents_sha256_active` intacto. Ninguna
  tabla ganó ni perdió columnas.
- **Base ↔ sv3 ↔ sv4 coinciden**: las dos copias del ORM siguen byte-idénticas
  y cuadran con la base. Control cruzado: 118 + 19 = **137 sentencias**, justo
  lo que loguearon los dos servicios.
- **4 filas de prueba** de las pruebas en navegador, **ya desactivadas** por el
  humano: `origen='manual'` ✅ y `created_by`/`updated_by` **NULL** ✅, que es
  lo esperado sin `DEFAULT_REVIEWER` (H1) y confirma ese hallazgo desde la base.

**R7 VERIFICADO** (2026-08-20, segunda vuelta). Alta en pantalla con último
día incluido `2026-07-31`: la base guarda **`hasta = 2026-08-01`** y el listado
repinta `2026-07-31`. La conversión «+1 día» funciona. Confirmado por partida
doble con una fila de control (último día `2026-08-20` → `hasta = 2026-08-21`),
y una tercera fila «sin fin» cubre la mitad NULL del requisito.

`desde` sin desplazamiento de huso en las tres. Se sostiene porque `desde` y
`hasta` son **`varchar(16)`** con la fecha ISO, no `date`/`timestamp`: no hay
capa que pueda reinterpretar la zona horaria.

**R12 (solapes) sin violación**: las tres filas se solapan en julio pero solo
una está activa; la auditoría muestra que el humano desactivó cada una antes de
crear la siguiente (baja 11:31:16 → alta 11:31:42), así que el alta **no debía**
rechazarse. La rama de rechazo sí se ejercitó, pero en la prueba anterior de
navegador (el aviso rojo nombrando la fila en conflicto), no en estas filas —
lógicamente no deja rastro en la base, porque no llega a crear nada.

### 2-bis. (histórico) el falso bloqueo por firewall

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

### 3. Pruebas en navegador (2026-08-20, humano) — SUPERADAS

Las 6 verificaciones de `specs/F-016-admin-empleado-jornada/design.md` §8.2 y
el punto de KPI de **F-015 T12**, hechas por el humano contra el portal
desplegado. **Todo funciona.** Combo de trabajador (la 6, que ningún test
cubre): busca por nombre y por DNI, y el alta guarda el DNI elegido. Alta con
DNI ficticio: sale el aviso de R19 y la fila se crea igual. Solape: rechazado
nombrando la fila en conflicto, sin crear nada. Contigua: aceptada. El
listado enseña el `hasta` **inclusivo**, no el interno.

Tres hallazgos, ninguno de ellos un fallo del código desplegado:

**H1 · `DEFAULT_REVIEWER` NO está configurada en el Container App de sv4.**
Comprobado en Azure: la variable no existe en la plantilla del contenedor, y
`.env.example` la declara vacía. El helper `_actor`
(`services/partes-front/interface_adapters/web/app.py:477`) lo contempla —
«sin `DEFAULT_REVIEWER` configurado se sella `NULL` y la operación NO falla»—
y la plantilla pinta `—`. Consecuencia que va más allá de F-016: **los once
puntos de auditoría del portal (`approved_by`, `deleted_by` y las cuatro
entradas de `undo_log`) llevan sellando NULL desde el primer despliegue**. La
auditoría del portal está en blanco, no «firmada con un genérico».
Reordena el enunciado de **F-017**: no es «pasar del valor genérico al usuario
real», es que hoy no hay ni genérico. **DECIDIDO por el humano el 2026-08-20**:
NO se configura un `DEFAULT_REVIEWER` provisional; se espera a **F-017**. El
NULL dice «no se sabe», que es la verdad, y un genérico crearía un tramo de
filas que luego habría que explicar.

**H2 · El KPI de jornada se resuelve con el PRIMER DÍA DEL PERIODO MOSTRADO,
no con hoy** (`app.py:698`, decisión consciente de R25). El periodo que sale
por defecto es el más reciente **con registros de ese trabajador**. Efecto
práctico: se creó una excepción con `desde` = hoy y **el KPI no la reflejaba**;
tampoco con `desde` = 1 del mes en curso. Con `desde` = 2026-01-01 apareció al
instante. Le pasó al humano, que conoce el sistema: **a un administrador le
parecerá que la pantalla no funciona**. No es un bug —la caché se invalida
bien y sv4 tiene una réplica— pero es deuda de usabilidad real. Candidatas:
avisar en la pantalla, o resolver el KPI con `hoy` cuando la excepción esté
vigente hoy.

**H3 · Hueco de borde**: si el trabajador **no tiene ningún registro**, la
ficha no construye calendario, y entonces el KPI se calcula con `date.today()`
pero pasando `excepcion=None` — ignoraría una excepción vigente hoy. En esa
rama la fecha y la excepción dejan de ir juntas. Menor, pero es una
incoherencia real.

**LIMPIEZA**: las pruebas dejaron filas en `empleado_jornada` de la BASE REAL,
incluida una de **un trabajador real** con vigencia desde 2026-01-01 y 42
h/sem. Hay que dejarlas todas `inactiva` (esta pantalla no borra, por diseño).

## F-017 · done, APROBADA y lista para mergear (2026-08-21)

Identidad real de Easy Auth en sv4. Resumen en `progress/history.md`; detalle
en `progress/impl_F-017.md`, `progress/mutacion_F-017.md` y
`progress/review_F-017.md`.

Verificado por el reviewer re-ejecutando: **1.057 tests** en sv4 + 138 en la
raíz, cobertura **99,3 %**, mutación **32/32 muertos, 0 supervivientes, 0
timeouts**. Solo sv4, cero cambios de schema. Primera vuelta RECHAZADA con
tres defectos, los tres corregidos y verificados —el guardián ampliado lo
comprobó **rompiéndolo**—.

**Pendiente**: mergear a `dev` y desplegar. Tras desplegar, la verificación que
no se puede hacer antes: **`GET /whoami` dirá qué inyecta Azure de verdad** en
`X-MS-CLIENT-PRINCIPAL-NAME` (¿UPN o display name?). Era la única ambigüedad
que la spec no podía cerrar.

**Aviso para F-018**: su borrador vive en el worktree
`worktree-agent-ad862e62640d64553` y **heredó el criterio del corte SIN la
excepción de `undo_log.actor`**. Hay que refrescarlo contra `dev` después de
mergear, antes de darlo por bueno.

## Lo que el humano tiene que decidir o hacer

1. **Verificaciones del despliegue**: las 6 de F-016 §8.2 y el KPI de F-015
   **SUPERADAS** en navegador el 2026-08-20 (sección anterior). Quedan: el
   contraste contra la BASE (`origen`, `is_active`, `created_by` y que el
   `hasta` sea un día después del escrito) y la **M1 de F-010**, los dos a la
   espera de la **regla de firewall** de `psql-albaranes-rs9k2`; el «último
   laborable 6 h» con `candef = 9` de verdad, que no llega hasta F-014; y la
   **limpieza** de las filas de prueba.
   Decisión pendiente: qué hacer con `DEFAULT_REVIEWER` (H1).
2. **Enviar la petición de F-014 a RRHH**: la condición ya se cumple (F-015
   desplegada). Texto aprobado en `progress/peticion_F-014.md`.
3. **F-017** (identidad real de Easy Auth): **spec escrita el 2026-08-20**, a
   la espera de aprobación del humano. Ver la sección «F-017 · spec escrita»
   más abajo. Mientras no exista, todas las filas de auditoría del portal
   siguen sellando `NULL` (H1).
4. **Dos dudas abiertas de F-016** (`design.md` §13): los tres normalizadores
   de DNI equivalentes de sv4 (¿feature de limpieza aparte?) y si las filas con
   `origen` `sigrid`/`sesame` serán editables cuando existan.
5. **Automejoras del arnés** acumuladas (lista abajo), ya sin feature propia:
   F-009 se eliminó el 2026-08-20 por decisión del humano. Varias con evidencia
   medida. Destino previsto: portarlas a `arnes-base` al actualizar el arnés.

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

## F-017 · spec escrita (2026-08-20), pendiente de aprobación

`specs/F-017-identidad-easy-auth/` con los tres ficheros. **Solo sv4**: se
comprobó que sv5 ya acepta el campo `usuario` (`Optional[str]`) y **solo lo
loguea** — no llega a ninguna columna de Sigrid, así que empezará a registrar
un nombre real sin un cambio de código. Cero cambios de schema: las siete
columnas de autor ya existen y la más estrecha es `String(120)`
(`undo_log.actor`, `empleado_jornada.created_by`/`updated_by`,
`empleado_alias.created_by`); un UPN cabe de sobra y el helper trunca a 120 de
una vez para todos.

**Ocho decisiones que el humano tiene que aprobar o rebatir** (detalle y
argumentos en `design.md` §11):

| # | Decisión propuesta |
|---|---|
| DA1 | Manda `X-MS-CLIENT-PRINCIPAL-NAME`; el token base64 es el suplente y **nunca** puede lanzar |
| DA2 | Se guarda el **UPN**, no el `oid`: la columna la leen personas (`parte_detail.html`, `admin_jornadas.html`) y no hay dónde meter el `oid`. Identidad inmutable ⇒ F-018 |
| DA3 | El actor se normaliza a **minúsculas** (los UPN son insensibles a mayúsculas; si no, un `GROUP BY` cuenta dos personas donde hay una) |
| DA4 | **ENMENDADA por el humano el 2026-08-20 y ya incorporada.** El fallback tiene **dos ramas**: sin desplegar ⇒ `local:<DEFAULT_REVIEWER>` / `local:sin-identidad`; **desplegado y sin cabecera ⇒ `sin-identidad`, sin prefijo, con WARNING por petición**. Motivo: escribir `local:` en producción no sería «honesto», sería **afirmar un origen falso** y taparía una caída de la autenticación en una columna. La operación se completa igual en las dos ramas |
| DA4 bis | Se distingue el entorno **sin variable nueva ni tocar Azure**: `CONTAINER_APP_*` presente **o** haber visto ya una cabecera de Easy Auth desde el arranque (segunda señal, red de seguridad de la primera). ⚠ **Supuesto de plataforma NO verificado en este repo**: nadie lee esas variables hoy ⇒ **T0 es una puerta** que lo comprueba con `az containerapp exec … printenv` **antes** de implementar, y si no aparecen, `blocked` y se consulta |
| DA5 | `DEFAULT_REVIEWER` se queda con el nombre, cambia el significado: pasa a ser la etiqueta de la sesión local. Renombrarla obligaría a tocar Azure para nada |
| DA6 | El test `test_f016_r13_auditoria` **se pone rojo a propósito** (T4, es la evidencia de que `_actor` manda) y se repara **fabricando la cabecera**, no parcheando el helper: `_actor` es una clausura dentro de `build_app` y no hay nada que `monkeypatch` alcance |
| DA7 | Las filas que escribe **sv3** (ingesta automática) NO se tocan: ahí el autor es el pipeline, no una persona |
| DA8 | **Aprobado por el humano.** `GET /whoami` devuelve actor, **por qué rama salió** (`cabecera-name` / `cabecera-token` / `local` / `sin-identidad-desplegado`), `entorno`, la señal que lo prueba y los **nombres** de las cabeceras presentes (nunca valores). Con la enmienda gana papel: es el único sitio donde se comprueba la detección de entorno **sin escribir una fila** |

**Filas históricas**: no se reescribe ni una (R22). Con H1 la decisión sale
más barata de lo previsto — no hay genéricos que traducir, hay `NULL`, que ya
dice la verdad. Y como a partir de la feature **siempre** hay actor (R7), el
corte queda exacto y gratis: `autor IS NULL` ⇔ «anterior a F-017». Se
documenta en `docs/referencia/partes-proyecto.md` (T10) con un hueco
`⛔ PENDIENTE: fecha de despliegue` que **rellena el humano al desplegar**.

**Ambigüedades encontradas que conviene que el humano sepa:**

0. **La enmienda mete un riesgo nuevo, y es el único de la feature que
   ensucia datos**: si en Azure no existieran las `CONTAINER_APP_*`, el
   portal se creería local y firmaría filas de producción como `local:…` —
   justo la mentira que la enmienda quiere evitar. El fallo es asimétrico
   (creerse desplegado en local es inocuo: `sin-identidad` + WARNINGs en un
   puesto de trabajo). Mitigado por tres vías: **T0** lo comprueba antes de
   implementar (y si falla, `blocked`), el arranque lo loguea, y la segunda
   señal lo corrige en cuanto entra el primer usuario autenticado. Aun así,
   el humano debe saber que la detección de entorno pasa a ser **una pieza
   con peso en la auditoría** que antes no existía.
1. **No está verificado que Azure inyecte `-NAME`** con el UPN: en local no
   existe la cabecera y en el repositorio no hay ni una referencia a
   `X-MS-CLIENT-PRINCIPAL`. Puede llegar el *display name*. No es un fallo
   (identifica igual) y `/whoami` lo resuelve en un minuto (M1), pero el
   humano debe saber que el valor exacto que acabará en la columna **no se
   puede confirmar hasta desplegar**.
2. **Alcance colateral no acotado del todo**: siete ficheros de tests de
   F-002/F-003/F-004 configuran `DEFAULT_REVIEWER="ana"` y alguno comprueba
   ese valor. **T1 los inventaría antes de tocar nada** en vez de descubrirlos
   a mitad, pero el número final de tests a ajustar no se sabrá hasta ese
   inventario.
3. **`docs/referencia/partes-proyecto.md` §5.4 está desactualizado**: dice que
   `created_by`/`updated_by` llevan `DEFAULT_REVIEWER`. Con H1 sabemos que
   llevan `NULL`. Se corrige en T10.
4. **`.env.example` de sv4 no está versionado** (el `.gitignore` ignora
   `*.example`), igual que pasó con `JORNADAS_ADMIN_ENABLED` en F-016: la
   documentación efectiva de `DEFAULT_REVIEWER` va al docstring y a
   `azure-apps/partes.md` (T11).
5. **Aviso para F-008**: esta feature confía en el texto en claro de la
   cabecera porque lo que decide es una *anotación*, no un permiso. Un **rol**
   leído igual sí sería una decisión de permiso y ahí esa confianza deja de
   ser gratis (`design.md` §8).

## Orden del backlog

1. **F-017** — identidad real de Easy Auth en sv4 (`pending`, prioridad 8).
   **Spec escrita** en `specs/F-017-identidad-easy-auth/` (2026-08-20), a la
   espera de que el humano apruebe las ocho decisiones DA1–DA8. Los once
   puntos exactos, verificados de nuevo contra el árbol: `app.py` líneas
   1675, 1769, 1804, 1859, 1862, 2279, 2305, 2319, 2338, 2348 y 2559.
2. **F-014** — `blocked`, solo la desbloquea RRHH.
3. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-011 jornada reducida
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

## Automejoras del arnés pendientes (⇒ genéricas a `arnes-base`)

> **F-009 se eliminó de `harness/features.json` el 2026-08-20** por decisión
> del humano. Esta lista NO desaparece con ella: sigue siendo el registro de lo
> que hay que portar a `arnes-base`. Varios puntos (1, 2, 3 y 7) son de la
> campaña de mutación y **probablemente ya vengan resueltos en el arnés
> 1.6.0**, que la rehace entera; confirmarlo con
> `progress/analisis_arnes_1.6.2.md` antes de implementar ninguno.
>
> Los **dos puntos originales de F-009**, que NO son de mutación y se habrían
> perdido al borrar la ficha, se conservan aquí:
>
> - **C4 bis**: cuando un fichero del alcance con muchas líneas cambiadas
>   genera **0 mutantes**, exigir evidencia alternativa (fase RED específica
>   sobre ese fichero).
> - **C3/C4 + `init.sh`**: cruzar los imports nuevos de terceros del diff
>   contra el `requirements.txt` del manifiesto de despliegue del servicio que
>   los importa. Habría cazado en automático el crash-loop de `azure-*` de
>   F-002.

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

---

## F-017 · Identidad real de Easy Auth (sv4) — pendientes del humano

Rama `feature/F-017-identidad-easy-auth`. Implementación terminada (T0–T14),
suite en verde, **pendiente de review**. Informe: `progress/impl_F-017.md`.

### ⚠ DECISIÓN PENDIENTE — R14/R15 nombran una columna que nadie escribe

Verificado contra el árbol al implementar T6 (y coincide con lo que encontró
el agente de F-018 por su cuenta):

- `undo_log.actor` **existe pero no la escribe nadie**: `_record_undo` ni
  siquiera acepta un actor.
- Las cuatro operaciones de R14/R15 —los tres borrados y el alta manual—
  **no generan ninguna fila de `undo_log`**. Solo la generan las ediciones.
- `crear_parte_manual` **acepta `by=` y lo ignora**: el parámetro no aparece
  en su cuerpo.

Lo implementado es lo que manda `design.md` §5.2: entregar `_actor(request)`
por el parámetro `by=`. Para los tres borrados eso llega de verdad a
`deleted_by`; para el alta manual se queda en la puerta del repositorio.

**No se resolvió por cuenta propia**, y el motivo es que las dos salidas
posibles se salen del alcance aprobado:

| Salida | Por qué se paró |
|---|---|
| Que los borrados escriban en `undo_log` | Hay que **crear** filas de historial que hoy no existen: payload de restauración, `undo_last` sabiendo deshacerlas y entradas nuevas en el widget de deshacer. Es funcionalidad nueva, y un log de acciones es **F-018** |
| Que `crear_parte_manual` use su `by=` | **No hay dónde escribirlo**: ni `parte_documents` ni `parte_registros` tienen columna `created_by` (solo la tienen `empleado_alias` y `empleado_jornada`). Exigiría **columna nueva** ⇒ cambio de schema en las dos copias gemelas del ORM ⇒ prohibido por la spec y por `CLAUDE.md` |

**Consecuencia que hay que conocer**: el criterio del corte (`autor IS NULL`
⇔ «anterior a F-017») vale para las columnas de autor que sí se escriben,
**no para `undo_log.actor`**, que seguirá siempre a `NULL`. Queda dicho así,
sin redondear, en `docs/referencia/partes-proyecto.md` §5.7 punto 3.

### Verificaciones MANUAL pendientes

- **M1 bis — YA EJECUTADA en T0 (2026-08-20), resultado POSITIVO.** Las cuatro
  variables `CONTAINER_APP_NAME` / `_REVISION` / `_REPLICA_NAME` / `_HOSTNAME`
  **existen** en `ca-sv4-front`. La señal A de R5c es un hecho verificado, no
  un supuesto; no hace falta la alternativa `ENTORNO=produccion`.
  Comprobado **sin volcar el entorno**, una variable por invocación:
  `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_NAME"`
  (ídem con las otras tres). **No usar `printenv` a secas**: vuelca los
  secretos resueltos desde Key Vault.
- **M1 — tras desplegar.** Abrir `https://<fqdn de ca-sv4-front>/whoami` con
  la sesión de Entra iniciada y comprobar tres cosas: `actor` es el correo/UPN
  de quien mira, `origen` es `cabecera-name` y `entorno` es `desplegado`.
  Lecturas posibles:
  - `origen = cabecera-token`: la cabecera `-NAME` no llega y el suplente hace
    su trabajo. Correcto, pero **anótalo**.
  - `origen = sin-identidad-desplegado`: Easy Auth no inyecta nada.
    **Incidente**: la feature funciona (no miente), pero la autenticación del
    portal está rota. Parar y avisar.
  - `origen = local` o `entorno = local`: la detección de R5c ha fallado en
    Azure y el portal estaría firmando filas de producción como locales.
    **Parar y avisar de inmediato**: es el único fallo de esta feature que
    ensucia datos. El campo `senal_despliegue` dice qué se buscó.
- **M2 — tras desplegar.** Aprobar un parte de prueba desde el portal y
  comprobar en la base `partes`:
  `SELECT id, approved_by, approved_at_utc FROM parte_documents WHERE approved_at_utc IS NOT NULL ORDER BY approved_at_utc DESC LIMIT 5;`
- **M3 — tras desplegar.** Borrar una línea de prueba y comprobar:
  `SELECT created_at_utc, action, actor FROM undo_log ORDER BY id DESC LIMIT 5;`
  **Ojo**: por lo dicho arriba, `actor` saldrá `NULL` y el borrado **no**
  generará fila de `undo_log`. La comprobación útil hoy es sobre
  `parte_registros.deleted_by`.
- **M4 — antes y después de desplegar.** Que las filas anteriores sigan
  intactas (R22): el número debe ser **el mismo** las dos veces:
  `SELECT count(*) FROM parte_documents WHERE approved_at_utc IS NOT NULL AND approved_by IS NULL;`

M2, M3 y M4 necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya
está pendiente más arriba en este mismo documento.

### Otros pendientes de F-017

- **La fecha del corte la rellena quien despliegue.**
  `docs/referencia/partes-proyecto.md` §5.7 tiene el hueco marcado como
  `⛔ PENDIENTE: fecha de despliegue`, y
  `tests/test_f017_r23_corte_documentado.py` se pondrá **rojo** cuando se
  cambie, a propósito: obliga a actualizar el test en el mismo trabajo.
- **`DEFAULT_REVIEWER` cambia de significado, no de nombre**: ya no es «quién
  firma el portal» sino la etiqueta de la sesión local (`local:<valor>`).
  Sigue sin estar configurada en Azure y **no hace falta configurarla**.
- **Nota para F-018** (aviso recibido del coordinador, no aplicado aquí a
  propósito): si F-018 llama a `_resolver_identidad` más de una vez por
  petición, saldrán varios WARNING de R5b. Hoy no ocurre —cada endpoint pide
  el actor una sola vez—, así que memoizar sería resolver un problema que aún
  no existe. Cuando F-018 lo necesite, son tres líneas en
  `_resolver_identidad` y no cambia ninguna firma.

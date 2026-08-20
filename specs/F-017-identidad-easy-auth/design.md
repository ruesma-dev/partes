<!-- specs/F-017-identidad-easy-auth/design.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Diseño técnico

> **Base de partida**: `specs/F-017-identidad-easy-auth/requirements.md`, el
> material de `specs/F-016-admin-empleado-jornada/design.md` **§14**, el
> hallazgo **H1** de `progress/current.md` (2026-08-20) y el contraste contra
> la base real de `progress/verif_esquema_partes_20260820.md`.
>
> Todas las líneas de código citadas están verificadas contra el árbol en
> `dev` (`3d6fd7e`) el **2026-08-20**. Se moverán al implementar: **la
> referencia buena es el nombre de la función, no el número**.

---

## 1. Servicios que toca y por qué (LÍMITE DE SERVICIO)

| Servicio | ¿Se toca? | Por qué |
|---|---|---|
| **sv4 `partes-front`** | **SÍ, y solo él** | Es el **único servicio con un humano delante** y el único detrás de Easy Auth. La identidad viaja en cabeceras HTTP que solo existen en su ingress. Todas las columnas de autor que esta feature rellena las escribe sv4. |
| sv1 `partes-email` | **NO** | Poller de buzón sin HTTP. No hay usuario que identificar. |
| sv2 `partes-api` | **NO** | Worker KEDA de cola. Ídem. |
| sv3 `partes-persistencia` | **NO** | Worker KEDA de cola. **Escribe `created_by`/`deleted_by` de la ingesta automática**, y ahí el autor no es una persona: es el pipeline. Confundir las dos cosas sería falsear la auditoría. Ver DA7. |
| sv5 `partes-transfer` | **NO** | Recibe el campo `usuario` en el payload —campo que **ya existe** (`interface_adapters/api/app.py:56`, `Optional[str]`)— y **solo lo escribe en su log** (`application/pipelines/registro_pipeline.py:341`). Empezará a loguear un nombre real **sin un solo cambio de código**. Verificado: `usuario` no llega a ninguna columna de Sigrid. |
| `sigrid-api` | **NO** | Ni una consulta nueva. |
| PostgreSQL `partes` | **NO** | **Cero cambios de schema**: esta feature rellena columnas que ya existen. Ver §3. |
| Infra / Azure | **NO** | Easy Auth ya está configurado en `ca-sv4-front` (verificado el 2026-08-20: `HTTP 401` sin cookie). No hay variable nueva que crear. |

**Señal de alarma**: si durante la implementación hace falta tocar un
servicio distinto de sv4, o añadir una columna, el diseño se ha torcido.
**Parar y consultar** (regla dura de `CLAUDE.md`).

**Copias gemelas**: `infrastructure/database/orm_models.py` está duplicado en
sv3 y sv4 y `tests/test_f010_orm_models_gemelos.py` lo vigila. Esta feature
**no lo toca**, así que la regla no se activa. Si alguien lo tocara, tendría
que tocar las dos — y eso ya sería otra feature.

---

## 2. La decisión central: qué cabecera manda

Easy Auth (aquí, el sidecar de autenticación de Container Apps) inyecta a la
aplicación varias cabeceras. Las tres que importan:

| Cabecera | Qué trae | Coste de leerla | Modos de fallo |
|---|---|---|---|
| `X-MS-CLIENT-PRINCIPAL-NAME` | El nombre del principal **en claro**. Con Entra ID, normalmente el UPN (`nombre.apellido@dominio`) | Cero: es texto | Puede llegar con el *display name* en lugar del UPN según cómo esté mapeado el claim de nombre; puede no llegar |
| `X-MS-CLIENT-PRINCIPAL` | **Base64** de un JSON `{"auth_typ":…,"claims":[{"typ":…,"val":…}]}` con el juego completo de claims | Decodificar + parsear + elegir claim | Base64 inválido, JSON inválido, estructura distinta, claim ausente. **Cuatro formas de reventar una petición que hoy funciona** |
| `X-MS-CLIENT-PRINCIPAL-ID` | El `oid`/`sub`: identificador **inmutable** del usuario en el tenant, en claro | Cero | Es un GUID: ilegible para un humano |

**Decisión DA1 — manda `X-MS-CLIENT-PRINCIPAL-NAME`; el token base64 es solo
el suplente.**

Argumentos:

1. **Lo que se guarda lo van a leer personas.** La columna `approved_by` se
   pinta literalmente en `templates/parte_detail.html:79` («Aprobado por
   …») y `created_by`/`updated_by` en `templates/admin_jornadas.html:200`.
   Un GUID ahí no informa a nadie; `nombre.apellido@dominio` sí.
2. **Es la vía sin modos de fallo.** Leer una cabecera de texto no puede
   lanzar. Decodificar base64 sí. En una feature cuyo único cometido es
   *anotar* algo, el mecanismo de anotación **jamás** puede tumbar la
   operación anotada (R3, R7).
3. **El suplente cubre el riesgo real.** El riesgo conocido de `-NAME` es que
   traiga el display name en vez del UPN. Ese caso NO es un fallo (sigue
   identificando a la persona) y, si el humano prefiere el UPN, la
   verificación **M1** lo detecta desde el navegador y el arreglo es cambiar
   el orden de preferencia dentro de una función pura, sin tocar ninguna ruta.
4. **El `oid` no se guarda porque no hay dónde.** Ver DA2.

**Decisión DA2 — se guarda el UPN, no el `oid`, y no se guardan los dos.**

Se descartó `"upn|oid"` en la misma columna: son 120 caracteres en las
columnas más estrechas (§3), el valor dejaría de ser legible y de ser
comparable con las filas anteriores, y nadie ha pedido identidad inmutable.

**Consecuencia asumida, y hay que escribirla**: si una persona cambia de UPN
(matrimonio, cambio de apellido, cambio de dominio), las filas antiguas
conservan el UPN de entonces y no se pueden encadenar automáticamente con las
nuevas. **Para una auditoría esto es correcto, no un defecto**: una firma
registra quién era esa persona en ese momento. Si el humano quiere
trazabilidad inmutable, la solución es una columna `actor_oid` **en la tabla
propia de F-018**, no ensuciar estas.

**Decisión DA3 — se normaliza a minúsculas.** Los UPN de Entra son
insensibles a mayúsculas, así que `Nombre.Apellido@…` y `nombre.apellido@…`
son la misma persona. Si se guardan tal cual llegan, un `GROUP BY approved_by`
devuelve dos personas donde hay una. Se normaliza en el único sitio donde se
resuelve la identidad y nunca más se vuelve a pensar en ello.

---

## 3. Anchos de columna: la comprobación pedida

Contado en `services/partes-front/infrastructure/database/orm_models.py`
(2026-08-20) y **confirmado contra la base real** en
`progress/verif_esquema_partes_20260820.md`:

| Tabla | Columna | Tipo | Quién la escribe |
|---|---|---|---|
| `parte_documents` | `approved_by` | `String(255)` | sv4 (R12) |
| `parte_documents` | `deleted_by` | `String(255)` | sv4 (R13) |
| `parte_registros` | `deleted_by` | `String(255)` | sv4 |
| `parte_registros` | `sigrid_registrado_by` | `String(255)` | sv4 (R16) |
| `empleado_alias` | `created_by` | `String(120)` | sv4 (Conciliar) |
| `empleado_jornada` | `created_by`, `updated_by` | `String(120)` | sv4 (R19) |
| `undo_log` | `actor` | `String(120)` | sv4 — **columna que hoy no escribe nadie**; R14/R15 enmendados el 2026-08-20 no la usan (ver `requirements.md`). Se mantiene en la tabla de anchos porque sigue siendo la columna de autor más estrecha del esquema y por tanto la que fija el truncado a 120. |

**Conclusión: el mínimo común es 120, y sobra.** Un UPN cabe de largo (los del
tenant rondan los 25–35 caracteres; el límite teórico de un UPN son 113 según
el propio Entra). Aun así, **la longitud no se deja al azar**: el helper
trunca a 120 (R4/R8), de una vez y para todos los consumidores. Así ninguna de
las siete columnas puede recibir un valor que no le quepa, y **no hace falta
tocar el schema** — que es exactamente lo que esta feature quiere evitar.

Se descartó ampliar las columnas de 120 a 255 «por simetría»: sería un cambio
de schema en las dos copias del ORM, en la base compartida, sin ningún caso de
uso que lo justifique.

---

## 4. El fallback cuando no llega la cabecera

En local **no hay Easy Auth**: no hay sidecar, no hay cabeceras. Y esto no es
teórico — el humano arranca sv4 en local **contra el PostgreSQL real**
(así se hicieron las verificaciones del 2026-08-20). Es decir: **una sesión
local puede escribir filas en la base de producción**.

> **Enmienda del humano (2026-08-20), incorporada.** La primera versión de
> esta sección disparaba el fallback por **ausencia de cabecera**, sin mirar
> dónde corría el proceso. Defecto real: si Easy Auth dejara de inyectar la
> cabecera en Azure —mal configurado, una ruta excluida, un cambio de
> plataforma—, el portal escribiría `local:sin-identidad` **en producción**.
> Eso no es «honesto y evidente»: **afirma algo falso**, que la fila vino de
> una sesión local. Un dato de auditoría que miente sobre su origen es peor
> que uno vacío. Y encima taparía un incidente de autenticación en una
> columna, en silencio. Los dos casos van separados.

Tabla de resolución completa:

| Cabeceras | Entorno | Actor | `origen` | Log |
|---|---|---|---|---|
| `…-NAME` con valor | cualquiera | el principal normalizado | `cabecera-name` | — |
| solo `X-MS-CLIENT-PRINCIPAL` | cualquiera | claim preferido normalizado | `cabecera-token` | — |
| ninguna | **no desplegado** | `local:<DEFAULT_REVIEWER>` o `local:sin-identidad` | `local` | — |
| ninguna | **desplegado** | **`sin-identidad`** (sin prefijo) | `sin-identidad-desplegado` | **WARNING por petición** |
| reservada (invade el espacio de nombres) | cualquiera | se descarta ⇒ fila anterior según entorno | `local` / `sin-identidad-desplegado` | WARNING |

En los cuatro casos **la operación se completa**. Ese principio viene de F-016
y no lo toca la enmienda: no saber quién fue no es motivo para perder el
cambio. Lo que cambia es **el valor** y **el aviso**.

**Decisión DA4 (enmendada) — el fallback tiene DOS ramas, y solo la de
desarrollo lleva el prefijo `local:`.**

1. **Ninguna rama puede confundirse con un usuario real**, y no por la forma
   del texto sino **por construcción**: R6 descarta cualquier valor que llegue
   por cabecera invadiendo el espacio reservado (`local:*` o exactamente
   `sin-identidad`). Los valores reservados **solo puede producirlos el
   resolutor**. Como refuerzo, ni uno ni otro tienen forma de UPN: `:` no es
   un carácter válido en un UPN de Entra, y `sin-identidad` no lleva `@`.
2. **Ninguna rama puede confundirse con «no se sabe».** `NULL` ya tiene
   dueño: las filas anteriores al corte (R7, R22). Ni `local:…` ni
   `sin-identidad` son `NULL`, así que el criterio del corte sigue siendo
   exacto.
3. **`local:` afirma algo, y por eso hay que merecerlo.** Decir «esto lo hizo
   una sesión de desarrollo» es una afirmación sobre el origen del dato. Solo
   se escribe cuando el proceso **ha comprobado** que no está desplegado.
   `sin-identidad` no afirma nada sobre el origen: dice exactamente lo que
   pasó, que la petición llegó sin identidad.
4. **El caso desplegado es un incidente y se trata como tal**: WARNING por
   petición (no una nota de arranque), para que se vea en Log Analytics con el
   mismo filtro con el que ya se leen los arranques.

### 4.1 Cómo se sabe si el proceso está desplegado (R5c)

Sin variable nueva y sin tocar Azure, como pide la enmienda. Dos señales, en
`OR`:

**Señal A — el entorno del proceso.** Azure Container Apps inyecta en todos
sus contenedores `CONTAINER_APP_NAME`, `CONTAINER_APP_REVISION`,
`CONTAINER_APP_REPLICA_NAME` y `CONTAINER_APP_HOSTNAME`. En un puesto local no
existen. Presencia de cualquiera ⇒ desplegado.

> **⚠ SUPUESTO NO VERIFICADO EN ESTE REPOSITORIO.** Comprobado el 2026-08-20:
> **ningún servicio del monorepo lee esas variables** y **ningún script de
> `infra/` las declara** (`grep` sobre `*.py` y `*.ps1`). Es comportamiento
> documentado de la plataforma, no un hecho verificado en este despliegue. Por
> eso: (a) la verificación **M1 bis** de `requirements.md` §4 se puede ejecutar
> **antes** de implementar, con `az containerapp exec … printenv`; (b) `R9`
> obliga a loguear al arranque **qué señal se encontró**; y (c) existe la
> señal B.

**Señal B — la evidencia acumulada.** Si el proceso ya ha atendido **alguna**
petición con cabecera de Easy Auth desde su arranque, está detrás de Easy
Auth: eso ya no es un supuesto, es un hecho observado. Un `bool` en
`app.state`, puesto a `True` la primera vez que se ve una cabecera.

**Por qué la disyunción y no solo A.** El fallo de detección es
**asimétrico**, y conviene verlo escrito:

| Fallo | Consecuencia | Gravedad |
|---|---|---|
| Creerse **local** estando desplegado (A no llega) | Se escriben filas de producción firmadas `local:…`: **exactamente la mentira que la enmienda viene a evitar** | **Grave: ensucia datos** |
| Creerse **desplegado** estando en local (alguien exporta la variable) | Se escribe `sin-identidad` y salen WARNINGs en un puesto de desarrollo | Inocua |

La señal B solo puede mover el resultado hacia el lado seguro, nunca hacia el
peligroso: no puede convertir un proceso local en «desplegado» salvo que
alguien fabrique cabeceras de Easy Auth a mano contra su propio portal, y el
resultado de hacerlo sería `sin-identidad`, que es inocuo. Cuesta tres líneas
y cierra el único agujero de A.

**Alternativa descartada**: una variable `ENTORNO=produccion` en el Container
App. Sería la señal más fiable, pero obliga a tocar Azure —la enmienda lo
excluye explícitamente— y a mantener sincronizado un valor que la plataforma
ya sabe. Si M1 bis demostrara que A no existe en este entorno, esta es la
propuesta de repuesto y hay que consultarla con el humano antes de
implementar, no resolverla por cuenta propia.

**Decisión DA5 — `DEFAULT_REVIEWER` se queda, con el significado cambiado.**
Ya no es «quién firma el portal» sino «cómo se etiqueta la sesión local». No
se renombra: renombrar una variable de entorno obliga a tocar Azure y aquí no
está ni configurada. Sí se cambia su documentación (§5, ficheros a modificar).
`services/partes-front/.env.example` **no está versionado** (el `.gitignore`
de sv4 ignora `*.example`, misma situación que `JORNADAS_ADMIN_ENABLED` en
F-016): se actualiza en el árbol local, pero la documentación **efectiva** es
el docstring de `identidad.py` y `azure-apps/partes.md`.

---

## 5. Ficheros

### 5.1 A crear

| Fichero | Capa | Qué es |
|---|---|---|
| `services/partes-front/interface_adapters/web/identidad.py` | `interface_adapters` (adaptador web) | **Función pura** que traduce cabeceras HTTP a un actor. Sin FastAPI, sin `Settings`, sin I/O: entra un `Mapping[str, str]` y una etiqueta de fallback, sale `(actor, origen)`. Testeable sin levantar la app. |
| `services/partes-front/tests/test_f017_identidad.py` | tests | R1–R9 (menos R5c), R20, R21 |
| `services/partes-front/tests/test_f017_entorno.py` | tests | R5c: las dos señales de despliegue, las dos direcciones del fallo y la asimetría de §4.1 |
| `services/partes-front/tests/test_f017_punto_unico.py` | tests | R10, R11 |
| `services/partes-front/tests/test_f017_endpoints_firmados.py` | tests | R12–R15 |
| `services/partes-front/tests/test_f017_aprobacion_firmada.py` | tests | R16–R18 |
| `tests/test_f017_r22_sin_reescritura_historica.py` | tests (raíz) | R22 |
| `tests/test_f017_r23_corte_documentado.py` | tests (raíz) | R23 |

**Por qué la lógica va en `interface_adapters/web/` y no en `domain/`**: leer
cabeceras HTTP es, por definición, un detalle de transporte. El dominio de
este proyecto son partes, líneas, obras y jornadas; «quién manda la petición»
no es una regla de negocio. Colocarlo en `domain/` haría que el dominio
supiera qué es una cabecera de Azure — justo lo que la hexagonal prohíbe.
Se descartó también `infrastructure/`: no hay adaptador a ningún sistema
externo, solo el parseo del transporte que ya entra por `web/`.

### 5.2 A modificar

**`services/partes-front/interface_adapters/web/app.py`** — el único fichero
de producción que cambia. Doce puntos:

| # | Función / ruta (línea el 2026-08-20) | Qué cambia |
|---|---|---|
| 0 | `_actor` (477) | **Solo su interior** y su docstring, como prometió F-016. Firma **intacta**: `def _actor(request: Request) -> str \| None`. Delega en `_resolver_identidad` (§7), función nueva **junto** a él. Y `build_app` inicializa `app.state.easy_auth_visto = False` |
| 1 | `_payload_registro` (1654 → campo `usuario`, 1675) | Nuevo parámetro `*, actor: str \| None`. Sus **dos** llamadores ya tienen `request` |
| 2 | `_trazar` (1758 → `usuario=`, 1769) | Nuevo parámetro `*, actor: str \| None` |
| 3 | `aprobar_ejecutar` (1804, log de forzado) | `settings.default_reviewer or "(sin usuario)"` → el actor (que nunca es vacío, R7; el `or` se puede quitar) |
| 4 | `aprobar_encolar` (1859) `publisher.publicar(..., usuario=)` | actor |
| 5 | `aprobar_encolar` (1862) `marcar_registros_encolado(..., usuario=)` | actor |
| 6 | `approve_document` (2279) | **Añadir `request: Request` a la firma** + `approved_by=_actor(request)` |
| 7 | `delete_document` (2305) | **Añadir `request: Request`** + `deleted_by=_actor(request)` |
| 8 | `api_registro_delete` (2319) | **Añadir `request: Request`** + `by=_actor(request)` |
| 9 | `api_obra_delete` (2338) | **Añadir `request: Request`** + `by=_actor(request)` |
| 10 | `api_trabajador_delete` (2348) | **Añadir `request: Request`** + `by=_actor(request)` |
| 11 | `api_partes_nuevo` (2559) | Ya tiene `request`: `by=_actor(request)` |
| 12 | ruta nueva `GET /whoami` | R21 |

**Cinco de las once no tienen `request` en su firma.** Añadirlo es seguro:
FastAPI inyecta `Request` por anotación de tipo y **no** lo trata como
parámetro de query, path ni body, así que ni el contrato HTTP ni el JS
cambian. `approve_document` y `delete_document` tienen además parámetros
`Form(default=…)`: `request: Request` se pone **el primero** y los `Form` se
quedan como están.

**`services/partes-front/tests/test_f016_endpoints_admin_jornadas.py`** — la
trampa que dejó localizada el reviewer de F-016. Ver §6.

**`docs/referencia/partes-proyecto.md`** — R23. Dos toques:
§5.4 (`empleado_jornada`), donde hoy dice literalmente *«`created_by` /
`updated_by` llevan hoy `DEFAULT_REVIEWER` … el usuario real de Easy Auth es
trabajo de F-017»*, y un apartado nuevo **«Corte de auditoría (F-017)»** en
§5, que vale para las siete columnas de autor a la vez.

**`docs/ARCHITECTURE.md`** — una entrada corta en la lista de reglas de
dominio: la identidad del portal se resuelve en un único punto y `NULL`
significa «anterior a F-017».

**`C:\Users\pgris\PycharmProjects\azure-apps\partes.md`** — regla de
mantenimiento de `CLAUDE.md`: cambia el significado de una variable de entorno
de sv4 (`DEFAULT_REVIEWER`) y aparece una ruta nueva (`/whoami`). Se actualiza
en el mismo trabajo. **Repo distinto ⇒ commit aparte**, en su propio
repositorio, sin `push` (es local por decisión del humano).

### 5.3 Ficheros que NO se tocan (los colindantes que tientan)

| Fichero | Por qué NO |
|---|---|
| `infrastructure/database/orm_models.py` (sv3 **y** sv4) | Cero cambios de schema. Tocarlo obligaría a tocar las dos copias y a un DDL en la base compartida, sin ninguna necesidad (§3) |
| `infrastructure/database/parte_repository.py` | Ya recibe el autor por parámetro (`by=`, `usuario=`, `approved_by=`, `deleted_by=`, `actor=`). El repositorio **no debe saber** qué es una cabecera HTTP: si aparece la tentación de leer la identidad ahí, el diseño se torció (R10) |
| `interface_adapters/workers/resultado_consumer.py` | R18: es un hilo sin petición. Toma `usuario` del sobre, que **ya** viaja firmado desde `aprobar_encolar` (punto 4). Su `getattr(settings, "default_reviewer", None)` final es el último recurso para sobres antiguos y se queda tal cual |
| `templates/parte_detail.html`, `templates/admin_jornadas.html` | Empiezan a pintar un nombre real **sin tocarlas**. Se descartó acortar el UPN a la parte local (`nombre.apellido`) para que quepa mejor: es una decisión de presentación, discutible, y esta feature no cambia pantallas (fuera de alcance §2.5) |
| `static/app.js`, `templates/base.html` | El widget de deshacer **no pinta `actor`** (verificado: no hay ni una referencia a `actor` en las plantillas ni en el JS). Nada que ajustar |
| `config/settings.py` | `default_reviewer` sigue existiendo con el mismo nombre y tipo (DA5). Solo cambia lo que significa, y eso se documenta, no se codifica |
| Todo sv1, sv2, sv3, sv5 e `infra/` | §1 |

---

## 6. La trampa de F-016: `test_f016_r13_auditoria`

El reviewer de F-016 avisó y tiene razón a medias; conviene precisarlo porque
determina la tarea.

El test (`test_f016_endpoints_admin_jornadas.py:519`) hace
`monkeypatch.setenv("DEFAULT_REVIEWER", "quien-firma")` y espera
`created_by == "quien-firma"`. Con el diseño de esta spec, el TestClient no
manda cabeceras de Easy Auth ⇒ cae al fallback ⇒ el valor sellado será
**`local:quien-firma`** ⇒ **el test se pone ROJO**. Exactamente lo anunciado.

**Decisión DA6 — se pasa a fabricar la cabecera, no a parchear el helper.**

Parchear `_actor` es **imposible sin retorcer el código**: es una clausura
definida dentro de `build_app`, no un símbolo de módulo, así que no hay nada
que `monkeypatch.setattr` pueda alcanzar. Convertirlo en función de módulo o
en dependencia inyectable solo para poder parchearlo sería deformar el diseño
para complacer al test — y encima probaría menos: el camino que hay que
verificar es precisamente **cabecera → columna**.

Cambios concretos en ese fichero:

1. Helper local `_como(usuario)` que devuelve
   `{"X-MS-CLIENT-PRINCIPAL-NAME": usuario}`, y las peticiones del test pasan
   a llevar `headers=_como("quien.firma@ejemplo.invalid")`.
   **Dominio `.invalid`** (RFC 2606): en el repositorio no entra ningún correo
   real de una persona.
2. `test_f016_r13_auditoria` pasa a comprobar el **principal de la cabecera**
   (y se renombra su docstring: ya no se parchea por resultado). Sigue
   cubriendo R13 de F-016 y pasa a cubrir **R19 de F-017**.
3. `test_f016_r13_sin_default_reviewer_se_sella_nulo_y_no_falla` **cambia de
   nombre y de aserción**: ya no se sella `NULL` (R7). Pasa a ser
   `test_f016_r13_sin_cabecera_se_sella_el_actor_local`, comprobando
   `created_by == "local:sin-identidad"`. Es el mismo requisito de F-016 —«no
   saber quién fue no puede perder el cambio»— con la respuesta actualizada.
4. `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio` **sigue verde sin
   tocarlo**, y es la razón de que la firma de `_actor` sea intangible:
   afirma `fuente.count("def _actor(request: Request)") == 1`,
   `bloque.count("_actor(request)") == 5` y que `settings.default_reviewer` no
   aparece en el bloque de F-016. El diseño de esta spec respeta las tres.
   **Si ese test se pone rojo, es que se ha roto el punto único.**

**Ningún otro test de sv4 debería ponerse rojo**, pero varios rondan la zona
(`test_f002_aprobar_encolar.py`, `test_f002_degradacion.py`,
`test_f003_r23_bloqueo_registro.py`, `test_f004_endpoints_congelados.py`,
`test_f002_mutantes.py`, `test_f002_resultado_consumer.py`,
`test_f002_credenciales_y_arranque.py`): todos configuran
`DEFAULT_REVIEWER="ana"` y algunos comprueban ese valor en el payload de sv5 o
en las marcas. **T1 de `tasks.md` es ejecutar la suite y listar los rojos
reales antes de tocar nada**, para que el implementer no descubra el alcance a
mitad. Regla para arreglarlos: si el test comprueba *quién firma*, se le
pone cabecera; si solo necesita *que haya algún valor*, `local:ana` es una
respuesta válida y basta con actualizar el literal esperado.

---

## 7. Firmas nuevas

### `interface_adapters/web/identidad.py`

```python
# interface_adapters/web/identidad.py

CABECERA_NOMBRE = "X-MS-CLIENT-PRINCIPAL-NAME"
CABECERA_TOKEN = "X-MS-CLIENT-PRINCIPAL"
CABECERA_ID = "X-MS-CLIENT-PRINCIPAL-ID"     # solo para /whoami (R21)

PREFIJO_LOCAL = "local:"
ACTOR_LOCAL_SIN_NOMBRE = "local:sin-identidad"
ACTOR_SIN_IDENTIDAD = "sin-identidad"        # R5b: desplegado y sin cabecera
ACTOR_MAX_LEN = 120          # la columna mas estrecha: undo_log.actor

#: R5c, senal A. Variables que Azure Container Apps inyecta en todos sus
#: contenedores y que en un puesto local no existen. SUPUESTO DE PLATAFORMA:
#: verificar con M1 bis (design.md §4.1) antes de fiarse.
VARIABLES_DESPLIEGUE: tuple[str, ...] = (
    "CONTAINER_APP_NAME", "CONTAINER_APP_REVISION",
    "CONTAINER_APP_REPLICA_NAME", "CONTAINER_APP_HOSTNAME",
)

CLAIMS_PREFERIDOS: tuple[str, ...] = (
    "preferred_username", "upn", "email", "emails", "name",
)


def normalizar_actor(valor: str | None) -> str | None:
    """R4: recorta, quita caracteres de control, minusculas, 120."""


def es_actor_reservado(valor: str | None) -> bool:
    """R6: `local:*` o exactamente `sin-identidad`, ya normalizado."""


def actor_desde_token(token: str | None) -> str | None:
    """R2/R3: base64 -> JSON -> primer claim preferido. NUNCA lanza."""


def senal_de_despliegue(
    entorno: Mapping[str, str], *, cabecera_vista: bool = False,
) -> str | None:
    """R5c: devuelve el NOMBRE de la senal que prueba el despliegue.

    El nombre de la variable encontrada (senal A), `'cabecera-vista'`
    (senal B) o None si no hay ninguna. Devolver el nombre y no un bool
    es lo que permite a R9 y a /whoami decir POR QUE se creyo desplegado.
    """


def actor_desde_cabeceras(
    cabeceras: Mapping[str, str], *, fallback: str | None,
    desplegado: bool,
) -> tuple[str, str]:
    """R1/R2/R5/R5b/R6/R7: devuelve (actor, origen).

    `origen`: 'cabecera-name' | 'cabecera-token' | 'local' |
    'sin-identidad-desplegado'. El actor NUNCA es vacio ni None.
    """
```

`actor_desde_cabeceras` recibe un `Mapping` (no un `Request`) y un `bool`
(no lee `os.environ`) a propósito: así la función es **pura** —no importa
FastAPI, no toca el proceso— y las dos decisiones se prueban por separado.
`request.headers` de Starlette ya es un mapping insensible a mayúsculas.
Quien lee el entorno de verdad es `senal_de_despliegue`, y también recibe el
`Mapping`: en los tests entra un diccionario, no `monkeypatch.setenv`.

### `_actor` dentro de `app.py` (firma intacta)

```python
def _resolver_identidad(request: Request) -> tuple[str, str]:
    """Resuelve (actor, origen) y mantiene la senal B viva (R5c).

    Vive junto a `_actor` y NO lo sustituye: `_actor` es la firma que
    consumen los once puntos y la que vigila el guardian de F-016.
    """
    senal = senal_de_despliegue(
        os.environ, cabecera_vista=app.state.easy_auth_visto)
    actor, origen = actor_desde_cabeceras(
        request.headers, fallback=settings.default_reviewer,
        desplegado=senal is not None)
    if origen.startswith("cabecera"):
        app.state.easy_auth_visto = True          # senal B
    elif origen == "sin-identidad-desplegado":
        logger.warning(
            "[identidad] peticion SIN identidad de Easy Auth estando "
            "desplegado (senal=%s, ruta=%s): se sella '%s'. Revisa la "
            "autenticacion del portal.", senal, request.url.path, actor)
    return actor, origen


def _actor(request: Request) -> str | None:
    """Quien firma el cambio. PUNTO UNICO de identidad del portal (R10).

    F-016 dejo escrito que aqui solo cambiaria el INTERIOR: asi ha sido.
    """
    actor, _origen = _resolver_identidad(request)
    return actor
```

`app.state.easy_auth_visto` se inicializa a `False` en `build_app`, junto a
`app.state.tables_ready`. Es por proceso, no compartido entre réplicas: sv4
corre con `--min-replicas 1 --max-replicas 2`, así que como mucho una segunda
réplica tarda una petición autenticada en «aprender» lo mismo. Irrelevante,
porque la señal A ya la tiene resuelta desde el arranque; B solo existe por si
A falla.

Se mantiene el tipo de retorno `str | None` aunque hoy nunca devuelva `None`
(R7): es el tipo que aceptan las siete columnas y los repositorios, y estrechar
la firma obligaría a tocar `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio`,
que compara el texto exacto `def _actor(request: Request)`.

### `GET /whoami` (R21)

```python
@app.get("/whoami")
def whoami(request: Request) -> dict[str, Any]:
    senal = senal_de_despliegue(
        os.environ, cabecera_vista=app.state.easy_auth_visto)
    actor, origen = _resolver_identidad(request)
    return {
        "actor": actor,
        "origen": origen,                  # la RAMA por la que salio
        "entorno": "desplegado" if senal else "local",
        "senal_despliegue": senal,         # POR QUE se cree desplegado
        "cabeceras_easy_auth": [           # NOMBRES, nunca valores
            c for c in (CABECERA_NOMBRE, CABECERA_TOKEN, CABECERA_ID)
            if c.lower() in request.headers
        ],
    }
```

**Por qué existe `/whoami` y por qué es tan aburrida.** Sin ella, la
verificación M1 obliga a aprobar un parte de verdad y a mirar la base — y si
sale mal, ya has escrito la fila. Con ella, el humano abre una URL y ve en un
segundo si la cabecera llega, cuál, y **por qué rama salió el actor**.
Devuelve **la identidad de quien pregunta y nada más**: ni el token, ni los
claims, ni los valores de las cabeceras, ni ningún dato de otro usuario.

Con la enmienda, `/whoami` gana el papel que antes no tenía: es **el único
sitio donde se puede comprobar la detección de R5c sin escribir una fila**.
`entorno` y `senal_despliegue` son precisamente lo que M1 mira para descartar
el fallo grave (creerse local estando desplegado). Los campos `entorno` y
`senal_despliegue` no revelan nada sensible: el nombre de una variable de
plataforma, no su valor.

---

## 8. Seguridad: ¿se puede falsificar la cabecera?

Hay que decirlo por escrito porque F-008 se apoyará en el mismo mecanismo.

- **Hoy, no.** `ca-sv4-front` tiene ingress externo con Easy Auth y
  `unauthenticatedClientAction` rechazando: verificado el 2026-08-20, sin
  cookie responde `HTTP 401`. El contenedor de autenticación se pone delante y
  **sobrescribe** las cabeceras `X-MS-CLIENT-PRINCIPAL*` que venga poniendo el
  cliente. La aplicación nunca ve las del atacante.
- **El día que eso cambie, sí.** Si alguien pusiera la autenticación en modo
  «permitir anónimo» delegando la decisión en la app, cualquiera podría
  mandar `X-MS-CLIENT-PRINCIPAL-NAME: quien-sea` y firmar con ese nombre.
- **Riesgo aceptado y su motivo**: lo que esta feature decide con la cabecera
  es una **anotación**, no un permiso. Un atacante que ya está dentro del
  portal puede hoy aprobar, borrar y editar **sin dejar nombre ninguno**;
  después de esta feature podría dejar un nombre falso. No se abre ninguna
  puerta nueva.
- **Aviso explícito para F-008**: un **rol** leído de estas cabeceras SÍ sería
  una decisión de permiso, y ahí la confianza en el sidecar deja de ser
  gratis. F-008 debe validar el token, no fiarse del texto en claro.

---

## 9. Las filas históricas (R22)

**No se reescribe ni una.** Ni migración, ni `UPDATE`, ni valor inventado.

El hallazgo H1 hace esta decisión **más fácil** de lo que preveía F-016 §14.
Aquel material asumía un tramo de filas firmadas con un genérico conviviendo
con las reales, y planteaba si «traducirlas». Pero no hay genérico: **hay
ausencia**. Y `NULL` ya dice la verdad —«no se sabe»—, así que:

- **No hay nada que traducir**: rellenar esos `NULL` con cualquier nombre
  sería literalmente **inventar una firma**. Eso no es una migración, es
  falsificar una auditoría.
- **El corte queda perfectamente nítido, y gratis.** Con R7 (siempre hay
  actor), a partir del despliegue **ninguna fila nueva puede quedar en
  `NULL`**. Por tanto: `autor IS NULL` ⇔ «anterior a F-017». Es un criterio
  exacto, comprobable con una consulta y sin necesidad de guardar la fecha en
  ninguna parte.
- **Se documenta** en `docs/referencia/partes-proyecto.md` con la fecha real
  de despliegue (R23), para que dentro de un año nadie lea esos `NULL` como un
  fallo del sistema. Como el despliegue lo hace el humano y no los agentes, la
  redacción deja el hueco de la fecha marcado con un `⛔ PENDIENTE: fecha de
  despliegue` y **T10** lo recuerda en `progress/current.md`.

Alternativa descartada: sellar las filas antiguas con `desconocido-pre-f017`.
Añade ruido, obliga a un `UPDATE` masivo sobre la base compartida y no aporta
nada que `NULL` no diga ya.

---

## 10. Cómo se prueba sin red ni BBDD

Igual que F-016: `TestClient`, `FabricaSesionSqlite` (SQLite en memoria con el
ORM real), `Settings(_env_file=None)` y dobles. **Ni un test toca red, ni
PostgreSQL, ni Sigrid, ni colas, ni sv5.**

La cabecera se fabrica y ya está:

```python
def _como(usuario: str) -> dict[str, str]:
    return {"X-MS-CLIENT-PRINCIPAL-NAME": usuario}

cliente.post("/documents/abc/approve", headers=_como("ana@ejemplo.invalid"))
```

Y el token, con `base64.b64encode(json.dumps({...}).encode())`.

**El entorno también se fabrica, no se toca**: `senal_de_despliegue` recibe un
`Mapping`, así que los tests de R5c le pasan `{"CONTAINER_APP_NAME": "ca-sv4-front"}`
o `{}` directamente. Para los tests que necesitan la app entera «desplegada»,
`monkeypatch.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")`, que se
deshace solo al acabar el test.

**Un test que hay que escribir aunque incomode** (R5b, fase RED): con el
entorno marcado como desplegado y **sin** cabecera, aprobar un parte y
comprobar las tres cosas a la vez — que `approved_by` es `sin-identidad`, que
**no** empieza por `local:`, y que el parte **queda aprobado igualmente**. Es
el requisito que la enmienda añade y el que un implementer con prisa se
saltaría por parecer un caso raro.

**Datos de prueba**: dominio `ejemplo.invalid` (RFC 2606) y nombres
inventados. **En la spec, en los tests y en los commits no entra ni un correo
real de una persona, ni un DNI, ni una IP** (regla dura de `CLAUDE.md`).

Lo único que NO se puede probar en local es que Azure inyecte la cabecera: eso
son las verificaciones **M1–M4** de `requirements.md` §4.

---

## 11. Riesgos y decisiones

| # | Decisión / riesgo | Resolución |
|---|---|---|
| **DA1** | ¿`-NAME` o el token base64? | `-NAME` manda, token de suplente. §2 |
| **DA2** | ¿UPN u `oid`? | UPN. El `oid` es ilegible y no hay columna; identidad inmutable ⇒ F-018. §2 |
| **DA3** | ¿Se normaliza a minúsculas? | Sí: los UPN son insensibles a mayúsculas y si no, `GROUP BY` miente. §2 |
| **DA4** | ¿Qué se escribe cuando no llega la cabecera? | **Dos ramas** (enmienda del humano, 2026-08-20): sin desplegar, `local:<algo>`; **desplegado, `sin-identidad` + WARNING por petición**. Escribir `local:` en producción sería afirmar un origen falso, y taparía una caída de la autenticación. §4 |
| **DA4 bis** | ¿Cómo se sabe si está desplegado, sin variable nueva ni tocar Azure? | `CONTAINER_APP_*` presente **o** haber visto ya una cabecera de Easy Auth desde el arranque. §4.1. **Supuesto de plataforma sin verificar en este repo** ⇒ M1 bis |
| **DA5** | ¿Se elimina `DEFAULT_REVIEWER`? | No: se queda con significado nuevo (etiqueta de sesión local). Renombrarla obligaría a tocar Azure para nada. §4 |
| **DA6** | ¿Se inyecta o se parchea el helper en el test de F-016? | Ninguna de las dos: **se fabrica la cabecera**. `_actor` es una clausura, no hay nada que parchear, y el camino a probar es cabecera→columna. §6 |
| **DA7** | ¿Y las filas que escribe **sv3** (ingesta automática)? | **No se tocan.** Ahí el autor no es una persona. Si en el futuro se quiere distinguir el pipeline de un humano, el sitio es F-018, no esta feature |
| **DA8** | ¿`/whoami` es alcance de más? | Se propone porque hace verificable M1 sin escribir en la base. Es la pieza más fácil de retirar si el humano dice que no |
| **R1** | Añadir `request: Request` a cinco firmas rompe algún contrato HTTP | **No**: FastAPI inyecta `Request` por anotación, sin tocar query/path/body. Lo cubren los tests de esas rutas, que ya existen |
| **R2** | Que `-NAME` traiga el *display name* en vez del UPN | Detectable con **M1** en un minuto. No es un fallo (identifica igual) y, si molesta, se arregla cambiando el orden de preferencia dentro de una función pura |
| **R3** | Que el sidecar de Container Apps no inyecte las cabeceras | Con la enmienda, se sella `sin-identidad` y sale un **WARNING por petición** (R5b): el incidente se ve en Log Analytics en vez de disfrazarse de sesión local. Visible también en `/whoami` (M1). **No rompe nada**: la operación se completa igual (R7) |
| **R6** | Que `CONTAINER_APP_*` no exista en este entorno y la señal A no valga | **Es el riesgo nuevo que introduce la enmienda**, y es el único que ensucia datos (§4.1). Mitigado por tres vías: **M1 bis** lo comprueba *antes* de implementar, **R9** lo loguea al arranque y la **señal B** lo corrige en cuanto entra el primer usuario autenticado. Si M1 bis sale negativo ⇒ **parar y consultar** la alternativa `ENTORNO=produccion` |
| **R4** | Rojos colaterales en la suite de sv4 | **T1** los inventaria antes de tocar nada. §6 |
| **R5** | Que aparezca la tentación de meter roles «ya que estamos» | `requirements.md` §0 y §2. Un `403` nuevo en el diff es motivo de rechazo |

---

## 12. Frontera con F-018

Esta feature deja preparadas dos cosas para F-018 y **ninguna más**:

1. Un punto único donde preguntar «quién es el que está pidiendo esto»
   (`_actor`), que ya devuelve un valor siempre no vacío.
2. Un criterio limpio para el corte histórico (`autor IS NULL` ⇔ antes de
   F-017).

Lo que F-018 tendrá que decidir por su cuenta y **no** se prejuzga aquí: qué
acciones se registran, qué tabla, si guarda `oid` además del UPN, si hay
pantalla, cuánto se conserva y si sv3/sv5 escriben en ese log.

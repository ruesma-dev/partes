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
| `undo_log` | `actor` | `String(120)` | sv4 (R14, R15) |

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

## 4. El fallback de desarrollo local

En local **no hay Easy Auth**: no hay sidecar, no hay cabeceras. Y esto no es
teórico — el humano arranca sv4 en local **contra el PostgreSQL real**
(así se hicieron las verificaciones del 2026-08-20). Es decir: **una sesión
local puede escribir filas en la base de producción**.

De ahí el diseño:

```
X-MS-CLIENT-PRINCIPAL-NAME  →  "nombre.apellido@dominio"      (origen: cabecera-name)
X-MS-CLIENT-PRINCIPAL       →  "nombre.apellido@dominio"      (origen: cabecera-token)
(ninguna)                   →  "local:<DEFAULT_REVIEWER>"     (origen: local)
(ninguna, y sin variable)   →  "local:sin-identidad"          (origen: local)
```

**Decisión DA4 — el fallback es un valor MARCADO, no `NULL` y no un nombre
suelto.** Tres razones:

1. **No puede confundirse con un usuario real.** Un UPN de Entra **no admite
   el carácter `:`**. El prefijo `local:` es, por tanto, un espacio de nombres
   que ninguna identidad real puede ocupar. Y R6 cierra la puerta por el otro
   lado: un valor que llegue por cabecera empezando por `local:` se descarta.
2. **No puede confundirse con «no se sabe».** `NULL` ya tiene dueño: las filas
   anteriores al corte (R7, R22). Si el desarrollo local también escribiera
   `NULL`, se perdería la única propiedad limpia que esta feature regala.
3. **Sigue siendo útil.** `local:pgris` dice quién y desde dónde. Con
   `DEFAULT_REVIEWER` sin configurar —que es el estado real hoy—, dice
   `local:sin-identidad`: honesto y evidente.

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
| `services/partes-front/tests/test_f017_identidad.py` | tests | R1–R9, R20, R21 |
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
| 0 | `_actor` (477) | **Solo su interior** y su docstring, como prometió F-016. Firma **intacta**: `def _actor(request: Request) -> str \| None`. Pasa a llamar a `identidad.actor_desde_cabeceras(request.headers, fallback=settings.default_reviewer)` |
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
ACTOR_MAX_LEN = 120          # la columna mas estrecha: undo_log.actor

CLAIMS_PREFERIDOS: tuple[str, ...] = (
    "preferred_username", "upn", "email", "emails", "name",
)


def normalizar_actor(valor: str | None) -> str | None:
    """R4: recorta, quita caracteres de control, minusculas, 120."""


def actor_desde_token(token: str | None) -> str | None:
    """R2/R3: base64 -> JSON -> primer claim preferido. NUNCA lanza."""


def actor_desde_cabeceras(
    cabeceras: Mapping[str, str], *, fallback: str | None,
) -> tuple[str, str]:
    """R1/R2/R5/R6/R7: devuelve (actor, origen).

    `origen` es 'cabecera-name', 'cabecera-token' o 'local'.
    El actor devuelto NUNCA es vacio ni None.
    """
```

`actor_desde_cabeceras` recibe un `Mapping` (no un `Request`) a propósito: así
la función es pura, no importa FastAPI y se prueba sin levantar la app.
`request.headers` de Starlette ya es un mapping insensible a mayúsculas.

### `_actor` dentro de `app.py` (firma intacta)

```python
def _actor(request: Request) -> str | None:
    """Quien firma el cambio. PUNTO UNICO de identidad del portal (R10).

    F-016 dejo escrito que aqui solo cambiaria el INTERIOR: asi ha sido.
    """
    actor, _origen = actor_desde_cabeceras(
        request.headers, fallback=settings.default_reviewer)
    return actor
```

Se mantiene el tipo de retorno `str | None` aunque hoy nunca devuelva `None`
(R7): es el tipo que aceptan las siete columnas y los repositorios, y estrechar
la firma obligaría a tocar `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio`,
que compara el texto exacto `def _actor(request: Request)`.

### `GET /whoami` (R21)

```python
@app.get("/whoami")
def whoami(request: Request) -> dict[str, Any]:
    actor, origen = actor_desde_cabeceras(
        request.headers, fallback=settings.default_reviewer)
    return {
        "actor": actor,
        "origen": origen,
        "cabeceras_easy_auth": [           # NOMBRES, nunca valores
            c for c in (CABECERA_NOMBRE, CABECERA_TOKEN, CABECERA_ID)
            if c.lower() in request.headers
        ],
    }
```

**Por qué existe `/whoami` y por qué es tan aburrida.** Sin ella, la
verificación M1 obliga a aprobar un parte de verdad y a mirar la base — y si
sale mal, ya has escrito la fila. Con ella, el humano abre una URL y ve en un
segundo si la cabecera llega y cuál. Devuelve **la identidad de quien
pregunta y nada más**: ni el token, ni los claims, ni los valores de las
cabeceras, ni ningún dato de otro usuario. Si el humano la considera de más,
es la pieza más fácil de quitar de toda la feature (una ruta y un test).

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
| **DA4** | ¿Qué se escribe en local? | `local:<algo>`, marcado y no confundible: `:` no es válido en un UPN. §4 |
| **DA5** | ¿Se elimina `DEFAULT_REVIEWER`? | No: se queda con significado nuevo (etiqueta de sesión local). Renombrarla obligaría a tocar Azure para nada. §4 |
| **DA6** | ¿Se inyecta o se parchea el helper en el test de F-016? | Ninguna de las dos: **se fabrica la cabecera**. `_actor` es una clausura, no hay nada que parchear, y el camino a probar es cabecera→columna. §6 |
| **DA7** | ¿Y las filas que escribe **sv3** (ingesta automática)? | **No se tocan.** Ahí el autor no es una persona. Si en el futuro se quiere distinguir el pipeline de un humano, el sitio es F-018, no esta feature |
| **DA8** | ¿`/whoami` es alcance de más? | Se propone porque hace verificable M1 sin escribir en la base. Es la pieza más fácil de retirar si el humano dice que no |
| **R1** | Añadir `request: Request` a cinco firmas rompe algún contrato HTTP | **No**: FastAPI inyecta `Request` por anotación, sin tocar query/path/body. Lo cubren los tests de esas rutas, que ya existen |
| **R2** | Que `-NAME` traiga el *display name* en vez del UPN | Detectable con **M1** en un minuto. No es un fallo (identifica igual) y, si molesta, se arregla cambiando el orden de preferencia dentro de una función pura |
| **R3** | Que el sidecar de Container Apps no inyecte las cabeceras | Sería un `local:sin-identidad` en producción, visible al instante en `/whoami` (M1) y en la primera fila. **No rompe nada**: la operación se completa igual (R7) |
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

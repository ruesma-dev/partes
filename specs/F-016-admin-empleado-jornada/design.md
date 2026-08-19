<!-- specs/F-016-admin-empleado-jornada/design.md -->
# F-016 · Pantalla de administración de `empleado_jornada` (sv4) — Diseño técnico

> **Base de partida**: `specs/F-016-admin-empleado-jornada/requirements.md`,
> la decisión **D5** del estudio F-012 y el requisito **R27 de F-015**, que
> reservó para esta feature las validaciones de negocio y la UI.
>
> **Puerta de entrada**: esta rama **no se empieza a implementar** hasta que
> `feature/F-015-jornada-semanal-candef` esté mergeada en `dev`. Sin ella no
> existen `EmpleadoJornadaOrm`, `list_jornadas_empleado()` ni
> `JornadaEmpleadoProvider`, que son las tres cosas sobre las que F-016 se
> apoya. Ver §11.1.

---

## 1. Servicios que toca y por qué (LÍMITE DE SERVICIO)

| Servicio | ¿Se toca? | Por qué |
|---|---|---|
| **sv4 `partes-front`** | **SÍ, y solo él** | Es el único servicio con humano delante: portal FastAPI + Jinja2 + JS vanilla con Easy Auth. Ya tiene la sesión a la base `partes`, ya declara `EmpleadoJornadaOrm` (F-015) y ya lee la tabla. Una pantalla de administración de una tabla de esa base es exactamente su trabajo. |
| sv3 `partes-persistencia` | **NO** | Es un worker de cola sin interfaz humana. Lee `empleado_jornada` (F-015) y seguirá leyéndola igual: **no necesita enterarse de que ahora hay una UI**. Si en algún momento del desarrollo pareciera necesario tocar sv3, es una señal de alarma — ver §12, decisión DA7. |
| sv1, sv2, sv5 | **NO** | No saben qué es una jornada. sv5 recibe líneas ya desglosadas. |
| `sigrid-api` | **NO** | Ni una consulta nueva. El único roce con Sigrid es de solo lectura y **opcional**: el catálogo de empleados que sv4 ya tiene cacheado, para avisar de un DNI desconocido (R19). |
| `infra/` | **NO** | La única variable nueva (`JORNADAS_ADMIN_ENABLED`) tiene default en código y **no** se declara en el manifiesto: encenderla/apagarla es `az containerapp update`, no un redespliegue. Ver §7 y §13, duda 1. |
| raíz del monorepo (`tests/`) | **NO** | F-016 no crea ninguna propiedad del monorepo que vigilar: no duplica nada entre servicios. El guardián de F-010 sigue como está y debe seguir en verde (R1). |

### 1.1 Duplicación: ninguna

F-016 **no añade una sola línea a la lista cerrada de duplicación tolerada de
`CLAUDE.md`**. Todo el código nuevo vive una sola vez, en sv4. En particular:

- La **validación** (R8–R12, R18) es de la pantalla, no del cómputo: sv3 no
  la necesita, porque su resolutor ya se defiende ignorando con WARNING una
  fila mal formada (F-015 R17). Duplicarla en sv3 sería exactamente lo que
  `CLAUDE.md` prohíbe.
- El **schema** ya está duplicado por F-015 y F-016 **no lo toca** (R1).

---

## 2. Modelo mental de la pantalla

Una sola página, `/admin/jornadas`, con dos zonas:

1. **Formulario** (panel superior) — alta o edición de UNA fila. Es el mismo
   formulario en los dos modos: `GET /admin/jornadas?editar=<id>` lo devuelve
   **relleno desde el servidor** (patrón PRG, cero JS de precarga) y con el
   botón «Guardar cambios» en vez de «Crear». Campos:
   - DNI (texto; deshabilitado en modo edición, R4).
   - `Jornada semanal (h)` — número, coma o punto decimal.
   - `Usar patrón por días` (checkbox) → siete números L, M, X, J, V, S, D.
   - `Desde` (`<input type="date">`, por defecto hoy).
   - `Sin fecha de fin` (checkbox, marcado por defecto) → si se desmarca,
     `Último día incluido` (`<input type="date">`).
   - `Nota` (texto, ≤ 255).
2. **Tabla** de todas las filas (R2), con la fila de filtros client-side que
   el portal ya usa (`class="table docs-table filterable"` +
   `<tr class="filter-row">`, como `trabajadores_list.html`) y, por fila, los
   botones `Editar`, `Cerrar…`, `Desactivar` / `Reactivar`.

**La palabra «exclusivo» no aparece nunca en la pantalla.** El humano escribe
y lee «último día incluido»; la conversión `+1 día` la hace el servidor (R7).
Debajo del campo se pinta la ayuda: «El día que escribas queda **incluido**.
Para una vigencia que acaba el 31/07, escribe 31/07.»

### 2.1 El ciclo de vida de una excepción, tal como lo ve el humano

```
   Crear ─────────────► [activa, sin fin]
                             │
                 Cerrar…     │  (indica el último día incluido)
                             ▼
                        [activa, con fin]  ──► crear la siguiente vigencia
                             │                 (contigua: no solapa, R12)
              Desactivar     │
                             ▼
                        [inactiva]  ◄──► Reactivar (revalida solapes, R6)
```

---

## 3. Ficheros a crear

| Fichero | Contenido | Capa |
|---|---|---|
| `services/partes-front/application/services/jornada_admin.py` | Reglas de negocio **puras** de la pantalla: `EntradaJornada`, `JornadaInvalida`, `normalizar_entrada`, `validar_entrada`, `buscar_solape`, `a_hasta_exclusivo`, `a_ultimo_dia_incluido`. Sin BBDD, sin FastAPI, sin logging. Vecino natural de `congelacion.py`, que hace lo mismo para F-004. | **application** |
| `services/partes-front/templates/admin_jornadas.html` | Plantilla de la página: `{% extends "base.html" %}`, formulario + tabla + aviso de caché. | interface_adapters (vista) |
| `services/partes-front/tests/test_f016_validacion_jornada_admin.py` | R7–R12, R18 sobre funciones puras (sin app, sin BBDD). | tests sv4 |
| `services/partes-front/tests/test_f016_endpoints_admin_jornadas.py` | R3–R6, R12 (409), R13, R16, R19 con TestClient + SQLite en memoria. | tests sv4 |
| `services/partes-front/tests/test_f016_vista_admin_jornadas.py` | R1, R2, R14, R15, R17 (HTML renderizado y puerta de acceso). | tests sv4 |

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | §5.3: `_actor`, `_exigir_admin_jornadas`, la página `GET /admin/jornadas` y los cinco endpoints JSON; un `templates.env.globals` para el enlace de la barra. |
| `services/partes-front/infrastructure/database/parte_repository.py` | §5.2: cinco métodos nuevos en `ParteReviewRepository` (`list_jornadas_admin`, `crear_jornada`, `actualizar_jornada`, `cerrar_jornada`, `set_jornada_activa`). **`list_jornadas_empleado()` de F-015 no se toca.** |
| `services/partes-front/application/services/jornada_provider.py` | Añadir `invalidar() -> None` a `JornadaEmpleadoProvider` (vacía la caché TTL). Es lo único que F-016 cambia de lo que dejó F-015, y no altera su comportamiento (R14). |
| `services/partes-front/config/settings.py` | `jornadas_admin_enabled: bool = Field(True, alias="JORNADAS_ADMIN_ENABLED")`. **Única variable nueva.** |
| `services/partes-front/templates/base.html` | Un enlace `Jornadas` en `<nav class="topnav">`, envuelto en `{% if jornadas_admin_enabled %}` (R15). |
| `services/partes-front/static/app.js` | Un IIFE nuevo al final, con el patrón de la casa (`MotivoHttp.lanzarSiFalla`, delegación por `data-*`, `window.location.reload()` al terminar). Sin frameworks, sin build. |
| `services/partes-front/static/styles.css` | **Solo si hace falta.** El objetivo es no tocarlo: `panel`, `table`, `field`, `field-row`, `btn`, `badge`, `alert`, `muted`, `cell-sub`, `cell-actions` ya existen. |
| `services/partes-front/tests/dobles.py` | `sembrar_jornadas(fabrica, filas) -> list[int]`, al lado de `sembrar_registros`. |
| `services/partes-front/.env.example` | `JORNADAS_ADMIN_ENABLED=true` con su comentario. |
| `docs/referencia/partes-proyecto.md` | La pantalla nueva y el criterio «último día incluido» en la sección de `empleado_jornada` que abrió F-015. |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | Las rutas nuevas que expone sv4 y la variable nueva. **Commit local, sin push** (ese repositorio no tiene remoto). |

## 5. Clases y funciones

### 5.1 `application/services/jornada_admin.py` — capa **application**

Todo son funciones puras sobre tipos del estándar: se prueban sin app, sin
BBDD y sin reloj. La capa web solo traduce HTTP ⇄ estas firmas.

```python
class JornadaInvalida(ValueError):
    """Motivo en español, listo para el cuerpo JSON. `campo` sitúa el error."""
    def __init__(self, motivo: str, *, campo: str | None = None) -> None: ...

@dataclass(frozen=True)
class EntradaJornada:
    """Una fila ya normalizada y validada, lista para persistir.

    `hasta` YA ES EXCLUSIVO: la conversión ocurre en `normalizar_entrada`.
    """
    dni_norm: str
    jornada_semanal: float | None
    patron: tuple[float, ...] | None      # 7 valores L…D, o None
    desde: str                            # ISO 'YYYY-MM-DD', inclusivo
    hasta: str | None                     # ISO, EXCLUSIVO; None = abierta
    nota: str | None

def a_hasta_exclusivo(ultimo_dia_incluido: str | None) -> str | None: ...
def a_ultimo_dia_incluido(hasta: str | None) -> str | None: ...
def normalizar_entrada(datos: Mapping[str, Any], *,
                       dni_fijo: str | None = None) -> EntradaJornada: ...
def validar_entrada(entrada: EntradaJornada) -> None: ...
def buscar_solape(entrada: EntradaJornada,
                  existentes: Sequence[Mapping[str, Any]],
                  *, excluir_id: int | None = None) -> Mapping[str, Any] | None: ...
```

Detalles que el implementer no debe reinventar:

- **`normalizar_entrada`** hace, en este orden: normalizar el DNI (§5.5),
  convertir números con coma o punto (`"6,5"` → `6.5`), tratar `""` y `None`
  como ausencia, exigir los siete días o ninguno (R9), convertir el último
  día incluido a `hasta` exclusivo (R7) y recortar la nota a 255. Lanza
  `JornadaInvalida` con el `campo` culpable. `dni_fijo` es lo que usa la
  edición para **ignorar** el DNI que venga en el cuerpo (R4).
- **`validar_entrada`** aplica R8 (`S` o patrón), R10 (`0 < S ≤ 168`), R9
  (cada hora en `[0, 24]`) y R11 (`desde` ISO válida y, si hay `hasta`,
  `hasta > desde`).
- **`buscar_solape`** compara con `datetime.date.fromisoformat` (no con
  cadenas: aunque el ISO ordena lexicográficamente, comparar fechas deja el
  error de formato donde debe estar). Regla: dos intervalos `[d1, h1)` y
  `[d2, h2)` con `None` = infinito solapan **si y solo si**
  `d1 < h2 y d2 < h1`. Devuelve la **primera** fila en conflicto (la de
  `desde` menor) o `None`. Solo mira filas con `is_active` verdadero.
- La conversión de fecha usa `date + timedelta(days=1)`, nunca aritmética de
  cadenas: así el 31/12 y el 28/02 bisiesto salen bien solos (R7).

### 5.2 `ParteReviewRepository` — capa **infrastructure**

Se añaden al repositorio único de sv4, que es el patrón real del servicio
(`upsert_empleado_alias` vive ahí mismo), con su idioma: constructor
`__init__(self, session_factory)` ya existente y `with
self._session_factory.create_session() as session: … session.commit()` por
método.

```python
def list_jornadas_admin(self) -> list[dict]: ...
def crear_jornada(self, *, entrada: EntradaJornadaDict, actor: str | None) -> int: ...
def actualizar_jornada(self, *, jornada_id: int,
                       entrada: EntradaJornadaDict, actor: str | None) -> bool: ...
def cerrar_jornada(self, *, jornada_id: int, hasta: str | None,
                   actor: str | None) -> bool: ...
def set_jornada_activa(self, *, jornada_id: int, activa: bool,
                       actor: str | None) -> bool: ...
```

- `list_jornadas_admin()` devuelve **todas** las filas (activas e inactivas)
  ordenadas `dni_norm ASC, desde DESC`, como `dict` planos con las 16
  columnas. Es la fuente tanto del listado (R2) como de la comprobación de
  solape (R12): una sola lectura por petición, porque la tabla tiene unidades
  de filas (misma razón que la decisión DA8 de F-015).
- `crear_jornada` sella `origen='manual'`, `is_active=True`, `created_at_utc`
  y `created_by`; **nunca** acepta `origen` del cliente (R3).
- Los cuatro métodos de modificación sellan `updated_at_utc` / `updated_by` y
  devuelven `False` si el id no existe (→ 404 de R16), sin lanzar.
- **Ningún método hace `DELETE`** (R6, semántica 8 de `ARCHITECTURE.md`).
- Los instantes se generan con `datetime.now(timezone.utc).isoformat()`,
  igual que `upsert_empleado_alias`.

### 5.3 `interface_adapters/web/app.py` — capa **interface_adapters**

Todo dentro de `build_app`, como el resto (clausuras sobre `repository`,
`settings`, `jornada_provider`), sin `Depends` ni router aparte.

| Método | Ruta | Devuelve |
|---|---|---|
| GET | `/admin/jornadas` | HTML (`admin_jornadas.html`); `?editar=<id>` precarga el formulario |
| POST | `/api/admin/jornadas` | `{"ok": true, "id": N, "aviso": …}` \| 422 \| 409 |
| PATCH | `/api/admin/jornadas/{jornada_id}` | `{"ok": true, "id": N}` \| 422 \| 409 \| 404 |
| POST | `/api/admin/jornadas/{jornada_id}/cerrar` | `{"ok": true}` \| 422 \| 404 |
| POST | `/api/admin/jornadas/{jornada_id}/desactivar` | `{"ok": true}` \| 404 |
| POST | `/api/admin/jornadas/{jornada_id}/reactivar` | `{"ok": true}` \| 409 \| 404 |

El prefijo `/api/admin/` no es nuevo: lo estrenó F-002 con
`/api/admin/poison`. Todos los endpoints JSON llevan
`include_in_schema=False`, como sus vecinos.

Helpers nuevos (uno de cada, y solo uno):

```python
def _actor(request: Request) -> str | None:
    """Quién firma el cambio (R13).

    Easy Auth (App Service) inyecta `X-MS-CLIENT-PRINCIPAL-NAME` en cada
    petición autenticada. En local esa cabecera no existe y se cae a
    `DEFAULT_REVIEWER`, que es lo que hoy usa el resto del portal.
    """

def _exigir_admin_jornadas() -> None:
    """Puerta ÚNICA de la pantalla (R15).

    Hoy: `JORNADAS_ADMIN_ENABLED`. Cuando exista F-008, la comprobación de
    rol se escribe AQUÍ y en ningún otro sitio.
    """
```

Forma de las respuestas de error, copiada de lo que ya hace el portal
(`poison_reencolar` y el handler de `CongeladoError`):

```python
return JSONResponse({"ok": False, "error": exc.motivo, "campo": exc.campo},
                    status_code=422)
return JSONResponse({"ok": False, "error": "…", "conflicto": {...}},
                    status_code=409)
```

`JornadaInvalida` se traduce a 422 en cada endpoint con un `try/except`
local, **no** con un `exception_handler` global: es una excepción de la
pantalla, y un handler global la convertiría en parte del contrato de todo el
portal (`CongeladoError` sí lo es, porque F-004 la lanza desde el repositorio
en media docena de rutas).

Y una línea junto a `asset_version`, para que el enlace de la barra no
obligue a tocar el contexto de las diez rutas existentes:

```python
templates.env.globals["jornadas_admin_enabled"] = bool(settings.jornadas_admin_enabled)
```

### 5.4 `static/app.js`

Un IIFE nuevo, autocontenido, que **solo actúa si existe** el contenedor de
la página (`document.getElementById("admin-jornadas")`), como hacen los demás
bloques del fichero. Responsabilidades:

1. Mostrar/ocultar los siete campos del patrón con el checkbox, y el campo de
   fecha de fin con «Sin fecha de fin».
2. Enviar el formulario por `fetch` (`POST` o `PATCH` según el `data-modo`
   que ponga la plantilla), con `MotivoHttp.lanzarSiFalla`.
3. En error, pintar el motivo en `#adminjor-status` (y marcar el campo si la
   respuesta trae `campo`); si trae `conflicto`, resaltar esa fila de la
   tabla por su `data-jornada-id`.
4. En éxito, `window.location.assign("/admin/jornadas")` (vuelve al modo alta
   y recarga el listado), con el `aviso` de R19 por query string si lo hay.
5. Delegación por `data-*` para `Editar` (navegar a `?editar=<id>`),
   `Cerrar…` (pide el último día incluido y hace POST), `Desactivar` y
   `Reactivar`, con `confirm()` en los dos últimos.

### 5.5 Normalización del DNI (R18)

Se usa **`application/services/text_match.normalize_dni`** (mayúsculas, solo
alfanumérico). Hoy conviven en sv4 tres funciones equivalentes
(`text_match.normalize_dni`, `calendario_provider.normalizar_dni` y
`_norm_dni`, local a `build_app`); F-016 **no las unifica** (§13, duda 4)
pero sí ata el cabo peligroso: el test de R18 comprueba que la que usa la
pantalla y la que usa la lectura de jornadas de sv4 dan el **mismo** resultado
para una batería de entradas. Si alguien las toca por separado, se pone rojo
antes de que una excepción deje de casar en producción.

---

## 6. SQL / schema

**Ninguno.** F-016 no crea, no altera y no borra nada del schema: trabaja
sobre `empleado_jornada` tal como la dejó F-015 (16 columnas, `origen` con
`server_default='manual'`, `is_active` con `server_default='true'`, índice en
`dni_norm`). Este proyecto no tiene ficheros `NN_nombre.sql`: el schema vive
en `orm_models.py` y lo materializan `create_all()` + `ddl_complementario()`
al arrancar (F-010). R1 lo convierte en un test.

Las columnas de las que se apropia la pantalla:

| Columna | Quién la escribe en F-016 |
|---|---|
| `dni_norm` | El alta (normalizado, §5.5). La edición **no** lo cambia. |
| `jornada_semanal`, `h_lun`…`h_dom`, `desde`, `hasta`, `nota` | Alta y edición. |
| `origen` | Siempre `manual`, puesto por el servidor. |
| `is_active` | `true` al crear; `desactivar` / `reactivar`. |
| `created_at_utc`, `created_by` | Solo el alta. |
| `updated_at_utc`, `updated_by` | Las cuatro operaciones de modificación. |
| `id` | La base. |

---

## 7. Configuración y el efecto en caliente

| Variable | Servicio | Default | Secreto |
|---|---|---|---|
| `JORNADAS_ADMIN_ENABLED` | sv4 | `true` | No |
| `JORNADA_CACHE_TTL_S` | sv3 y sv4 (**ya existe**, F-015) | `600` | No |

**El problema honesto**: un cambio hecho en la pantalla **no se ve al
instante en todas partes**, porque sv3 y sv4 cachean la tabla entera con TTL
(F-015). Lo que F-016 hace y lo que no:

- **Sí**: tras cada escritura con éxito, sv4 invalida el proveedor **de su
  propio proceso** (`jornada_provider.invalidar()`, R14). Con una sola
  réplica de sv4 —que es el caso hoy— el portal refleja el cambio en la
  siguiente pantalla que pinte.
- **No**: no se avisa a sv3, ni a otras réplicas de sv4. Hacerlo exigiría una
  llamada HTTP entre servicios o una cola de invalidación que
  `docs/ARCHITECTURE.md` no contempla («los servicios se acoplan únicamente
  por mensajes, HTTP y la BBDD»), para ahorrar como mucho diez minutos en una
  tabla que se toca dos veces al año. **Se descarta a propósito.**
- **Y por eso se dice**: la página lleva un aviso **permanente**, no un toast
  que se va, con los minutos calculados desde `settings.jornada_cache_ttl_s`:

  > **Los cambios tardan en aplicarse.** El portal los usa enseguida, pero la
  > conciliación (sv3) sigue con los datos anteriores hasta **10 minutos**.
  > Si acabas de cambiar una excepción, espera ese rato antes de comprobar el
  > reparto de extras de un parte.

  El número sale de la configuración, no cableado (R14): si mañana el TTL
  sube a media hora, el aviso lo dice solo.

Bajar el TTL para «arreglarlo» sería peor: multiplicaría por seis las
lecturas de una tabla que casi nunca cambia. Lo correcto, si algún día
molesta, es una invalidación explícita, y eso es otra feature.

---

## 8. Plan de pruebas

Todo sin red y sin PostgreSQL: `FabricaSesionSqlite` (SQLite en memoria con
el ORM real, `tests/dobles.py`), `Settings(_env_file=None)` y `TestClient`.
Es el montaje de F-002/F-003/F-004, sin inventar nada.

```python
def _settings(**env) -> Settings:      # patrón de la casa
    return Settings(_env_file=None)

fabrica = FabricaSesionSqlite()
repositorio = ParteReviewRepository(fabrica)
app = build_app(_settings(), repository=repositorio,
                jornada_provider=ProveedorFake())   # doble que cuenta invalidar()
cliente = TestClient(app)
```

- **Fase RED obligatoria** (rigor `estandar`) en **R7, R12, R14 y R15**, con
  la traza real pegada en `progress/impl_F-016.md`.
- **Dobles nuevos**: `ProveedorFake` (cuenta llamadas a `invalidar()`) y
  `sembrar_jornadas(fabrica, filas)` en `tests/dobles.py`.
- **Fechas de los casos**: julio–agosto de 2026, para ejercitar el cambio de
  mes en la conversión de R7; más 2028-02-28/29 para el bisiesto.
- **DNIs de los tests**: cadenas sintéticas que **no** son DNIs reales
  (`AAA1`, `BBB2`, y variantes con guiones y minúsculas para R18). En esta
  spec, en los tests y en el informe **no** aparece ningún DNI ni nombre de
  persona real.
- **Regresión**: ningún test existente de sv4 se modifica. Si uno se pone
  rojo, es que se rompió algo que ya funcionaba: **parar y avisar**, no
  adaptar el test.
- **Campaña de mutación**: `python -m harness.mutacion --feature F-016`, con
  los supervivientes analizados en `progress/mutacion_F-016.md`.

### 8.1 Tabla de casos del solape (R12), que es donde se falla

Con `A = [2026-07-01, 2026-08-01)` activa y del mismo DNI:

| Candidata | ¿Solapa? | Por qué |
|---|---|---|
| `[2026-08-01, ∞)` | **No** | Contigua: `hasta` de A = `desde` de la candidata. |
| `[2026-07-31, ∞)` | **Sí** | Comparten el 31/07. |
| `[2026-06-01, 2026-07-01)` | **No** | Termina justo cuando A empieza. |
| `[2026-06-01, 2026-07-02)` | **Sí** | Comparten el 01/07. |
| `[2026-07-10, 2026-07-12)` | **Sí** | Contenida en A. |
| `[2026-01-01, ∞)` | **Sí** | Contiene a A. |
| `[2026-07-10, …)` de **otro** DNI | **No** | El solape es por `dni_norm`. |
| Igual que A pero A **inactiva** | **No** | Solo cuentan las activas. |
| A misma, editando A | **No** | `excluir_id` la saca de la comparación. |

### 8.2 MANUAL (humano) — lo que no se puede probar sin BBDD ni navegador

1. **Portal en local, `/admin/jornadas`**: crear una excepción con `S = 48`
   para un trabajador de pruebas, ver la fila en el listado y comprobar en la
   base que `origen='manual'`, `is_active=true`, `created_by` con la
   identidad esperada y `hasta` **un día después** del que se escribió.
   Comando de comprobación:
   `SELECT id, dni_norm, jornada_semanal, desde, hasta, origen, is_active, created_by FROM empleado_jornada ORDER BY id DESC LIMIT 5;`
2. **Solape en pantalla**: intentar crear una segunda vigencia que pise la
   primera y comprobar que sale el aviso rojo nombrando la fila en conflicto
   y que **no** se ha creado nada (`SELECT count(*)` antes y después).
3. **Efecto en caliente**: tras crear la excepción, comprobar que el KPI de
   jornada de la vista del trabajador (F-015 R25) la refleja en el portal, y
   que sv3 tarda hasta `JORNADA_CACHE_TTL_S` en usarla.
4. **Estáticos**: `Ctrl+F5` tras el despliegue (convención de sv4) y
   `node --check services/partes-front/static/app.js` antes del commit.
5. **Easy Auth en Azure**: comprobar que `created_by` recoge el principal
   real (`X-MS-CLIENT-PRINCIPAL-NAME`) y no el `DEFAULT_REVIEWER`. En local
   esa cabecera no existe: es la única forma de verificarlo.

---

## 9. Ficheros que NO se tocan (los colindantes que tientan)

- **`services/partes-persistencia/` entero** — y muy especialmente su
  `jornada_resolver.py` y su repositorio de excepciones. F-016 edita filas;
  quién las interpreta ya está decidido en F-015.
- **Las dos copias de `infrastructure/database/orm_models.py`** y
  `tests/test_f010_orm_models_gemelos.py`: cero cambios de schema (R1).
- **`services/partes-front/application/services/jornada_resolver.py`**: la
  regla de la jornada del día no cambia ni un carácter.
- **`congelacion.py`** y las guardas de F-004: `empleado_jornada` no es una
  línea de parte; no hay nada que congelar.
- **`parte_registros`, `parte_documents`, `empleado_alias`, `undo_log`**: ni
  una columna, ni una fila. En particular, la pantalla **no** entra en el
  historial de deshacer (`undo_log`): ese widget es para ediciones de líneas
  de parte, y meter ahí un cambio de jornada obligaría a un `undo` capaz de
  revertir filas de otra tabla. La papelera lógica de R6 es la marcha atrás.
- **`sigrid_lookup_client.py`, `sesame_api_client.py`, `transfer_*`**: sin
  llamadas nuevas.
- **`infra/`**, **`harness/features.json`**, **`progress/current.md`**: los
  mueve el líder, no esta spec.

---

## 10. Orden de implementación (resumen; el detalle en `tasks.md`)

1. Validación pura (`jornada_admin.py`) con sus tests — es donde está el
   riesgo real y no necesita ni app ni BBDD.
2. Repositorio (los cinco métodos) sobre SQLite.
3. Cableado web: puerta de acceso, actor, endpoints.
4. Plantilla y JS.
5. Aviso de caché e invalidación del proveedor.
6. Documentación (`partes-proyecto.md`, `azure-apps/partes.md`) y cierre.

---

## 11. Riesgos

### 11.1 Dependencia dura de F-015 (el riesgo principal)

F-016 se diseña **contra la spec de F-015**, no contra el árbol actual: hoy
no existen ni la tabla, ni `EmpleadoJornadaOrm`, ni `list_jornadas_empleado`,
ni `JornadaEmpleadoProvider`. Consecuencias que el implementer debe asumir:

- **No se empieza hasta que F-015 esté en `dev`.** Empezar antes obliga a
  inventar la tabla, y acabarían existiendo dos definiciones.
- Si al implementar, la **firma real** de lo que dejó F-015 difiere de lo que
  aquí se supone (nombre del proveedor, del método de lectura, de la clase
  ORM), se **adapta el nombre** y se anota en el informe. Lo que **no** se
  toca sin consultar es la **semántica**: `hasta` exclusivo, `is_active` como
  papelera, `origen` con tres valores. Si lo que cambió es la semántica,
  `blocked` y se consulta.

### 11.2 Una pantalla que edita el cómputo de nóminas

Una fila mal puesta aquí cambia cuántas horas se consideran extra en sv3 y,
por esa vía, lo que se registra en Sigrid. Mitigaciones, por orden de
importancia:

1. Las validaciones R8–R12 impiden lo que el resolutor de F-015 ignoraría en
   silencio (con un WARNING que nadie lee).
2. **Nunca se borra** (R6): toda fila queda en la tabla con su auditoría.
3. **Nunca se ajusta la fila de otro automáticamente** (R12, DA3): si dos
   vigencias chocan, el humano decide cuál cierra.
4. F-004 sigue protegiendo lo ya aprobado o registrado: cambiar una excepción
   **no** recalcula lo que ya viajó a Sigrid (F-015 R31/R32).

### 11.3 Solape y concurrencia

La comprobación de solape se hace leyendo y luego escribiendo, sin bloqueo:
dos altas simultáneas del mismo DNI podrían colarse las dos. Se acepta a
propósito — un único administrador, dos veces al año, y la consecuencia es
una fila de más que se ve en el listado y se desactiva en un clic. Poner una
restricción de exclusión en PostgreSQL obligaría a DDL nuevo (que R1 prohíbe)
y a un tipo `daterange` que el ORM de este proyecto no usa. Queda anotado
como límite conocido, no como descuido.

### 11.4 El aviso de caché puede convertirse en ruido

Un aviso permanente que siempre está acaba siendo invisible. Se asume: es
preferible a que el humano concluya que la pantalla «no funciona» porque
sv3 tardó diez minutos. Si con el uso resulta molesto, la alternativa es
mostrarlo solo durante los `JORNADA_CACHE_TTL_S` siguientes a un cambio —lo
cual exige recordar el instante del último cambio, y eso es estado nuevo.

---

## 12. Decisiones tomadas por el spec-author

- **DA1 · El humano escribe «último día incluido», nunca `hasta`.** Era la
  trampa señalada por la duda 4 de F-015. La alternativa (enseñar el valor
  exclusivo y explicarlo en la ayuda) traslada al usuario un detalle de
  almacenamiento, y el error resultante —un día de más o de menos en una
  vigencia— es silencioso: no produce ningún fallo, solo un reparto de horas
  distinto. La conversión vive **solo** en la capa web (R7) para que la BBDD
  siga hablando el idioma de F-015.
- **DA2 · Cerrar es poner `hasta`; desactivar es la papelera.** Son dos
  acciones distintas y no se fusionan. «Cerrar» es historia legítima (la
  excepción dejó de aplicar el 31/07); «desactivar» es «esta fila no debería
  existir». Fundirlas obligaría a elegir por el usuario qué quiso decir.
- **DA3 · Un solape se rechaza, no se resuelve solo.** La tentación es
  cerrar automáticamente la vigencia anterior al crear la nueva. Se descarta:
  reescribe en silencio un dato que sv3 usa para calcular extras de meses
  pasados. El mensaje de error nombra la fila en conflicto y el humano decide.
- **DA4 · Reactivar existe, y revalida.** No estaba en el enunciado («crear,
  editar y cerrar»), pero sin él una desactivación por error solo se arregla
  por SQL — justo lo que esta feature viene a evitar. Cuesta un endpoint y
  reutiliza la validación de R12. **Si el humano prefiere recortar alcance,
  es lo primero que se cae** (§13, duda 5).
- **DA5 · La validación vive en `application/services/`, no en Pydantic.**
  Los payloads Pydantic del portal (`HoraPayload`, `RegistroEditPayload`…)
  validan **tipos**; aquí hay **reglas de negocio** (solape, «`S` o patrón»)
  que necesitan ver otras filas. Ponerlas en un validador de Pydantic las
  ataría a FastAPI y las haría intestables sin app. `congelacion.py` (F-004)
  es el precedente exacto: una regla de negocio, en `application/services/`,
  usada por el repositorio y por las vistas.
- **DA6 · Los métodos van al `ParteReviewRepository` existente, no a una
  clase nueva.** sv4 tiene **un** repositorio con todo (incluido
  `upsert_empleado_alias`, que es otra tabla auxiliar) y F-015 ya le cuelga
  `list_jornadas_empleado`. Crear `JornadaAdminRepository` al lado sería un
  patrón nuevo en un servicio que no lo usa.
- **DA7 · sv3 no se toca, y eso es una decisión, no un olvido.** Se comprobó
  el camino contrario: para que sv3 «se entere» de un cambio haría falta un
  endpoint de invalidación o una cola nueva, es decir, acoplamiento nuevo
  entre servicios. La alternativa barata —el TTL que ya existe— cuesta diez
  minutos de espera en una tabla que cambia dos veces al año. Se elige el TTL
  y **se avisa en pantalla** (R14, §7).
- **DA8 · Una sola lectura de la tabla por petición.** `list_jornadas_admin`
  sirve al listado y al control de solape. Consultar por DNI sería más
  «eficiente» sobre el papel y peor aquí: la tabla tiene unidades de filas
  (misma razón que la decisión DA8 de F-015) y la comprobación de solape
  necesita todas las del DNI de todos modos.
- **DA9 · La puerta de acceso es una función, no un decorador ni un
  middleware.** `_exigir_admin_jornadas()` se llama al principio de las seis
  rutas. Cuando llegue F-008, el cambio es **una** función; un middleware por
  prefijo de ruta habría que desmontarlo.
- **DA10 · 422 para lo que está mal escrito, 409 para lo que choca con el
  estado.** Es la separación que ya usa el portal (422 en
  `poison_reencolar`, 409 en `CongeladoError`) y permite al JS distinguir
  «corrige el campo» de «mira esa otra fila».

---

## 13. Dudas para el humano (ninguna bloquea la implementación)

1. **¿Quién puede entrar, mientras F-008 no exista?** La propuesta es
   repetir el precedente que el propio humano fijó el 2026-08-13 con el
   reencolado de mensajes poison: **abierta a cualquier usuario autenticado
   por Easy Auth**, con `JORNADAS_ADMIN_ENABLED` (default `true`) como
   interruptor para apagarla entera desde Azure sin tocar código, y un único
   punto (`_exigir_admin_jornadas`) donde F-008 enchufará el rol. Las dos
   alternativas, por si prefieres otra: (a) default `false` y encenderla solo
   cuando la necesites; (b) esperar a F-008 y dejar F-016 en `blocked`.
   **Recomendación: la propuesta.** La pantalla no borra nada y todo cambio
   queda firmado.
2. **¿Se introduce la lectura de la identidad de Easy Auth?** Hoy sv4 **no
   la lee**: `approved_by` y `deleted_by` se rellenan con la variable
   `DEFAULT_REVIEWER`, la misma para todos. F-016 necesita «quién», así que
   propone el helper `_actor(request)` (cabecera
   `X-MS-CLIENT-PRINCIPAL-NAME`, con `DEFAULT_REVIEWER` de reserva) **solo
   para sus columnas**. Extenderlo a `approved_by` / `deleted_by` cambiaría
   el significado de datos ya guardados y es material para F-008. ¿De
   acuerdo con dejarlo acotado?
3. **¿Hace falta elegir el trabajador de una lista?** La pantalla pide el DNI
   a mano y solo **avisa** si no consta en el catálogo de Sigrid (R19). Un
   selector de trabajadores como el de «+ Nuevo» es bastante más JS y ata la
   pantalla a que Sigrid esté cableado. Si prefieres el selector, se dice
   ahora: después es rehacer la mitad del formulario.
4. **Tres normalizadores de DNI equivalentes en sv4**
   (`text_match.normalize_dni`, `calendario_provider.normalizar_dni` y el
   `_norm_dni` local de `build_app`). F-016 **no los unifica** —sería tocar
   código de tres features ajenas— pero deja un test que salta si divergen
   (R18). ¿Se abre una feature de limpieza aparte?
5. **¿Se queda «Reactivar»?** (DA4). No estaba en el enunciado. Si sobra, se
   quita el endpoint y la mitad de R6, y una desactivación por error vuelve a
   arreglarse por SQL.
6. **`origen`**: la pantalla escribe siempre `manual` (R3) y, tal como está
   especificada, deja **editar cualquier fila** con independencia de su
   `origen` — hoy no existe ninguna que no sea `manual`. Cuando lleguen las
   importadas de `sigrid` o `sesame`, ¿deberán quedar en solo lectura (una
   importación posterior pisaría la corrección a mano) o se podrán corregir
   igualmente desde aquí? No urge, pero condiciona esa feature futura.

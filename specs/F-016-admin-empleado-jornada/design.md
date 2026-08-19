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
>
> **Segunda pasada (2026-08-19)**: el humano ha contestado cuatro de las seis
> dudas de §13. Han quedado **resueltas** la 1 (acceso), la 2 (identidad, con
> el alcance ampliado y sacado a **F-017**, §14), la 3 (**selector** de
> trabajador, que cambia el formulario — §5.6, DA11, R20) y la 5 («Reactivar»
> se queda). Siguen **abiertas** la 4 y la 6. El detalle del cambio está en
> `progress/spec_F-016.md`.

---

## 1. Servicios que toca y por qué (LÍMITE DE SERVICIO)

| Servicio | ¿Se toca? | Por qué |
|---|---|---|
| **sv4 `partes-front`** | **SÍ, y solo él** | Es el único servicio con humano delante: portal FastAPI + Jinja2 + JS vanilla con Easy Auth. Ya tiene la sesión a la base `partes`, ya declara `EmpleadoJornadaOrm` (F-015) y ya lee la tabla. Una pantalla de administración de una tabla de esa base es exactamente su trabajo. |
| sv3 `partes-persistencia` | **NO** | Es un worker de cola sin interfaz humana. Lee `empleado_jornada` (F-015) y seguirá leyéndola igual: **no necesita enterarse de que ahora hay una UI**. Si en algún momento del desarrollo pareciera necesario tocar sv3, es una señal de alarma — ver §12, decisión DA7. |
| sv1, sv2, sv5 | **NO** | No saben qué es una jornada. sv5 recibe líneas ya desglosadas. |
| `sigrid-api` | **NO** | Ni una consulta nueva **y ni un endpoint nuevo**. Los dos roces con Sigrid son de solo lectura, opcionales y **sobre lo que sv4 ya tiene**: el catálogo de empleados cacheado (`EmpleadoCatalog`) para avisar de un DNI desconocido (R19), y el endpoint **ya existente** `GET /api/sigrid/empleados` (F-003) que alimenta el selector de trabajador (R20, §5.6). |
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
   - **Trabajador** — **selector con búsqueda incremental por DNI y nombre**
     (R20, §5.6), el mismo componente de «+ Nuevo». Al elegir, el DNI queda
     en un campo oculto. Debajo, un checkbox **«El trabajador no está en la
     lista (escribir el DNI a mano)»** que descubre un campo de texto: es el
     camino de excepción y el único disponible si Sigrid no está cableado.
     En modo edición el bloque entero se muestra **deshabilitado** con el
     DNI de la fila (R4: la edición no cambia de trabajador).
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
| `services/partes-front/templates/admin_jornadas.html` | Plantilla de la página: `{% extends "base.html" %}`, formulario (con el **selector de trabajador** de §5.6, copiando el marcado `combo-simple` de `nuevo_parte.html`) + tabla + aviso de caché. | interface_adapters (vista) |
| `services/partes-front/tests/test_f016_validacion_jornada_admin.py` | R7–R12, R18 sobre funciones puras (sin app, sin BBDD). | tests sv4 |
| `services/partes-front/tests/test_f016_endpoints_admin_jornadas.py` | R3–R6, R12 (409), R13, R16, R19 con TestClient + SQLite en memoria. | tests sv4 |
| `services/partes-front/tests/test_f016_vista_admin_jornadas.py` | R1, R2, R14, R15, R17, R20 (HTML renderizado, puerta de acceso y marcado del selector). | tests sv4 |

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | §5.3: `_actor`, `_exigir_admin_jornadas`, la página `GET /admin/jornadas` (que pasa `sigrid_enabled` al contexto, §5.6) y los cinco endpoints JSON; un `templates.env.globals` para el enlace de la barra. **Ninguna ruta `/api/sigrid/*` nueva ni modificada.** |
| `services/partes-front/infrastructure/database/parte_repository.py` | §5.2: cinco métodos nuevos en `ParteReviewRepository` (`list_jornadas_admin`, `crear_jornada`, `actualizar_jornada`, `cerrar_jornada`, `set_jornada_activa`). **`list_jornadas_empleado()` de F-015 no se toca.** |
| `services/partes-front/application/services/jornada_provider.py` | Añadir `invalidar() -> None` a `JornadaEmpleadoProvider` (vacía la caché TTL). Es lo único que F-016 cambia de lo que dejó F-015, y no altera su comportamiento (R14). |
| `services/partes-front/config/settings.py` | `jornadas_admin_enabled: bool = Field(True, alias="JORNADAS_ADMIN_ENABLED")`. **Única variable nueva.** |
| `services/partes-front/templates/base.html` | Un enlace `Jornadas` en `<nav class="topnav">`, envuelto en `{% if jornadas_admin_enabled %}` (R15). |
| `services/partes-front/static/app.js` | Un bloque nuevo **dentro del IIFE grande** (el que hoy va de la línea ~40 a la ~2228 y es el que define `_comboSimple`), justo antes de su cierre, para poder **reutilizar el combo sin tocarlo** (§5.6). Patrón de la casa: `MotivoHttp.lanzarSiFalla`, delegación por `data-*`, recarga al terminar. Sin frameworks, sin build. |
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
    """Quién firma el cambio (R13). PUNTO ÚNICO de identidad en F-016.

    HOY devuelve `settings.default_reviewer`, exactamente lo que hace el
    resto del portal (once sitios de este mismo fichero, ver §14). No lee
    ninguna cabecera: leer y decodificar la de Easy Auth es trabajo de
    **F-017**, y cuando F-017 llegue solo cambia el INTERIOR de esta
    función — F-016 no se toca.

    Si F-017 ya está mergeada al implementar F-016, este helper NO se
    duplica: se llama al que haya dejado F-017.
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

Un bloque nuevo, autocontenido, que **solo actúa si existe** el contenedor de
la página (`document.getElementById("admin-jornadas")`), como hacen los demás
bloques del fichero.

**Dónde va, y por qué no es un IIFE al final.** `_comboSimple` —el motor del
selector de R20— es una función **privada** del IIFE grande de `app.js`
(declarada sobre la línea 1069, dentro del IIFE que abre en la ~40 y cierra
en la ~2228). Un IIFE nuevo al final del fichero **no la vería**. El bloque
de F-016 se escribe por tanto **dentro de ese mismo IIFE, justo antes de su
`})();`**, que es coste cero: no se modifica ni una línea existente. Ver
DA11.

Responsabilidades:

1. Mostrar/ocultar los siete campos del patrón con el checkbox, el campo de
   fecha de fin con «Sin fecha de fin», y el DNI manual con el checkbox
   «El trabajador no está en la lista» (§5.6).
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
6. Cablear el selector de trabajador con **una sola llamada** a
   `_comboSimple` (§5.6).

### 5.5 Normalización del DNI (R18)

Se usa **`application/services/text_match.normalize_dni`** (mayúsculas, solo
alfanumérico). Hoy conviven en sv4 tres funciones equivalentes
(`text_match.normalize_dni`, `calendario_provider.normalizar_dni` y
`_norm_dni`, local a `build_app`); F-016 **no las unifica** (§13, duda 4)
pero sí ata el cabo peligroso: el test de R18 comprueba que la que usa la
pantalla y la que usa la lectura de jornadas de sv4 dan el **mismo** resultado
para una batería de entradas. Si alguien las toca por separado, se pone rojo
antes de que una excepción deje de casar en producción.

### 5.6 Selector de trabajador (R20) — lo que YA existe y lo mínimo que falta

Decisión del humano del **2026-08-19** (duda 3): el DNI **no se teclea**, se
elige de un selector con DNI y nombre y búsqueda incremental, como los que ya
usa el portal. Antes de diseñar nada se ha mirado el que existe.

**Lo que ya existe y sirve tal cual (se reutiliza sin tocarlo):**

| Pieza | Dónde | Qué da |
|---|---|---|
| `GET /api/sigrid/empleados` | `interface_adapters/web/app.py:1183` | `{"ok": bool, "items": [{"ide", "codigo", "nombre", "dni", "reside", "categoria", "candef", "jornada_sugerida"}]}`. Trae **DNI y nombre**, que es justo lo que R20 pide. |
| `EmpleadoCatalog` | `application/services/empleado_catalog.py` | Cachea el maestro `emp` de Sigrid con TTL propio y `enabled = client is not None`. Sin cliente, el endpoint responde `{"ok": false, "items": []}` con **HTTP 200** (no 500). |
| `_comboSimple(rootId, inputId, panelId, url, render, onPick)` | `static/app.js:1069` | El combo entero: carga perezosa con caché en memoria, panel de 15 resultados, filtro **por la etiqueta pintada, por `dni` y por `codigo`**, cierre al hacer clic fuera, `mousedown` para no perder el foco. |
| Marcado `combo-simple` / `combo-panel` / `combo-option` | `templates/nuevo_parte.html:28-36` y `static/styles.css` | El HTML y el CSS del combo. **No hace falta CSS nuevo.** |

**Cómo se cabla en F-016** (una llamada, dentro del bloque de §5.4):

```js
_comboSimple("jor-emp-combo", "jor-emp-input", "jor-emp-panel",
  "/api/sigrid/empleados",
  function (e) { return (e.dni || "—") + " · " + (e.nombre || ""); },
  function (e) { document.getElementById("jor-dni").value = e.dni || ""; });
```

- El `render` pone **el DNI delante** (R20 pide «DNI y nombre»); «+ Nuevo»
  lo pinta al revés porque allí lo que identifica es el nombre. El filtro del
  componente ya mira `it.dni` aparte de la etiqueta, así que **la búsqueda
  incremental por DNI funciona sin añadir nada**.
- El `onPick` solo rellena el campo oculto `#jor-dni`. Ese campo es el único
  que lee el envío del formulario, venga del combo o del alta manual: el
  servidor recibe siempre lo mismo y R18 lo normaliza igual.

**Lo mínimo que hay que añadir, y por qué el componente no basta solo:**

1. **Camino manual.** `_comboSimple` no ofrece salida cuando el catálogo está
   vacío o apagado: el panel simplemente no se abre. Como R17 exige que la
   pantalla funcione **sin Sigrid cableado**, la plantilla añade el checkbox
   «El trabajador no está en la lista (escribir el DNI a mano)» que
   deshabilita el combo y descubre un `<input type="text">` que escribe en
   `#jor-dni`. Con `sigrid_enabled` falso, ese checkbox llega **marcado y el
   combo deshabilitado** desde el servidor, con el mismo `placeholder`
   «Sigrid no configurado» que usa `nuevo_parte.html`.
2. **Contexto en la plantilla.** `GET /admin/jornadas` pasa
   `"sigrid_enabled": settings.sigrid_lookup_enabled`, igual que hacen ya las
   otras seis vistas del portal (líneas 477, 639, 756, 801, 1060, 1956).
   Nada más.
3. **Modo edición.** Con `?editar=<id>`, la plantilla pinta el DNI de la fila
   como texto y deja combo, checkbox y campo manual **deshabilitados**
   (R4: cambiar de trabajador es cerrar una fila y crear otra).

**Lo que NO se hace:** promover `_comboSimple` a global compartido (como
`MotivoHttp` o `PartidaSel`). Sería más «limpio», pero obliga a mover código
vivo del que cuelgan cuatro combos de features ya cerradas (F-002/F-003) a
cambio de nada: colocar el bloque de F-016 dentro del mismo IIFE lo resuelve
sin tocar una línea ajena. Ver DA11.

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
- **Lo que del selector SÍ se puede probar sin navegador** (R20): que el HTML
  trae el marcado del combo con sus ids, que apunta a
  `/api/sigrid/empleados`, que con `sigrid_lookup_enabled` falso llega el
  camino manual descubierto y el combo deshabilitado, que en modo edición
  todo el bloque va deshabilitado, y que **el diff no añade ninguna ruta
  `/api/sigrid/*`**. Lo que **no**: el comportamiento del combo al teclear —
  este repositorio no tiene arnés de JS. Eso queda en `node --check` (T7) y
  en la verificación MANUAL 6.
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
5. **Identidad**: comprobar que `created_by` lleva lo que corresponde al
   estado del portal. **Si F-017 aún no está**, lo esperado es
   `DEFAULT_REVIEWER` (y eso es correcto, no un fallo). **Si F-017 ya está**,
   en Azure debe verse el principal real de Easy Auth; en local esa cabecera
   no existe, así que solo se puede verificar desplegado.
6. **Selector de trabajador (R20)** en el navegador, que es lo único que no
   cubre ningún test: teclear tres letras del nombre y ver la lista; teclear
   tres cifras del DNI y ver la misma lista filtrada; elegir uno y comprobar
   que el alta guarda **ese** DNI normalizado; marcar «no está en la lista»,
   escribir un DNI que no exista en Sigrid y comprobar que la fila **se crea
   igual** y sale el aviso de R19. Repetirlo con Sigrid apagado en local
   (sin `SIGRID_API_BASE_URL`): el combo debe salir deshabilitado y el
   camino manual funcionar entero.

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
- **`GET /api/sigrid/empleados` (`app.py:1183`) y
  `application/services/empleado_catalog.py`**: el selector de R20 los
  **consume tal cual**. Ni un campo nuevo en la respuesta, ni un parámetro
  de búsqueda, ni un TTL distinto. Si el selector pareciera necesitar algo
  de ahí, **parar y consultar** (§5.6).
- **`_comboSimple` (`static/app.js:1069`) y el marcado/CSS del combo**: se
  reutilizan **sin modificarlos**. F-016 solo lo *llama*. Tampoco se toca
  `templates/nuevo_parte.html`.
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

### 11.4 El selector ata media pantalla a que Sigrid esté cableado

Añadido en la segunda pasada (R20). El combo solo tiene contenido si sv4
tiene cliente de Sigrid; sin él, `GET /api/sigrid/empleados` devuelve la
lista vacía y el humano se queda mirando un campo que no propone nada. Por
eso el camino manual **no es un extra**, es el respaldo: se muestra siempre y
llega ya activado cuando `sigrid_lookup_enabled` es falso (§5.6). El riesgo
real que queda es más sutil: el catálogo se cachea con TTL propio en
`EmpleadoCatalog`, así que un trabajador **dado de alta hoy en Sigrid** puede
tardar en aparecer en la lista. La salida es la misma —alta manual— y el
aviso de R19 avisa de que ese DNI no consta. No se toca el TTL ajeno.

### 11.5 El aviso de caché puede convertirse en ruido

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
  reutiliza la validación de R12. **CONFIRMADO por el humano el 2026-08-19**
  (§13, duda 5): se queda, y deja de ser candidato a recorte.
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

### Decisiones de la segunda pasada (2026-08-19, tras las respuestas del humano)

- **DA11 · El selector reutiliza `_comboSimple`, y por eso el JS de F-016 va
  DENTRO del IIFE grande.** `_comboSimple` es privado de ese IIFE; un bloque
  nuevo al final del fichero no lo alcanzaría. Las tres salidas eran:
  (a) duplicar el componente — prohibido por el espíritu de `CLAUDE.md` y
  garantía de que un día divergen; (b) promoverlo a global como `MotivoHttp`
  — toca código vivo de cuatro combos de features cerradas para no ganar
  nada hoy; (c) escribir el bloque dentro del mismo IIFE — **cero líneas
  ajenas modificadas**. Se elige (c). Si algún día un cuarto sitio lo
  necesita desde otro IIFE, entonces sí toca promoverlo, y será su feature.
- **DA12 · El DNI viaja siempre por el mismo campo, venga del combo o del
  alta manual.** El servidor no distingue el origen y R18 lo normaliza
  igual. Así R3/R4/R18 no crecen ni un caso por haber añadido el selector, y
  el aviso de R19 sigue siendo una sola regla en un solo sitio.
- **DA13 · La identidad se pide por un helper y no se implementa aquí.**
  F-016 llama a `_actor(request)`; su interior, hoy, es
  `settings.default_reviewer`. Meter la decodificación de Easy Auth dentro
  de F-016 mezclaría dos cambios de naturaleza distinta —una pantalla nueva
  y un cambio de significado de datos ya guardados en todo el portal— en una
  sola revisión. Sale a **F-017** (§14). Consecuencia práctica: F-016 **no
  queda bloqueada** por F-017, y cuando F-017 entre, F-016 mejora sola.

---

## 13. Dudas para el humano

Estado tras la sesión del **2026-08-19**: **cuatro RESUELTAS, dos ABIERTAS**.
Ninguna bloquea la implementación.

### RESUELTAS

- **1 · ¿Quién puede entrar, mientras F-008 no exista?** — **RESUELTA
  (2026-08-19)**: **cualquier usuario autenticado**, con interruptor. Se
  acepta la propuesta tal cual, repitiendo el precedente que el propio humano
  fijó el **2026-08-13** con el reencolado de mensajes poison. Queda por
  tanto: `JORNADAS_ADMIN_ENABLED` con default **`true`** para poder apagar la
  pantalla entera desde Azure sin tocar código, y la puerta **única**
  `_exigir_admin_jornadas()` (DA9, R15) para que **F-008 solo tenga que
  enchufar el rol ahí**. Descartadas las alternativas de default apagado y
  de dejar F-016 en `blocked` hasta F-008.

- **2 · ¿Se introduce la lectura de la identidad de Easy Auth?** —
  **RESUELTA (2026-08-19), y con el alcance AMPLIADO**. El hallazgo era
  correcto y el líder lo ha verificado: **no hay ni una referencia a
  `X-MS-CLIENT-PRINCIPAL` en el repositorio** y todo el portal firma con
  `DEFAULT_REVIEWER`. Decisión del humano: **sí se lee Easy Auth, y no solo
  para las columnas de F-016** — `approved_by` y `deleted_by` deben llevar
  también el usuario real. Decisión del líder sobre **cómo organizarlo**:
  esa ampliación **NO entra en F-016**; sale a una feature propia,
  **F-017 · «Identidad real de Easy Auth en sv4»**, porque cambia el
  significado de datos ya guardados (hoy todas las filas dicen lo mismo) y
  merece sus propios tests y su propia revisión.
  **Efecto en F-016**: F-017 es **prerrequisito recomendado, no
  bloqueante**. F-016 consume la identidad por un helper único
  (`_actor(request)`, §5.3) que **hoy cae a `DEFAULT_REVIEWER` exactamente
  como el resto del portal**; cuando F-017 exista, ese helper devuelve el
  principal real y F-016 no cambia. Lo que debería cubrir F-017 está en
  **§14** (enumerado como propuesta, no redactado como spec).

- **3 · ¿Selector de trabajador o DNI a mano?** — **RESUELTA (2026-08-19):
  selector**, y **cambia el diseño**. El humano **no** quiere teclear el DNI:
  quiere un selector con **DNI y nombre y autorrellenado** como los que ya
  usa el portal. Se ha mirado el que existe («+ Nuevo») y se reutiliza:
  endpoint `GET /api/sigrid/empleados` **sin cambios** y componente
  `_comboSimple` **sin cambios**. Lo mínimo que hay que añadir —camino manual
  de excepción, `sigrid_enabled` en el contexto de la plantilla y el bloque
  deshabilitado en modo edición— está detallado y justificado en **§5.6**;
  la ubicación del JS, en **DA11**. Requisito nuevo **R20**; **R19** se
  degrada a caso raro (el aviso «no consta en Sigrid» solo aparece por el
  alta manual).

- **5 · ¿Se queda «Reactivar»?** — **RESUELTA (2026-08-19): se queda.** Deja
  de estar marcado como «lo primero que se recorta» (DA4). R6 se implementa
  entero, con la revalidación de solape al reactivar.

### ABIERTAS (no las cierra el spec-author)

- **4 · Tres normalizadores de DNI equivalentes en sv4**
  (`application/services/text_match.normalize_dni`,
  `calendario_provider.normalizar_dni` y el `_norm_dni` local de `build_app`,
  `app.py:363`). F-016 **no los unifica** —sería tocar código de tres
  features ajenas— pero deja un test que salta si divergen (R18). ¿Se abre
  una feature de limpieza aparte? **Sigue abierta.**

- **6 · `origen` de las filas importadas.** La pantalla escribe siempre
  `manual` (R3) y, tal como está especificada, deja **editar cualquier fila**
  con independencia de su `origen` — hoy no existe ninguna que no sea
  `manual`. Cuando lleguen las importadas de `sigrid` o `sesame`, ¿deberán
  quedar en solo lectura (una importación posterior pisaría la corrección a
  mano) o se podrán corregir igualmente desde aquí? No urge, pero condiciona
  esa feature futura. **Sigue abierta.**

---

## 14. Propuesta de F-017 · «Identidad real de Easy Auth en sv4»

**Esto NO es la spec de F-017**: es el material para que el líder pueda darla
de alta con criterio (decisión del 2026-08-19, duda 2). F-016 no depende de
que exista.

**Por qué es feature propia y no un trozo de F-016.** No añade una pantalla:
cambia **el significado de datos ya guardados**. Hoy toda fila aprobada o
borrada del portal dice lo mismo (`DEFAULT_REVIEWER`), así que la columna no
distingue a nadie; después empezará a distinguir. Ese corte hay que decidirlo
y documentarlo, no dejarlo caer de rebote dentro de otra feature.

**Qué debería cubrir, punto por punto:**

1. **Leer y decodificar la cabecera de Easy Auth.** App Service inyecta
   `X-MS-CLIENT-PRINCIPAL-NAME` (el UPN, en claro) y `X-MS-CLIENT-PRINCIPAL`
   (el token de claims en base64). Decidir cuál manda —lo barato y estable es
   el `-NAME`, y caer al base64 solo si falta— y **dónde** se corta la
   longitud, porque `created_by` / `approved_by` son columnas de texto con
   límite.
2. **El fallback cuando no llega**, que es el caso de **todo el desarrollo
   local**: sin cabecera, `settings.default_reviewer`; sin ninguno de los
   dos, `NULL` **sin fallar la operación**. Ese orden es exactamente el que
   F-016 ya asume en R13.
3. **Un solo helper, y los once sitios que hoy firman con
   `settings.default_reviewer`** — todos en
   `services/partes-front/interface_adapters/web/app.py`, verificados en el
   árbol el 2026-08-19:

   | Línea | Ruta / función | Qué firma |
   |---|---|---|
   | 1500 | `_payload_registro` | campo `usuario` del payload de edición |
   | 1594 | `_trazar` (aprobación) | `usuario=` de la traza |
   | 1629 | `POST /api/aprobar/ejecutar` | usuario del log (`or "(sin usuario)"`) |
   | 1684, 1687 | `POST /api/aprobar/encolar` | `usuario=` (dos llamadas) |
   | 1841 | `POST /documents/{id}/approve` | **`approved_by`** |
   | 1867 | `POST /documents/{id}/delete` | **`deleted_by`** |
   | 1881 | `POST /api/registro/{id}/delete` | `by=` |
   | 1900 | `POST /api/obra/{key}/delete` | `by=` |
   | 1910 | `POST /api/trabajador/{key}/delete` | `by=` |
   | 2121 | `POST /api/partes/nuevo` | `by=` (alta manual de parte) |

   Los cuatro `by=` van al **`undo_log`**, así que el cambio también se ve en
   el widget de deshacer: conviene mirarlo antes de decidir el formato del
   texto.
4. **Qué se hace con las filas históricas.** La propuesta es la barata y
   honesta: **no se reescriben**. Las filas anteriores conservan
   `DEFAULT_REVIEWER` y se **documenta el corte** —fecha de despliegue de
   F-017— en `docs/referencia/partes-proyecto.md`, para que dentro de un año
   nadie interprete que una persona aprobó doscientos partes en un día. Una
   migración que inventara autores sería falsificar auditoría.
5. **Tests sin red**: fabricar la cabecera en el `TestClient` y comprobar el
   principal en cada una de las columnas; comprobar el fallback sin cabecera;
   comprobar que una cabecera vacía o mal formada **no rompe** ninguna ruta.
   La verificación en Azure (que la cabecera llega de verdad) es MANUAL: en
   local no existe.
6. **Fuera de F-017**: los **roles** (quién puede hacer qué) siguen siendo
   F-008. F-017 responde «quién es», no «qué puede».

**Orden recomendado**: F-017 **antes** que F-016 si el humano quiere que las
filas de `empleado_jornada` nazcan ya con el usuario real desde el primer
día; **después** si prefiere no retrasar la pantalla. Las dos órdenes
funcionan sin retrabajo.

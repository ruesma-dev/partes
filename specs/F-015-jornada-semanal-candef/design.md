<!-- specs/F-015-jornada-semanal-candef/design.md -->
# F-015 · Jornada del día por jornada semanal derivada del candef y último laborable — Diseño técnico

> **Base de partida**: el estudio **F-012** (`specs/F-012-estudio-jornada-semanal/design.md`),
> con las decisiones **firmes** del humano del 2026-08-18 (§9.1, D1–D11), su
> §6.2 (firmas del resolutor), su §7 (ficheros) y su §8 (schema). Este
> documento **no reabre** ninguna de esas decisiones: las convierte en diseño
> ejecutable, cierra los huecos que el estudio dejó al implementador y
> declara en §12 las decisiones que ha tenido que tomar el spec-author.
>
> **Puerta de entrega (R35)**: esta rama **no se mergea a `dev` ni se
> despliega** hasta que **F-014** esté verificada en Sigrid. Ver §11.2: el
> orden importa y la ventana peligrosa es la inversa de la intuitiva.

## 1. Servicios que toca y por qué (LÍMITE DE SERVICIO)

| Servicio | ¿Se toca? | Por qué |
|---|---|---|
| **sv3 `partes-persistencia`** | **SÍ** | Aquí vive el cómputo de extras por exceso de jornada (`RecursoConciliador._reclasificar_extras_jornada`). Es el único sitio donde se decide cuánto de un día es ordinario y cuánto extra. Ya tiene el calendario por DNI (`CalendarioLaboralPort`, F-003). |
| **sv4 `partes-front`** | **SÍ** | Aquí viven los avisos de «jornada incompleta» (vista trabajador y matriz de obra), el KPI de jornada y la `jornada_sugerida` de «+ Nuevo». Los tres consumen `jornada_efectiva`. Ya tiene el calendario por DNI (`CalendarioProvider`). Además es quien crea el schema al arrancar. |
| **raíz del monorepo (`tests/`)** | **SÍ** | Guardianes de propiedades del monorepo, no de un servicio: copias gemelas del ORM (F-010, ampliado) y equivalencia de los dos resolutores (R19), más la variable espejo (R33). |
| sv1, sv2, sv5 | **NO** | sv1 y sv2 no saben de jornadas. sv5 recibe líneas **ya desglosadas**: el payload y la escritura en Sigrid no cambian. |
| `sigrid-api` | **NO** | El candef ya llega por `_SQL_RESHOR`; no hace falta ni una consulta nueva. |
| `infra/` | **Sí, mínimo** | La variable NO secreta `JORNADA_SEMANAL_POR_CANDEF` (misma cadena en sv3 y sv4) en el script de provisión. |

### 1.1 Duplicación: qué se duplica y qué no

La lista cerrada de `CLAUDE.md` (duplicación tolerada) es
`infrastructure/database/orm_models.py`, los clientes `infrastructure/sigrid/`
y los clientes `infrastructure/sesame/`, entre sv3 y sv4. F-015:

- **`orm_models.py`**: se toca en las DOS copias, en la misma feature, y
  quedan **byte-idénticas** (F-010 lo comprueba). Es exactamente el caso
  previsto por la lista.
- **`application/services/jornada_resolver.py`**: **ya está duplicado desde
  F-003**, con un test que compara ambas implementaciones. F-015 **amplía esa
  duplicación existente**; no crea una nueva. La duplicación se mantiene
  porque `docs/ARCHITECTURE.md` es explícito: «no hay librería compartida:
  los servicios se acoplan únicamente por mensajes, HTTP y la BBDD». El
  refuerzo es el guardián R19.
  *Punto para el humano*: ese fichero no figura por su nombre en la lista
  cerrada de `CLAUDE.md` aunque lleva duplicado desde F-003 (§13, duda 1).
- **Lo demás NO se duplica**: el puerto y el repositorio de excepciones de
  sv3 y el proveedor de sv4 son **código distinto** en cada servicio (uno
  lee con la sesión de sv3, otro con la de sv4), no copias del mismo
  fichero. No se propone ningún «servicio de jornadas»: sería un salto de red
  por cada día de cada parte y por cada celda de cada vista, para una función
  pura de veinte líneas.

## 2. Modelo: cómo se resuelve la jornada de un día

Para (recurso, DNI, fecha `d`):

1. `c = jornada_efectiva(candef_real, minimo, por_defecto)` — **sin cambios**
   (F-003, R11/R12).
2. **Excepción**: fila vigente y activa de `empleado_jornada` para el DNI
   normalizado (`desde ≤ d` y (`hasta` nulo o `d < hasta`)), leída del
   repositorio propio de cada servicio con caché TTL. Sin fila → sin
   excepción. Fallo de lectura → WARNING y sin excepción (R17).
   - con **patrón** explícito → `jornada = patron[d.weekday()]` si `d` es
     laborable, 0 si no; **FIN** (la regla del resto no se aplica).
   - con solo `jornada_semanal` → `S = fila.jornada_semanal`, `origen =
     'excepcion'`.
3. Sin excepción de `S`: `S = mapa.get(c)`; si `c` no está en el mapa,
   `S = 5 × c` y `origen = 'plana'` (el llamante emite el WARNING de R10).
4. **Regla del último laborable** con el calendario del trabajador:
   - `not es_laborable(d)` → **0**;
   - `d.weekday() >= 5` (sábado/domingo declarado laborable: solo ocurre sin
     calendario cableado, D11) → **c**;
   - `d` es L–V laborable y **existe** algún `x > d` en L–V de su semana con
     `es_laborable(x)` → **c**;
   - `d` es L–V laborable y **no** existe tal `x` → **`max(0, S − 4c)`**.

Como mucho **cinco** consultas al calendario por día (los L–V de su semana),
todas cacheadas por (DNI × año) en los dos servicios desde F-003: coste
despreciable.

Con `c = 8` y `S = 40` el último laborable recibe `40 − 32 = 8`: **idéntico a
hoy** en toda semana, con festivos o sin ellos. Esa es la propiedad que
sostiene la regresión cero (R11).

## 3. Ficheros a crear

| Fichero | Contenido | Capa |
|---|---|---|
| `services/partes-persistencia/domain/ports/jornada_empleado_port.py` | `JornadaEmpleadoRow` (dataclass: `dni_norm`, `jornada_semanal`, `patron: tuple[float,...] \| None`, `desde`, `hasta`, `origen`) y `JornadaEmpleadoPort` (ABC) con `fetch_jornadas() -> list[JornadaEmpleadoRow]` | **domain** |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | `SqlAlchemyJornadaRepository(session_factory)`: implementa el puerto leyendo `EmpleadoJornadaOrm` con `is_active` verdadero | **infrastructure** |
| `services/partes-front/application/services/jornada_provider.py` | `JornadaEmpleadoRow` (equivalente) y `JornadaEmpleadoProvider(cargar, ttl_seconds)` → `excepcion_para(dni, fecha) -> Excepcion \| None`, con caché TTL y degradación silenciosa (R17) | **application** |
| `services/partes-persistencia/tests/test_f015_r10_mapa_candef.py`, `…r11_regresion_candef8.py`, `…r12_candef_invalido.py`, `…r13_ultimo_laborable.py`, `…r14_finde_y_semana_festiva.py`, `…r15_calendario_no_registros.py`, `…r16_excepciones.py`, `…r17_tabla_caida_o_vacia.py`, `…r18_orm_empleado_jornada.py`, `…r20_computo_ultimo_laborable.py`, `…r21_hora_candef_intacto.py`, `…r22_sin_dni.py`, `…r23_degradado_review.py`, `…r28_log_trazable.py`, `…r30_ddl_empleado_jornada.py`, `…r31_revert_respeta_congelados.py`, `…r32_congelados_cuentan_no_se_tocan.py` | tests de sv3 (SQLite en memoria, dobles y calendario fake: **sin red ni BBDD**) | tests |
| `services/partes-front/tests/test_f015_r10_mapa_candef_sv4.py`, `…r12_candef_invalido_sv4.py`, `…r13_ultimo_laborable_sv4.py`, `…r16_excepciones_sv4.py`, `…r17_tabla_caida_o_vacia_sv4.py`, `…r18_orm_empleado_jornada_sv4.py`, `…r24_avisos.py`, `…r25_kpi.py`, `…r26_sugerida_fecha.py`, `…r30_ddl_empleado_jornada_sv4.py` | tests de sv4 (TestClient + SQLite + doble de calendario) | tests |
| `tests/test_f015_r19_jornada_resolver_gemelo.py` | guardián de equivalencia de los dos resolutores (API pública + tabla de ≥ 20 casos) | tests (raíz) |
| `tests/test_f015_r33_variable_espejo.py` | los dos `config/settings.py` cargados por ruta: mismo default de `JORNADA_SEMANAL_POR_CANDEF` y `JORNADA_CACHE_TTL_S` | tests (raíz) |
| `tests/test_f015_r29_guardian_cinco_tablas.py` | el guardián de F-010 sigue detectando divergencias con la tabla nueva (alteración en `tmp_path`) | tests (raíz) |

## 4. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-persistencia/application/services/jornada_resolver.py` | §5.1: `parsear_mapa_semanal`, `jornada_semanal_de`, `es_ultimo_laborable`, `Excepcion`, `DetalleJornada`, `detalle_jornada_dia`, `jornada_dia`. **`jornada_efectiva` y `candef_valido` intactas** |
| `services/partes-front/application/services/jornada_resolver.py` | **gemelo**: misma API pública y mismo comportamiento (docstrings propios de sv4, como hoy) |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` (§6) + docstring «CINCO tablas» |
| `services/partes-front/infrastructure/database/orm_models.py` | **byte-idéntico** al anterior |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | §5.2: `mapa_semanal`, `jornadas` y `jornada_cache_ttl_s` en `__init__`; `jornada_dia` en `_reclasificar_extras_jornada`; congelados (R31/R32); WARNING de mapa deduplicado; log R28 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | `revert_extras_auto()` salta congelados (R31); `fetch_registros_para_recurso()` devuelve además `sigrid_estado` y `doc_approved` (R32) |
| `services/partes-persistencia/config/settings.py` | `jornada_semanal_por_candef: str = Field("8:40,9:42", alias="JORNADA_SEMANAL_POR_CANDEF")` y `jornada_cache_ttl_s: int = Field(600, alias="JORNADA_CACHE_TTL_S")` |
| `services/partes-front/config/settings.py` | las **mismas dos** con los **mismos** defaults (variable espejo, R33) |
| `services/partes-persistencia/interface_adapters/api/app.py` | cableado: `parsear_mapa_semanal(settings.…)` (fail-fast) + `SqlAlchemyJornadaRepository` al conciliador |
| `services/partes-front/interface_adapters/web/app.py` | §5.3: `trabajador_detail` (avisos + KPI), `obra_detail` (avisos), `sigrid_empleados` (`fecha` → `jornada_dia`), `build_app(jornada_provider=None)` y fail-fast del mapa |
| `services/partes-front/infrastructure/database/parte_repository.py` | `list_jornadas_empleado() -> list[dict]` (lectura de `empleado_jornada` activa) |
| `services/partes-front/templates/trabajador_detail.html` | KPI de jornada (R25): candef efectivo, `S` aplicada con su origen y jornada del último laborable |
| `tests/test_f010_orm_models_gemelos.py` | `TABLAS` pasa a **cinco**; columnas literales de `empleado_jornada` (R29). El resto **no se relaja** |
| `services/partes-persistencia/.env.example`, `services/partes-front/.env.example` | las dos variables nuevas, mismo valor |
| `infra/create_capps_partes.ps1` | `JORNADA_SEMANAL_POR_CANDEF=8:40,9:42` en sv3 **y** en sv4 (no es secreto) |
| `docs/ARCHITECTURE.md` | semántica 3 (exceso sobre la jornada **del día**) y semántica 7 (cinco tablas) |
| `docs/referencia/partes-proyecto.md` | §4.3 (cómputo) y §5 (tabla nueva) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | schema de la base `partes` (tabla nueva) y variables nuevas. **Commit local, sin push** (ese repo no tiene remoto) |

## 5. Clases y funciones

### 5.1 Resolutor (gemelo sv3/sv4) — capa **application**

```python
# application/services/jornada_resolver.py  (las DOS copias)

def candef_valido(candef, *, minimo) -> bool: ...        # SIN CAMBIOS (F-003)
def jornada_efectiva(candef, *, minimo, por_defecto) -> float: ...  # SIN CAMBIOS

def parsear_mapa_semanal(texto: str) -> dict[float, float]:
    """'8:40,9:42' -> {8.0: 40.0, 9.0: 42.0}.

    ValueError si esta mal formado: par sin ':', valor no numerico, clave
    repetida, cadena vacia u horas fuera de (0, 24*7]. Se llama en el
    CABLEADO, para que un mapa invalido tire el arranque (R10, fail-fast).
    """

def jornada_semanal_de(candef_efectivo: float, *, mapa: Mapping[float, float]) -> tuple[float, str]:
    """(S, origen): del mapa -> ('mapa'); fuera del mapa -> (5*c, 'plana')."""

def es_ultimo_laborable(d: date, es_laborable: Callable[[date], bool]) -> bool:
    """d es L-V, laborable, y ningun dia POSTERIOR L-V de su semana lo es."""

@dataclass(frozen=True)
class Excepcion:
    semanal: float | None
    patron: tuple[float, ...] | None    # 7 valores L..D, o None
    origen: str                          # manual | sigrid | sesame

@dataclass(frozen=True)
class DetalleJornada:
    horas: float
    candef_efectivo: float
    semanal: float
    origen: str                          # mapa | excepcion | plana
    ultimo_laborable: bool

def detalle_jornada_dia(
    d: date, *, candef: float | str | None, minimo: float, por_defecto: float,
    mapa: Mapping[float, float], es_laborable: Callable[[date], bool],
    excepcion: Excepcion | None = None,
) -> DetalleJornada: ...

def jornada_dia(d: date, *, candef, minimo, por_defecto, mapa,
                es_laborable, excepcion=None) -> float:
    """Azucar: detalle_jornada_dia(...).horas — la firma que fijo F-012 §6.2."""
```

Responsabilidad: **función pura**. No abre BBDD, no llama a Sesame, no
loguea. El calendario le llega ya **ligado al DNI** como *callable*
(sv3: `lambda x: not calendario.es_no_laborable(x.isoformat(), dni=dni)`;
sv4: `lambda x: calendario_provider.dia(x, dni).laborable`). Los WARNING de
R10 y R17 los emite **quien llama**, que es quien sabe deduplicar por
recurso y por pasada/vista.

### 5.2 sv3 — `RecursoConciliador` (capa application)

- `__init__` gana `mapa_semanal: Mapping[float, float]`,
  `jornadas: JornadaEmpleadoPort | None = None` y `jornada_cache_ttl_s: int
  = 600`. Todos con valor por defecto: los tests existentes siguen
  construyéndolo igual (regresión, R11). Sin `mapa_semanal`, el default es
  `{8.0: 40.0, 9.0: 42.0}`.
- `conciliar_todos()` vacía al empezar los acumuladores de la pasada:
  `_avisados_mapa: set[int]` (R10) y `_aviso_jornadas_fallo: bool` (R17),
  igual que ya hace con `_docs_degradados`.
- `_excepcion_para(dni, fecha)`: caché TTL de la tabla entera (se espera
  vacía; una lectura por pasada) → `Excepcion | None`. Cualquier excepción
  de lectura → WARNING **una vez** y `None`.
- `_es_laborable_para(dni, regs)` → *callable* que envuelve
  `self._calendario.es_no_laborable(iso, dni=dni)` con el mismo `try/except`
  que hoy (fallo ⇒ «laborable», que es el comportamiento actual) y recoge la
  degradación con `_recoger_degradacion(regs)` (R23). Con
  `self._calendario is None` devuelve «todo laborable» (D11), lo que hace que
  el último laborable sea el viernes.
- `_reclasificar_extras_jornada`: **la rama de día no laborable no se toca**
  (sigue delante y sigue decidiéndose con `_es_no_laborable`). En la rama
  laborable, `candef_efectivo` se sustituye por
  `detalle = detalle_jornada_dia(fecha, candef=candef_real, …)` y
  `objetivo_extra = total − detalle.horas`. El resto del algoritmo —recorte
  por id descendente, extra negativa única sobre el pivote, día sin
  ordinarias, recurso sin HE— **no cambia** (R20).
- **Congelados (R31/R32)**: los registros llegan con `sigrid_estado` y
  `doc_approved`; `_congelado(reg)` es la regla, escrita **una sola vez**.
  Las líneas congeladas **suman** en `total_ord`/`total_ext` pero se excluyen
  de `ordinarios` (candidatos a recorte y a pivote). Si `delta ≠ 0` y no
  queda ninguna línea ordinaria no congelada, se emite WARNING y no se genera
  split.
- **Log R28**: cuando `detalle.horas != detalle.candef_efectivo`, los
  mensajes de recorte y de jornada incompleta añaden
  `jornada_dia=… (semanal=…, origen=…, ultimo_laborable=si|no)`.

### 5.3 sv4 — vistas y API (capa interface_adapters, con application detrás)

- `build_app(..., jornada_provider: JornadaEmpleadoProvider | None = None)`;
  si no se inyecta se construye sobre `repository.list_jornadas_empleado`.
  El mapa se parsea aquí (fail-fast, R10).
- `trabajador_detail`: el bucle de días deja de comparar contra
  `candef_efectivo` y compara contra `jornada_dia(fecha, …)` con el
  calendario del trabajador (R24). El contexto gana `jornada_kpi`
  (`candef`, `semanal`, `origen`, `ultimo_laborable`, `patron`) para el KPI
  (R25); `candef_kpi` se conserva tal cual para no romper la plantilla ni el
  aviso de contrato reducido de F-003.
- `obra_detail`: `_eff` por fila pasa a `jornada_dia` por (fila, día) usando
  `ObraMatrixRow.dni` (R24). Se mantiene el atajo actual de saltar
  findes/festivos antes de comparar.
- `sigrid_empleados`: `jornada_sugerida` **no cambia**; con
  `fecha: str | None = Query(default=None)` válida se añade `jornada_dia`
  por empleado (R26). Fecha inválida → 422 de FastAPI, nunca 500.
- `JornadaEmpleadoProvider` (application): caché TTL de la tabla entera,
  `excepcion_para(dni, fecha)`, degradación silenciosa con WARNING (R17).

## 6. SQL / schema

Este proyecto **no tiene ficheros `NN_nombre.sql`**: el schema vive en
`orm_models.py` (duplicado sv3/sv4) y los servicios lo materializan al
arrancar con `Base.metadata.create_all()` + `ddl_complementario()` (F-010).
La tabla nueva sigue ese camino: clase ORM en las dos copias, `create_all` la
crea y el generador emite sus `ALTER … ADD COLUMN IF NOT EXISTS` y su
`CREATE INDEX IF NOT EXISTS` **derivados del propio ORM**, sin lista escrita
a mano (R30).

### `empleado_jornada` (excepciones; familia de `empleado_alias`)

| columna | tipo | notas |
|---|---|---|
| `id` | Integer PK autoincrement | |
| `dni_norm` | String(32) NOT NULL, `index=True` | DNI normalizado, misma normalización que `empleado_alias` |
| `jornada_semanal` | Float NULL | `S` de la excepción; NULL si solo hay patrón |
| `h_lun`, `h_mar`, `h_mie`, `h_jue`, `h_vie`, `h_sab`, `h_dom` | Float NULL (7) | patrón explícito; los 7 a NULL = usar `S` con la regla del último laborable |
| `desde` | String(16) NOT NULL | ISO `YYYY-MM-DD`, inclusivo (mismo criterio que `parte_registros.fecha`) |
| `hasta` | String(16) NULL | ISO, **exclusivo**; NULL = vigencia abierta |
| `origen` | String(16) NOT NULL, default `manual`, `server_default='manual'` | `manual` / `sigrid` / `sesame` (futuro) |
| `nota` | String(255) NULL | |
| `is_active` | Boolean NOT NULL, default true, `server_default='true'` | papelera lógica (semántica 8 de ARCHITECTURE) |
| `created_at_utc` | String(40) NOT NULL | |
| `created_by` | String(120) NULL | |
| `updated_at_utc` | String(40) NULL | |
| `updated_by` | String(120) NULL | |

Los `server_default` de `origen` y `is_active` **son obligatorios**: sin
ellos, un `ALTER TABLE … ADD COLUMN` NOT NULL sobre una tabla con filas
haría que el servicio no arrancase (aviso escrito en el docstring de
`ddl_complementario`).

Restricciones de negocio (al menos `S` **o** patrón, sin solapes de vigencia
por `dni_norm`, horas 0–24): se validan **en aplicación** y son **de F-016**
(R27). F-015 no crea UI ni validador: la tabla nace vacía y solo se toca por
SQL manual del humano. El resolutor es defensivo ante una fila mal cargada:
patrón incompleto o valores fuera de 0–24 ⇒ se ignora la excepción con
WARNING (mismo camino de R17).

**Nada más cambia en la base**: `parte_registros` y `parte_documents` no
ganan ni pierden columnas (R21).

## 7. Configuración

| Variable | Servicios | Default | Secreto |
|---|---|---|---|
| `JORNADA_SEMANAL_POR_CANDEF` | **sv3 y sv4** (espejo, misma cadena) | `8:40,9:42` | No |
| `JORNADA_CACHE_TTL_S` | sv3 y sv4 | `600` | No |

Se parsean en el **cableado** (`interface_adapters/api/app.py` de sv3 y
`build_app` de sv4), no dentro de `config/settings.py`: así la validación
fail-fast ocurre al arrancar y `config/` no acaba importando de
`application/` (inversión de capas). Ninguna variable nueva es secreta:
viajan en el script de provisión versionado, no por Key Vault.

## 8. Plan de pruebas

Todo test es **sin red y sin BBDD**: SQLite en memoria para el ORM, dobles
para el repositorio de excepciones, calendario fake por *callable* o por la
clase `CalendarioFake` que ya usan los dorados de F-003, y
`Settings(_env_file=None)` en sv4 para no leer el `.env` del desarrollador.

- **Fase RED obligatoria** (rigor `estandar`) en R10, R13, R16, R20, R24,
  R31 y R32, con la traza real pegada en `progress/impl_F-015.md`.
- **Regresión (R11)**: los dorados de F-003 **no se modifican**. Si un test
  de F-003 hay que tocarlo, es señal de que la regresión cero se rompió:
  parar y consultar, no adaptar el test.
- Semana de referencia para los casos: **2026-03-16 (L) … 2026-03-22 (D)**,
  sin festivos nacionales, para que los festivos de los casos los ponga el
  doble de calendario y no el calendario real.
- **Campaña de mutación**: `python -m harness.mutacion --feature F-015`, con
  los supervivientes analizados en el informe.
- **MANUAL (humano)** — no se puede verificar sin BBDD ni despliegue:
  1. Arranque de sv3 y sv4 en local: en el log, «esquema inicializado (N
     sentencias complementarias)» con N mayor que el de F-010, y
     `\d empleado_jornada` en la base `partes` mostrando las 16 columnas.
  2. Portal, vista de un trabajador de la cuadrilla (ya con candef 9 en
     Sigrid): viernes de 6 h **sin** aviso de incompleto y KPI
     «9 h · 42 h/sem · último laborable 6 h».
  3. Verificación de que el reparto de una semana ya aprobada **no** cambió
     (R31/R32).

## 9. Ficheros que NO se tocan (los colindantes que tientan)

- `services/partes-email/`, `services/partes-api/`, `services/partes-transfer/`
  — sv1, sv2 y sv5 quedan intactos, incluido el payload hacia sv5.
- `jornada_efectiva` y `candef_valido`: **ni la firma ni la semántica**. Todo
  lo nuevo se construye encima.
- `CalendarioLaboralPort` (firma), `CalendarioProvider`, `HolidayProvider`,
  `calendar_builder.py`: se **consumen**, no se cambian.
- `_es_no_laborable` de sv3: sigue decidiendo la rama de día no laborable.
- `apply_extras_splits`, `_overwrite`, `_reshor_index`, `_recurso_maps`.
- `services/partes-front/application/services/congelacion.py`: F-015 **lee**
  la misma regla de congelación de F-004 en sv3, pero no la importa desde
  sv4 (servicios distintos) ni la modifica.
- `parte_registros`, `parte_documents`, `empleado_alias`, `undo_log`: ni una
  columna.
- Los clientes `infrastructure/sigrid/` y `infrastructure/sesame/`: no hay
  SQL nuevo contra Sigrid ni llamadas nuevas a Sesame.
- `services/partes-front/static/app.js`: solo si «+ Nuevo» llega a consumir
  `jornada_dia` (R26). Si se toca, `node --check` obligatorio.
- `harness/`, `CLAUDE.md`, `.env` de nadie.

## 10. Orden de implementación (resumen; el detalle en `tasks.md`)

Resolutor puro y sus tests → gemelo de sv4 y guardián R19 → ORM en las dos
copias y guardián de F-010 → sv3 (excepciones, cómputo, congelados,
cableado) → sv4 (proveedor, vistas, KPI, API) → documentación → verde.

## 11. Riesgos y decisiones

### 11.1 Riesgos heredados de F-012 §10

1. **Regresión silenciosa** (§10.4). Mitigación: R11 + dorados de F-003 sin
   tocar + guardián R19 + campaña de mutación.
2. **Calendario degradado decide el último laborable** (§10.7). Mitigación:
   R23 — el mismo régimen de F-003 (`review_required` en sv3, banner en
   sv4). No se inventa un tercer régimen.
3. **Mapa desincronizado entre sv3 y sv4** (§10.8, D9). Mitigación: mismo
   default en código verificado por test (R33), la misma cadena en el script
   de provisión, y el KPI de sv4 enseñando la `S` aplicada (R25).
4. **Recomputación de líneas ya registradas** (§10.5). Mitigación: R31/R32
   (D7). Es el riesgo más caro de esta feature: sin él, corregir un candef
   en Sigrid re-splitea en `partes` líneas que en Sigrid ya no cambian.
5. **Recurso sin DNI** (§10.9): cae al calendario por defecto y no puede
   tener excepción; con candef 9 recibe igualmente `S = 42`. Aviso, no
   bloqueo (R22).

### 11.2 Orden con F-014: la ventana peligrosa es la inversa (hallazgo de esta spec)

F-012 §10.6 dice, correctamente, que F-014 va antes. Al bajarlo a diseño
aparece un matiz que conviene que el humano tenga por escrito:

| Situación | Efecto sobre los 7 recursos de la cuadrilla |
|---|---|
| Hoy (candef 8, jornada plana) | +1 h extra L–J y −2 h el viernes = **+2 h/semana** de extra automática. Es el estado actual. |
| **F-015 desplegada, F-014 aún no** (candef 8, `S` 40) | **Exactamente lo mismo que hoy**: regresión cero (caso L de F-012). Ni mejora ni empeora. |
| **F-014 aplicada, F-015 aún no** (candef 9, jornada plana) | Viernes de 6 h ⇒ ordinaria 9 y **extra −3**; L–J sin extra. **−3 h/semana**. Peor que hoy. |
| F-014 + F-015 | Viernes de 6 h ⇒ **0 extras**. Lo que registran los humanos. |

Conclusión operativa: **la puerta de R35 se mantiene tal como la decidió el
humano** (no mergear F-015 sin F-014 verificada), pero el riesgo real está en
que RRHH cambie el candef y F-015 tarde en desplegarse. Recomendación:
coordinar el cambio en Sigrid y el despliegue de sv3+sv4 el mismo día, y si
la ventana se alarga, avisar a Administración de que esos partes llevarán
extras negativas hasta el despliegue. Como sv3 recomputa el día completo en
cada pasada, los partes **no congelados** se corrigen solos en cuanto F-015
esté desplegada; los congelados no (R31), y eso es lo correcto: ya están en
Sigrid.

### 11.3 Alternativas descartadas

- **Modelo acumulativo semanal** (F-012 §10.1): la semana llega en dos
  partes o dos meses, exigiría recomputar días anteriores (choca con F-004) y
  los avisos serían inexplicables. La regla elegida es **local al día** dado
  el calendario.
- **«Resto = lo que falte de lo trabajado»** (F-012 §10.2): absorbería
  festivos y ausencias (semana con lunes festivo ⇒ viernes de 13 h). El
  festivo cuenta como jornada (lectura A del humano).
- **Columna `jornada` en `parte_registros`** (F-012 §10.3): congela un dato
  editable, toca la tabla grande en dos copias y no sirve para días sin
  registros.
- **Tabla de configuración para el mapa** (D9): schema y UI para dos filas.
- **Validar el mapa dentro de `config/settings.py`**: obligaría a `config/`
  a importar de `application/`. Se valida en el cableado (§7).
- **`jornada_dia` devolviendo solo un `float`**: obligaría a recalcular `S`
  y el origen en cada llamante para el KPI (R25) y el log (R28). Se conserva
  `jornada_dia -> float` (la firma que fijó F-012) como azúcar sobre
  `detalle_jornada_dia` (§12, decisión DA2).
- **Excluir del todo las líneas congeladas del cálculo** (lectura literal de
  D7): dejaría un día mixto (una obra registrada, otra pendiente) calculando
  la jornada como si las horas registradas no existieran, y le daría al
  trabajador una segunda jornada completa. Ver DA3.

## 12. Decisiones tomadas por el spec-author (no estaban cerradas en F-012)

- **DA1 · Numeración heredada.** Se conservan los ids R10–R28 del bloque B de
  F-012 (y R27 se marca reservado para F-016) en lugar de renumerar desde
  R1: la trazabilidad estudio → spec → test vale más que la estética.
- **DA2 · `detalle_jornada_dia` además de `jornada_dia`.** F-012 §6.2 fijó
  `jornada_dia(...) -> float`; se mantiene **tal cual** y se añade
  `detalle_jornada_dia(...) -> DetalleJornada` (horas, candef efectivo, `S`,
  origen, si es último laborable). Sin él, R25 y R28 obligarían a cada
  llamante a recalcular por su cuenta la `S` y el origen, que es justo la
  duplicación de reglas que F-003 vino a quitar.
- **DA3 · D7 se implementa contando, no ignorando.** F-012 D7 dice «excluir
  del re-split lo registrado/encolado/approved». Al bajarlo a código,
  «excluir» de la **lectura** produce un error grave en días mixtos (ver
  §11.3). Se implementa como: las líneas congeladas **cuentan en el total del
  día** (su desglose ya conserva el total) pero **nunca se modifican**, y si
  el día no se puede cuadrar sin tocarlas, no se genera split y se avisa
  (R32). `revert_extras_auto` tampoco las toca (R31). El espíritu de D7 —lo
  que ya viajó a Sigrid no se recalcula— se cumple entero.
- **DA4 · Sábado/domingo sin calendario cableado.** D11 dice que sin
  calendario el último laborable es el viernes. Faltaba decir qué pasa con un
  sábado en esa situación: hoy sv3 le da jornada `c` (porque `_es_no_laborable`
  devuelve `False`). Se conserva: en el resolutor, un día laborable que no es
  L–V recibe `c`. Así R14 se cumple en producción (con calendario, el sábado
  no es laborable ⇒ 0) **sin** romper la regresión de los tests que corren
  con `calendario=None` (R11).
- **DA5 · El WARNING lo emite el llamante, no el resolutor.** El resolutor se
  queda **puro** (sin logging) y devuelve `origen='plana'`; sv3 y sv4 emiten
  el WARNING de R10 deduplicado por recurso y pasada/vista. Un `logger` dentro
  de una función pura llamada cinco veces por día inundaría el log.
- **DA6 · El guardián R19 vive en la raíz (`tests/`)**, como el de F-010, y
  compara **comportamiento y API pública**, no bytes: los dos
  `jornada_resolver.py` tienen hoy docstrings distintos (adrede: cada uno
  explica sus tres llamantes) y F-003 ya eligió equivalencia por
  comportamiento. Igualar los bytes sería un cambio de criterio que esta
  feature no necesita.
- **DA7 · Puerto + adaptador en sv3, proveedor en sv4.** Se sigue la
  propuesta de F-012 §7 en vez de colgar el método del repositorio grande de
  sv3: mantiene `RecursoConciliador` testable con un doble y permite que sv3
  funcione con `jornadas=None` (que es lo que harán todos los tests
  existentes). El puerto se llama `jornada_empleado_port.py` por coherencia
  con `calendario_laboral_port.py`.
- **DA8 · Lectura completa de la tabla, no consulta por DNI.** `empleado_jornada`
  nace vacía y se espera que tenga unidades de filas: se carga entera una vez
  por pasada (sv3) o por TTL (sv4) y se indexa por DNI en memoria. Un
  `SELECT` por DNI y día sería una consulta por celda de la matriz de obra.

## 13. Dudas para el humano (no bloquean la implementación salvo la 3)

1. **`jornada_resolver.py` no está en la lista cerrada de duplicación de
   `CLAUDE.md`** aunque lleva duplicado desde F-003 y F-015 lo amplía.
   ¿Se añade explícitamente a esa lista (con la fecha y el motivo, como se
   hizo con los clientes de Sigrid y Sesame en F-003)? El spec-author **no**
   ha tocado `CLAUDE.md`: es documento del humano.
2. **Ventana F-014 → F-015** (§11.2): ¿se coordina el cambio de RRHH con el
   despliegue el mismo día, o se acepta que esos 7 recursos lleven extras
   negativas mientras dure la ventana? Es una decisión de operación, no de
   código.
3. **DA3** (implementación de D7): se aparta de la letra de la decisión D7
   para no romper los días mixtos. Si el humano prefiere la lectura literal
   («excluir también del total»), hay que decirlo **antes** de T8, porque
   cambia el resultado en obras compartidas.
4. **`hasta` exclusivo**: F-012 §6.1 escribe `desde ≤ d < hasta`. Se mantiene
   exclusivo, pero conviene que quede claro para cuando F-016 pinte el
   formulario (una vigencia «hasta el 31/07» se carga como `hasta =
   2026-08-01`).
5. **Validaciones de `empleado_jornada`**: son de F-016 (R27). Hasta
   entonces las filas se cargan por SQL manual y el resolutor solo se
   defiende ignorando la fila mal formada. ¿Suficiente para el periodo
   intermedio, sabiendo que se espera que la tabla siga vacía?

### 13 bis. Respuestas del humano (2026-08-19, PARADA 1 del líder)

Las dudas 1, 2 y 3 quedan **resueltas**. Las 4 y 5 se aceptan tal como las
dejó el spec-author (`hasta` exclusivo; validaciones a F-016).

1. **Duda 1 — RESUELTA: sí.** `jornada_resolver.py` **se añade a la lista
   cerrada de duplicación tolerada de `CLAUDE.md`**, con fecha y motivo,
   igual que se hizo con los clientes de Sigrid y Sesame en F-003. La
   edición de `CLAUDE.md` se hace **dentro de F-015, en T11**
   (documentación), no antes: la lista queda entonces en
   `orm_models.py` + `infrastructure/sigrid/` + `infrastructure/sesame/` +
   `application/services/jornada_resolver.py`.
2. **Duda 2 — RESUELTA: no se envía la petición de F-014 hasta que F-015
   esté lista.** El humano elige eliminar la ventana en vez de gestionarla:
   el correo a RRHH **no sale todavía**. Consecuencia práctica: el tiempo de
   respuesta de RRHH entra en el camino crítico *después* de la
   implementación, no en paralelo. Anotado también en `progress/current.md`
   y en la cabecera de `progress/peticion_F-014.md` (rama
   `feature/F-014-candef-9-sigrid`).
3. **Duda 3 — RESUELTA: se confirma DA3**, la lectura NO literal de D7. Las
   líneas congeladas (`sigrid_estado` en {`encolado`, `registrado`} o
   documento `approved`) **cuentan en el total del día pero no se modifican
   nunca**; si el día no cuadra sin tocarlas, no se genera split y se avisa.
   Motivo: la lectura literal daría al trabajador una segunda jornada
   completa en los días mixtos (una obra ya registrada y otra pendiente).
   T6 se implementa como está diseñada.

> **Estado de la spec**: pendiente de la lectura del humano. F-015 sigue
> `pending` en `harness/features.json`; el líder no la ha pasado a
> `spec_ready`.

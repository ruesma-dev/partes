<!-- specs/F-003-sesame-festivos-jornada/design.md -->
# F-003 · Integración sesame-api: festivos y jornada reales — Diseño técnico

## 1. Servicios que toca y por qué (regla LÍMITE DE SERVICIO)

- **sv4 `partes-front`**: avisos de jornada incompleta, calendario de la
  vista trabajador, «+ Nuevo», preflight — todos consumen festivos y
  jornada. Recibe cliente Sesame propio + proveedor cacheado.
- **sv3 `partes-persistencia`**: el cómputo de extras decide «día no
  laborable» (ordinarias → extra). Recibe cliente Sesame propio y un
  `SesameCalendarioLaboral` detrás del puerto ya existente
  `CalendarioLaboralPort` (diseñado para esto: su firma ya admite `dni`).
- **sv1, sv2 y sv5 NO se tocan.** Tampoco `sigrid-api` ni la BBDD
  `partes` (esta feature no cambia schema — ver decisión D3).
- **sesame-api NO se toca desde aquí**: es otro proyecto. Lo que le falta
  se pide (sección 3), no se implementa en esta feature.

## 2. Estado real de sesame-api (explorado el 2026-08-15) y hueco documental

`C:\Users\pgris\PycharmProjects\sesame-api` — servicio FastAPI standalone
(puerto 8006), hexagonal, solo lectura, en español. Identificación de
empleados **por DNI normalizado** (casado contra `nid` de Sesame), que es
exactamente la clave de identidad de este monorepo. Autenticación por
API key propia en cabecera `x-api-key` (CSV de claves en `API_KEYS`).
Caché TTL interna (festivos 12 h) e invalidación por
`POST /api/v1/cache/invalidar`.

Endpoints relevantes para F-003 (todos envueltos en `{"ok": true, ...}`):

| Endpoint | Uso aquí |
|---|---|
| `GET /api/v1/festivos?dni=&ano=` | festivos del calendario asignado al trabajador |
| `GET /api/v1/calendarios-festivos` | calendario por defecto (`por_defecto=true`) para quien no case por DNI |
| `GET /api/v1/jornada?dni=` | `tipo`, `reducida`, `tipo_contrato` (SIN horas — ver P1) |
| `GET /api/v1/calendario?dni=&desde=&hasta=` | no se usa: componemos en local (D5) |

Errores: 401 clave, 404 DNI desconocido, 422 validación, 502 con cuerpo
`{"ok": false, "error": ...}` si Sesame upstream falla.

**Hechos que condicionan el diseño (verificados en el repo):**

1. **NO está desplegado en Azure.** Cero evidencia en el árbol y en el
   historial de las 4 ramas: sin Dockerfile, sin CI, sin scripts `az`,
   sin URL. Solo arranca en local (`python main.py`).
2. **Su código FastAPI ni siquiera está commiteado**: la rama `main`
   remota solo contiene el README; todo el servicio actual está untracked
   en la copia local.
3. **`/api/v1/jornada` NO devuelve horas** (ni día ni semana): solo el
   nombre del `workdayType`, un booleano `reducida` derivado por
   heurística de texto, y fechas de contrato. **No puede sustituir
   numéricamente al `candef` hoy.**
4. **`azure-apps/` no tiene documento de sesame-api** (verificado:
   no existe `sesame-api.md`). Hueco documental del ecosistema: el dueño
   es el proyecto sesame-api, no este repo; aquí solo se señala.

## 3. Peticiones al proyecto sesame-api (para el humano; NO se implementan aquí)

- **P1 (bloqueante para la jornada numérica).** Exponer la jornada del
  contrato en horas: ampliar `/api/v1/jornada` con `horas_dia` /
  `horas_semana` (o distribución por día). Vías upstream ya apuntadas en
  su propio `explora_sesame.py`:
  `/schedule/v1/worked-hours-by-employee-and-week-day` y las plantillas
  de horario. Hasta P1, la jornada teórica sigue saliendo del `candef`
  (R11/R15) y el enchufe queda preparado (D4).
- **P2 (bloqueante para activar en Azure).** Commitear/publicar el código
  y desplegar sesame-api en un recurso alcanzable desde las Container
  Apps de `rg-partes-dev`, con una clave dedicada para partes en
  `API_KEYS` y su valor en `kv-partes-pt7m3` (secreto `sesame-api-key`).
  Mientras tanto, la feature se puede mergear y desplegar **apagada**
  (`sesame_enabled=false` ⇒ comportamiento actual, R7/R10).
- **P3.** Escribir `azure-apps/sesame-api.md` (dueño: sesame-api).
- **P4 (menores).** Incoherencias detectadas: `.env` local con
  `SESAME_BASE_URL=eu4` pero `SESAME_REGION=eu1` (el `/health` miente);
  `GET /api/v1/empleados?dni=` omite `total` a diferencia del resto;
  cliente httpx síncrono dentro de endpoints `async` (serializa las
  peticiones); sin tests. No bloquean F-003.

## 4. La decisión central: un cliente Sesame por servicio (D1)

**Elegida**: crear `infrastructure/sesame/sesame_api_client.py` en sv3 y
en sv4, por separado, imitando el estilo de los clientes Sigrid
(constructor keyword-only con validación fail-fast, `rstrip("/")`, log de
instanciación con `key_len` y nunca la clave, errores a `RuntimeError`
con preview de 300 caracteres, `_LOG_PREFIX = "[sesame-client]"`).

- Es el precedente de F-002, textual en su design: «sin librería
  compartida, cada servicio lleva sus adaptadores y se acoplan solo por
  mensajes» — arquitectura declarada en `docs/ARCHITECTURE.md`, no
  duplicación prohibida.
- Diferencia deliberada con los clientes Sigrid: el constructor acepta
  `transport: httpx.BaseTransport | None = None` para poder testearlo con
  `httpx.MockTransport` sin red (R19). Los clientes Sigrid construyen el
  `httpx.Client` internamente y por eso hoy están sin cubrir; no
  repetimos ese defecto.

**Descartadas**:

- **A. Librería compartida** entre sv3 y sv4 — prohibida por
  `docs/ARCHITECTURE.md` («no hay librería compartida») y por el
  CLAUDE.md del repo.
- **B. Que sv4 haga de proxy de calendario para sv3** — acopla sv3 al
  portal (hoy no dependen entre sí), invierte el flujo del pipeline y
  añade un salto de red a cada persistencia.
- **C. Persistir los festivos en la BBDD `partes` y que ambos lean de
  ahí** — exige schema nuevo (trampa C3, ver D3), un job de refresco que
  no existe, y sv4 lo necesita igualmente en vivo para días sin registros.

**Decisión para el humano**: la pareja de clientes
`infrastructure/sesame/` queda declarada aquí como adaptadores por
servicio. Se propone además **ampliar la lista de duplicación tolerada
del CLAUDE.md** (regla LÍMITE DE SERVICIO) añadiendo «los clientes
`infrastructure/sesame/` (sv3 y sv4)» para que la regla «quien toque uno
cambia TODAS las copias» los proteja igual que a los Sigrid. Si el humano
prefiere no ampliarla, la feature funciona igual; solo pierde esa
protección explícita.

## 5. Otras decisiones

- **D2 · Resiliencia: fail-open en cascada, nunca KO.** Orden:
  caché vigente → llamada a Sesame → caché expirada (*stale-while-error*,
  patrón ya existente en `SigridMatcherProvider`) → calendario por
  defecto → respaldo actual (`holidays` en sv4 / `JsonCalendarioLaboral`
  en sv3), con WARNING. Justificación: la conciliación de sv3 ya es
  best-effort (envuelta en `try/except` en el pipeline) y un portal caído
  por RRHH sería peor que un festivo sin refrescar. **Descartada** la
  alternativa KO (fallar la persistencia/vista si Sesame no responde):
  rompería el pipeline por un sistema no crítico y hoy ni siquiera
  desplegado.
- **D3 · Resolución al vuelo, SIN columnas nuevas.** Festivo y jornada se
  resuelven en el momento de uso (sv3 al conciliar, sv4 al pintar), con
  caché TTL. **Descartada** la alternativa de persistir
  `festivo`/`jornada_teorica` en `parte_registros`: (a) obligaría a tocar
  las DOS copias de `orm_models.py` (trampa C3), que además ya están
  desincronizadas (sv3 tiene `horas_orig`/`extra_auto` que faltan en sv4;
  sv4 tiene las `sigrid_*` que faltan en sv3) — arreglar esa deriva es
  otra feature; (b) congelaría un dato que RRHH puede corregir en Sesame;
  (c) no evitaría el cliente en sv4, que necesita el calendario para días
  SIN registros (matriz completa, «+ Nuevo»). Se conserva `hora_candef`
  persistido como hasta ahora (diagnóstico).
- **D4 · Jornada numérica: enchufe preparado, activación bloqueada por
  P1.** Se extrae la regla actual (candef > umbral → candef; si no 8.0),
  hoy repetida en 4 sitios (sv3 `_reclasificar_extras_jornada` L486-493;
  sv4 `app.py` L495-528, L607-629 y `_sugerida` L1020-1025), a UN
  resolutor por servicio con tests de regresión (R11/R12/R15). Cuando P1
  exista, la implementación Sesame del resolutor será un cambio local +
  wiring. Mientras, de Sesame solo se usa lo que sí da: `tipo`/`reducida`
  para el badge del KPI y el aviso de divergencia (R13/R14).
- **D5 · Unidad de caché: festivos por (DNI × año), no rangos.** El
  cliente consume `/api/v1/festivos?dni=&ano=` (y el calendario por
  defecto por año); finde y `laborable` se componen en local, igual que
  hoy hacen `calendar_builder` (sv4) y el adaptador de sv3. Ventajas:
  claves de caché estables y pocas (≈ nº trabajadores activos/año, no una
  por rango consultado), y espeja la propia caché de sesame-api
  (`festivos:{empleado_id}:{ano}`). **Descartado** usar
  `/api/v1/calendario?desde=&hasta=`: cachear por rango multiplica
  entradas y no aporta nada que no sepamos calcular (weekday).
- **D6 · Matriz de obra: columna con el calendario por defecto, aviso por
  trabajador.** El tinte de columna `mx-hol` (cabecera) pasa a salir del
  calendario por defecto de Sesame (una consulta, no una por fila); la
  **exactitud por trabajador** vive donde importa: el cálculo de
  `incompletos` (R2) y el preflight (R18) evalúan festivo con el DNI de
  cada fila. **Descartado** el marcado festivo celda a celda: ruido
  visual y coste (filas × días llamadas al proveedor) para un matiz que
  el aviso ya captura. Nota: el cálculo de `incompletos` en
  `obra_detail` hoy agrupa por NOMBRE; se le añade el DNI de la fila
  (nuevo campo en el DTO `ObraMatrixRow`), sin cambiar la clave visual.
- **D7 · sv3 pasa el DNI al puerto.** `RecursoConciliador._es_no_laborable`
  recibe los registros del grupo: extrae `empleado_dni` (primer no vacío)
  y lo pasa a `CalendarioLaboralPort.es_no_laborable(fecha, dni=...)`.
  La firma del puerto NO cambia (ya admite `dni`); `JsonCalendarioLaboral`
  lo ignora como hasta ahora.
- **D8 · `holidays` NO se elimina.** Es el respaldo de sv4 (R5/R7): se
  queda en los dos `requirements.txt` de sv4. Se retirará cuando Sesame
  esté desplegado y rodado (feature futura).

## 6. Ficheros a crear

### sv4 — `services/partes-front/`

| Fichero | Contenido |
|---|---|
| `infrastructure/sesame/__init__.py` | vacío (comentario de ruta) |
| `infrastructure/sesame/sesame_api_client.py` | `SesameApiClient` (ver §8) |
| `application/services/calendario_provider.py` | `CalendarioProvider`: caché TTL + cascada de degradación + composición con el respaldo |
| `application/services/jornada_resolver.py` | `jornada_efectiva(...)` — regla candef única (R12) |
| `tests/test_f003_r*.py` | tests de la feature (nombres trazables) |

### sv3 — `services/partes-persistencia/`

| Fichero | Contenido |
|---|---|
| `infrastructure/sesame/__init__.py` | vacío |
| `infrastructure/sesame/sesame_api_client.py` | `SesameApiClient` (gemelo del de sv4) |
| `infrastructure/calendario/sesame_calendario_laboral.py` | `SesameCalendarioLaboral(CalendarioLaboralPort)` con respaldo interno |
| `application/services/jornada_resolver.py` | `jornada_efectiva(...)` (R11) |
| `tests/conftest.py` | inserta la raíz del servicio en `sys.path` (sv3 hoy NO tiene tests: se inaugura la carpeta, copiando el patrón de sv4) |
| `tests/dobles.py` | dobles de F-003 (transporte httpx, calendario fake) |
| `tests/test_f003_r*.py` | tests de la feature |

## 7. Ficheros a modificar

### sv4

- `config/settings.py`: bloque Sesame — `SESAME_API_BASE_URL`,
  `SESAME_API_KEY`, `SESAME_API_TIMEOUT_S` (10.0), `SESAME_CACHE_TTL_S`
  (21600); propiedad `sesame_enabled`. Los `HOLIDAYS_*` se quedan.
- `interface_adapters/web/app.py`:
  - wiring en `build_app` (junto al `HolidayProvider`, L294-298):
    construir `SesameApiClient` + `CalendarioProvider` si
    `sesame_enabled` (log `[sesame][wiring] CABLEADO/DESACTIVADO`);
    `build_app` acepta `calendario_provider=None` inyectable para tests,
    como ya hace con `repository`/`transfer_client`.
  - `trabajador_detail` (L423-551): festivos y `dias_incompletos` vía
    proveedor con el DNI del trabajador (R2/R3); KPI jornada con
    `tipo`/`reducida` y aviso de divergencia (R13/R14); regla candef vía
    `jornada_efectiva` (R12).
  - `obra_detail` (L579-651): `holiday_name` de columna = calendario por
    defecto; `incompletos` evaluando festivo por DNI de fila (D6);
    `jornada_efectiva`.
  - `_sugerida` (L1020-1025) → delega en `jornada_efectiva`.
  - nuevo endpoint `GET /api/calendario` (R16).
  - preflight de aprobación: anotar líneas en festivo/domingo (R18).
- `infrastructure/database/parte_repository.py`: añadir `dni` al DTO
  `ObraMatrixRow` (y poblarlo en `get_obra`). **Nada más** de este
  fichero.
- `templates/trabajador_detail.html`: badge jornada contrato + aviso
  divergencia.
- `templates/nuevo_parte.html` y `static/app.js` (L1202-1259): rejilla
  con clases festivo/domingo alimentada por `GET /api/calendario`,
  confirmación no bloqueante al enviar (R17). `static/styles.css`:
  clases nuevas.
- `.env.example`: bloque `SESAME_*` documentado (placeholders, sin
  valores reales).

### sv3

- `config/settings.py`: mismo bloque `SESAME_*` + `sesame_enabled`.
  `CALENDARIO_LABORAL_PATH` se queda (respaldo).
- `interface_adapters/api/app.py` (wiring L87-95): si `sesame_enabled`,
  `calendario = SesameCalendarioLaboral(cliente, respaldo=JsonCalendarioLaboral(...))`;
  si no, `JsonCalendarioLaboral` como hoy. Log CABLEADO/DESACTIVADO.
- `application/services/recurso_conciliador.py`:
  `_es_no_laborable(fecha_int, regs)` extrae el DNI del grupo y lo pasa
  al puerto (D7); la regla candef de L486-493 delega en
  `jornada_efectiva` (R11). El resto del algoritmo NO cambia.
- `.env.example`: bloque `SESAME_*`.

### Transversales

- `infra/`: variables `SESAME_API_BASE_URL` (redactada) y
  `SESAME_API_KEY` como `keyvaultref` al secreto `sesame-api-key` de
  `kv-partes-pt7m3`, en los manifiestos/scripts de sv3 y sv4 (valores
  reales en `*.local.ps1`, sin versionar). Sin desplegar: el deploy lo
  lanza el humano.
- `azure-apps/partes.md` (repo `azure-apps`): declarar el consumo de
  sesame-api (R21).
- `harness/features.json`: estado de F-003 según el flujo del arnés.

## 8. Clases y funciones (firma, responsabilidad, capa)

### `SesameApiClient` (infrastructure, sv3 y sv4 — gemelos)

```python
class SesameApiClient:
    def __init__(self, *, base_url: str, api_key: str,
                 timeout_s: float = 10.0,
                 transport: httpx.BaseTransport | None = None) -> None: ...
    def festivos(self, dni: str, ano: int) -> list[FestivoDia]: ...
    def calendario_por_defecto(self, ano: int) -> list[FestivoDia]: ...
    def jornada(self, dni: str) -> JornadaContrato | None: ...
```

- `FestivoDia` y `JornadaContrato`: `@dataclass(frozen=True)` en el mismo
  módulo (`fecha: str ISO`, `nombre: str | None`; `tipo`, `reducida`,
  `tipo_contrato`). En sv3 los tipos se declaran junto al puerto si el
  dominio los necesita; el puerto existente no cambia.
- 404 de DNI → `None`/lista según método (no excepción); resto de errores
  → `RuntimeError` (lo captura el proveedor, no el llamante final).
- `calendario_por_defecto`: de `GET /api/v1/calendarios-festivos`, toma
  el de `por_defecto=true` y filtra por año.

### `CalendarioProvider` (application, sv4)

```python
class CalendarioProvider:
    def __init__(self, *, cliente: SesameApiClient | None,
                 respaldo_holiday_name: Callable[[date], str | None],
                 ttl_seconds: int = 21600) -> None: ...
    def holiday_name_para(self, dni: str | None) -> Callable[[date], str | None]: ...
    def dia(self, d: date, dni: str | None) -> DiaCalendario: ...
    def jornada_contrato(self, dni: str | None) -> JornadaContrato | None: ...
```

- Devuelve *callables* `holiday_name` compatibles con `build_calendar` y
  `get_obra` (mismo contrato que `HolidayProvider.name`): el resto de
  sv4 no nota el cambio de fuente.
- Caché `dict` bajo `threading.RLock` con claves `fest:{dni_norm}:{ano}`,
  `fest:_default:{ano}`, `jornada:{dni_norm}`; *stale-while-error* como
  `SigridMatcherProvider` (guarda `(timestamp, valor)` y reutiliza el
  valor caducado si la recarga falla).
- `cliente is None` (Sesame no configurado) ⇒ delega siempre en el
  respaldo (R7) sin tocar red.

### `SesameCalendarioLaboral` (infrastructure, sv3)

```python
class SesameCalendarioLaboral(CalendarioLaboralPort):
    def __init__(self, *, cliente: SesameApiClient,
                 respaldo: CalendarioLaboralPort,
                 ttl_seconds: int = 21600) -> None: ...
    def es_no_laborable(self, fecha_iso: str, *, dni: str | None = None,
                        localizacion: str | None = None,
                        convenio: str | None = None) -> bool: ...
```

- Finde en local; festivo por caché (DNI × año) → calendario por defecto
  → `respaldo.es_no_laborable(...)` (R9). Nunca propaga excepciones.

### `jornada_efectiva` (application, sv3 y sv4 — misma regla)

```python
def jornada_efectiva(candef: float | None, *, minimo: float,
                     por_defecto: float) -> float:
    """Regla única: candef si es válido (> minimo), si no por_defecto."""
```

### Endpoint sv4 (interface_adapters)

`GET /api/calendario?desde=YYYY-MM-DD&hasta=YYYY-MM-DD[&dni=]` →
`{"ok": true, "data": [{fecha, laborable, fin_de_semana, festivo,
festivo_nombre}]}`; 422 si fechas inválidas o rango > 62 días (R16).

## 9. SQL

No aplica: sin cambios de schema ni SQL nuevo (decisión D3). No se toca
ninguna copia de `orm_models.py`.

## 10. Tests (estrategia, sin red — R19)

- Cliente: `httpx.MockTransport` con respuestas reales de sesame-api
  (fixtures JSON del formato `{"ok": true, ...}`), incluyendo 404, 502 y
  cuerpo no-JSON.
- Proveedores: dobles del cliente (fake que cuenta llamadas) para TTL
  (R6), *stale-while-error* y cascada (R4/R5/R9); `time` monkeypatcheado.
- sv4 vistas y endpoint: `TestClient(build_app(Settings(_env_file=None),
  repository=ParteReviewRepository(FabricaSesionSqlite()),
  calendario_provider=<doble>))` — patrón F-002. OJO: siempre
  `Settings(_env_file=None)` (el `.env` se resuelve por ruta absoluta).
- sv3: se inaugura `services/partes-persistencia/tests/` (hoy no existe);
  regresión de `_reclasificar_extras_jornada` con calendario fake
  (laborable/festivo) y casos dorados de splits (R15).
- JS: `node --check static/app.js` + parseo Jinja2 de plantillas tocadas
  (convención sv4). El comportamiento visual de R17 se verifica MANUAL.

## 11. Riesgos

1. **sesame-api sin desplegar ni commitear (P2)**: el riesgo operativo es
   activar `SESAME_*` contra una URL que no existe. Mitigación: la
   feature entera degrada a comportamiento actual con `sesame_enabled=
   false`, y la activación en Azure es un paso manual del humano
   posterior a P2.
2. **Cambio de contrato de sesame-api** (código aún no publicado, puede
   mutar): los tests del cliente fijan el contrato con fixtures; si
   sesame-api cambia, fallan los tests del cliente, no el portal en
   producción (fail-open).
3. **Divergencia sv3/sv4 en festivos durante la transición**: si solo un
   servicio tiene Sesame activo, sv3 y sv4 pueden discrepar en un
   festivo (ya discrepan hoy: Madrid vía `holidays` en sv4 vs nacionales
   en sv3). Mitigación: activar `SESAME_*` en ambos a la vez; la
   discrepancia actual queda documentada y esta feature la ELIMINA
   cuando ambos están cableados.
4. **Trabajadores sin DNI en Sesame** (su propio explorador lo avisa):
   caen al calendario por defecto (R4) — mismo trato que hoy, que ya era
   global.
5. **Rendimiento matriz de obra**: N filas × consulta de festivos por
   DNI. Mitigado por la caché (DNI × año): tras la primera carga del mes
   son hits de memoria.

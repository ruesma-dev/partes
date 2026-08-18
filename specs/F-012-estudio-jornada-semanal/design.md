<!-- specs/F-012-estudio-jornada-semanal/design.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Diseño técnico

> Este documento ES el entregable de F-012: estudio con datos reales
> (§3), análisis (§4), fuentes (§5), modelo propuesto (§6), ficheros de la
> implementación (§7–§8) y decisiones abiertas para el humano (§9). La
> implementación se propone como feature aparte (**F-014**, y opcionalmente
> **F-015** para la UI de mantenimiento) porque toca dos servicios, añade
> una tabla al schema duplicado y depende de decisiones de negocio que hoy
> nadie ha tomado. F-012 no cambia código.

## 1. Servicios que toca y por qué (regla LÍMITE DE SERVICIO)

**F-012 (este estudio): ninguno.** Solo `specs/F-012-estudio-jornada-semanal/`.
Las consultas del §3 se hicieron en modo SOLO LECTURA (`sigrid-api`
`POST /api/sql/read` sobre `ruesma`; `SELECT` sobre la BBDD `partes` de
desarrollo) desde un script de usar y tirar fuera del repositorio; el SQL
va en el anexo para que cualquiera lo reproduzca.

**F-014 (implementación propuesta)** tocaría, y por esto:

- **sv3 `partes-persistencia`**: es donde vive el cómputo de extras por
  exceso de jornada (`RecursoConciliador._reclasificar_extras_jornada`). La
  jornada del día deja de ser «candef plano» y pasa a depender del día de
  la semana y del trabajador. Necesita LEER la jornada particularizada.
- **sv4 `partes-front`**: es donde viven los avisos de «jornada
  incompleta» (vista trabajador y matriz de obra), el KPI de jornada y la
  `jornada_sugerida` de «+ Nuevo». Los tres consumen `jornada_efectiva`,
  el resolutor que F-003 dejó como único punto de entrada precisamente
  para esto. Y es el único servicio con UI: si la jornada particularizada
  se mantiene desde el portal (D5), el mantenimiento va aquí.
- **La regla se escribe DOS veces (resolutor gemelo)**, como ya ocurre con
  `jornada_resolver.py` desde F-003 y como manda `docs/ARCHITECTURE.md`
  (sin librería compartida). El guardián que compara ambas copias se
  amplía (R14). NO se propone extraer un «servicio de jornadas»: sería un
  salto de red en cada persistencia y en cada vista para una función pura
  de diez líneas.
- **La tabla nueva `empleado_jornada` entra en las DOS copias de
  `orm_models.py`** (duplicación tolerada del CLAUDE.md, trampa 3 de C3).
  OJO: las copias ya están desincronizadas (F-010, pendiente); F-014
  puede añadir la clase nueva idéntica en ambas sin resolver la deriva
  previa, pero es más limpio hacer F-010 antes (D6).
- **sv1, sv2 y sv5 NO se tocan.** sv5 recibe líneas ya desglosadas
  (ordinaria/extra) y no sabe de jornadas. `sigrid-api` tampoco (todo es
  lectura con el SQL que ya usa sv3).
- **Sigrid NO se escribe** (ni `reshor.candef`, ni `auxtur`, ni `emphis`):
  fuera del alcance de este monorepo (§5, S2). Si el humano quiere que
  RRHH mantenga algo en Sigrid, es una decisión suya, no una tarea de
  aquí.

## 2. Cómo funciona hoy (lo que el estudio pone en cuestión)

- **Jornada teórica = `reshor.candef` de la hora por defecto del recurso**
  (`res.horide`), y 8 h si el candef no es válido (≤ 2). Regla única en
  `jornada_efectiva(candef, minimo, por_defecto)` (F-003, R11/R12), con
  copias gemelas en sv3 y sv4. La jornada es **la misma todos los días
  laborables**: no distingue viernes ni sabe de semanas.
- **Cómputo de extras (sv3)**, por (recurso, día) reuniendo todas las
  obras: en día laborable, `extra objetivo = ordinarias + extras − candef
  efectivo`; si falta extra se recorta lo ordinario (ids mayores primero);
  si sobra, se **sube** el ordinario hasta la jornada y se crea UNA extra
  automática **negativa** («viernes típico: 6 h con jornada 8 → ordinaria
  8, extra −2»). Fin de semana/festivo: todo lo ordinario a extra. Recurso
  sin código HE: no se toca nada.
- **Avisos «jornada incompleta» (sv4)**: día laborable con `0 < ordinarias
  < candef efectivo`. Con jornada plana, TODO viernes corto sale marcado.
- **Recomputación total en cada pasada**: `revert_extras_auto()` deshace
  las extras automáticas de TODOS los registros activos y se recalcula
  desde cero (idempotente por diseño). No excluye líneas ya registradas en
  Sigrid (ver riesgo §10.5).

## 3. Estudio con datos reales

**Método.** Consultas de solo lectura el 2026-08-18: (a) Sigrid, base
`ruesma`, vía `sigrid-api` `POST /api/sql/read` con `max_rows` ≤ 1000
(ninguna respuesta llegó truncada; las agregaciones se hicieron en el
servidor, nunca cruzando tablas en cliente); (b) BBDD `partes` de
desarrollo (`SELECT` sobre `parte_registros`). Ventana del histórico:
`hmores.fec` en [20250101, 20260901). «Recurso vivo» = `con.fecbaj` nulo o
0. Ordinarias = códigos `HL%` (HLOF/HLGR/HLPE); extras = `HE%`. Día de la
semana calculado en servidor con `DATEPART(dw)` corregido por
`@@DATEFIRST` (1 = lunes). El SQL exacto está en el anexo A.

### H1 · Distribución del `candef` (hora por defecto de cada recurso vivo)

| candef | recursos | lectura |
|---|---|---|
| 1.0 | 561 | mensuales/otros: hora por defecto MENC, MJEFO, OGAS, OTEL… (no es una jornada) |
| 0.0 | 199 | no informado |
| **8.0** | **106** | jornada real informada (HLOF 79, HLGR 24, HLPE 5; algún MCAP/HEOF suelto) |
| **9.0** | **1** | un único recurso (H2) |
| otros >2 | 0 | no existe ningún candef 7, 10, 35, 40… |

Total 867 recursos vivos con hora por defecto. `candef` solo dice algo
para ~107 recursos (los que cobran por horas); el resto cae al fallback
de 8 h que ya aplica `jornada_efectiva`.

### H2 · «La gente que tiene 9 h como candef» es UNA persona

Recurso `MO/0037` (`res.ide` 2798044), OFIC. 2ª ALBAÑIL, hora por defecto
HLOF con `candef = 9`, con código HEOF (sí computa extras). Alta reciente:
su primer parte en Sigrid es del 2026-07-13. Su histórico registrado
(29 líneas): **7 h HLOF todos los días laborables** de julio y agosto
(jornada intensiva de verano, H6), tres días con HEOF +1, y una
incidencia CIE/CIZ. Ni un solo día de 9 h todavía. Dos observaciones:

- El `candef = 9` no describe lo que hace hoy (7 h): describe la jornada
  que tendrá fuera del verano (presumiblemente 9 h L–J con la cuadrilla
  de H5).
- **No tiene DNI en `emp`** (`res.conide` no enlaza con un empleado con
  DNI). El sistema lo resolverá solo por nombre/alias, no por DNI: dato a
  corregir en Sigrid (aviso al humano, fuera del alcance de F-012).

### H3 · Cómo se registran hoy los viernes (histórico `hmores`, candef 8)

Pares (ordinaria, extra) más frecuentes en **viernes** de recursos con
candef 8 (3.498 viernes con ordinarias):

| ord | extra | días | lectura |
|---|---|---|---|
| 8 | 0 | 836 | viernes de 8 h |
| 8 | **−2** | 810 | viernes de 6 h registrado como 8 − 2 |
| 8 | +1 | 678 | |
| 8 | **−3** | 328 | viernes de 5 h como 8 − 3 |
| 7 | 0 | 247 | intensiva (H6) |
| 8 | +2 | 234 | |
| 8 | −1 | 157 | |

Suma neta de extras en viernes: **−1.101 h** (negativa); en L–J es
positiva (+4.600…+5.000 h por día de semana). Es decir: **la práctica
humana en Sigrid ya usa el modelo «jornada diaria + extra negativa el
viernes»**, exactamente lo que sv3 automatiza. No aparece NINGÚN viernes
de 4 h (n=0 de 3.498) ni de 9 h (n=1). El patrón «9+9+9+9+4» que
enunciaba la petición **no existe en el histórico**.

### H4 · Semanas completas (5 días laborables con horas): horas ordinarias

| candef | h ordinarias/semana | semanas | recursos |
|---|---|---|---|
| 8 | **40** | 2.351 | 81 |
| 8 | 35 | 362 | 69 (intensiva, H6) |
| 8 | **48** | 222 | 9 |
| 8 | **42** | 46 | 7 |
| 8 | 41 | 4 | 4 |
| 8 | 43–58 | 7 | 6 (puntuales) |
| 9 | 35 | 4 | 1 (MO/0037, intensiva) |

Semanas de 39/38/37/16 h: residuales (< 10 en total). Conclusión: la
inmensa mayoría es 40 h; hay un **grupo estable por encima de 40** (H5) y
un bloque estacional de 35 (H6). «Más de 40 h semanales» es real y
concentrado.

### H5 · El grupo que hace más de 40 h: una cuadrilla de 7 oficiales

Recursos con ≥ 15 semanas completas por encima de 40 h: **7**, todos
OFIC. 1ª ALBAÑIL, todos con DNI en `emp` y con código HE, todos con
`candef = 8` en Sigrid: `MO/0006`, `MO/0007`, `MO/0008`, `MO/0031`,
`MO/0366`, `MO/0405`, `MO/0456`. Su patrón registrado por los humanos:

| periodo | L | M | X | J | V | semana | extras registradas |
|---|---|---|---|---|---|---|---|
| 2025-01 → 2026-04 | 10 | 10 | 10 | 10 | 8 | **48** | ≈ 0 (netas por debajo de ±1 h/día) |
| 2026-05 → 2026-06 | 9 | 9 | 9 | 9 | **6** | **42** | ≈ 0 |
| 2026-07 → 2026-08 | 7 | 7 | 7 | 7 | 7 | 35 | 0 (intensiva) |

Lo relevante para el diseño:

- Sigrid les tiene `candef = 8`. **sv3 hoy** les generaría, en el régimen
  de 42 h: +1 h extra L–J y −2 h el viernes = **+2 h/semana**; en el de
  48 h: **+8 h/semana**. Los humanos registraron **0**. Hay una
  discrepancia de fondo que ninguna regla resuelve sola: ¿su jornada
  semanal es 42/48 (y entonces 0 extras) o es 40 y esas horas son extras
  no registradas? Es la decisión D3.
- Su viernes NO es «el resto hasta 40» (sería 4): es 6. Solo con una
  jornada semanal **particularizada a 42** la regla «viernes = resto»
  reproduce lo que hacen. Es exactamente lo que el humano intuía.
- El régimen cambia con el tiempo (48 → 42 → 35): la jornada
  particularizada necesita **vigencia** (desde/hasta), no un número fijo.

### H6 · Hallazgo colateral: jornada intensiva de verano (7 × 5 = 35 h)

Julio-agosto 2025: 667/543 días de 7 h frente a 283/251 de 8 h; julio
2026: 754 frente a 311; agosto 2026 (parcial): 388 frente a 34. Los
humanos registran **7 ordinarias y 0 extra**; sv3 hoy registraría **8
ordinarias y −1 extra** cada día. No es objeto de F-012 (es F-011,
«jornada reducida por días»), pero el modelo del §6 lo cubre con un patrón
explícito con vigencia, y la fuente del §5 es la misma. Se anota para que
F-011 no reinvente otra tabla.

### H7 · Campos de jornada en Sigrid: existen, pero están vacíos

| tabla.campo | qué es | estado real |
|---|---|---|
| `auxtur` (`horlun`…`hordom`) | turnos con horas por día de semana | **1 fila**: «Normal» 8-8-8-8-8-0-0 |
| `emphis.turide` → `auxtur` | turno del empleado (histórico RRHH) | 0 (sin turno) en 1.623 de 1.633 filas |
| `emphis.numhor` | horas contratadas | 8 → 360 filas, 35 → 4, 4 → 2, resto 0 |
| `emphis.porjorlab` | % de jornada | 100 → 1.559 filas; **87,5 → 20; 75 → 14; 50 → 9; 62,5 → 7**… |
| `emphis.rjgl` | reducción por guarda legal | 23 filas |
| `resjor`, `caljor`, `e_jor`, `auxjla` | calendario de jornadas por recurso, jornadas RRHH | **vacías** |
| `calcab` | calendarios (MADRID, SEVILLA…, uno por obra) | 20; `caltur` 120 filas, todas al turno «Normal» |

Es decir: Sigrid tiene la **estructura** ideal (`auxtur` es literalmente
un patrón semanal) pero nadie la mantiene; y `emphis.porjorlab` es una
**fuente real de jornada reducida** que F-011 dio por inexistente
(porcentajes de 87,5 %, 75 %, 50 %). `emphis` es histórico de nómina (una
fila por cambio, `fec`): habría que tomar la última fila ≤ fecha.

### H8 · La BBDD `partes` de desarrollo no sirve para patrones

104 líneas activas, 5 DNIs, julio-agosto 2026: datos de prueba. Todo el
análisis de patrones se apoya en `hmores` (Sigrid), que es la verdad
registrada por Administración durante 20 meses.

## 4. Análisis: qué cambia con «viernes = resto hasta la jornada semanal»

Notación: candef c, jornada semanal S, patrón derivado
`L–J = c, V = S − 4c`. Extras netas de la semana = Σ(trabajado) − Σ(patrón
de los días laborables).

| caso | horas trabajadas L–V | hoy (candef plano) | propuesto | comentario |
|---|---|---|---|---|
| A. c=9, S=40 (la petición) | 9,9,9,9,4 | L–J 0; V ord 9 / extra **−5**; neto −5; aviso «incompleto» cada viernes | V jornada 4 → 0 extra; neto 0; sin aviso | el motivo de la feature |
| A'. ídem, viernes de 9 h | 9,9,9,9,9 | 0 extras (45 h sin extra) | V ord 4 + **5 extra** | hoy se PIERDEN 5 h extra |
| B. cuadrilla H5, c=8 (Sigrid), S=40 | 9,9,9,9,6 | +1×4, V −2 → **+2** | igual (+2) | los humanos registran 0: D3 |
| B'. cuadrilla, c=9, S=42 | 9,9,9,9,6 | (con c=9) V 9/−3 → −3 | V jornada 6 → **0** | reproduce la práctica humana |
| C. régimen 48, c=10, S=48 | 10,10,10,10,8 | (con c=8) +8/sem | 0 | ídem |
| D. c=9, S=40, festivo lunes | —,9,9,9,4 | V −5 | V 4 → 0; jornada teórica de la semana 31 h | el viernes NO absorbe el festivo (ver §6.2) |
| E. semana partida entre dos meses | — | día a día | día a día | el modelo es local al día: indiferente al parte mensual |
| F. parte que solo trae L–M | 9,9 | 0 | 0 | ídem; el viernes se calcula cuando llegue |
| G. sábado/festivo trabajado | 6 (S) | todo a extra | todo a extra | sin cambio (jornada 0) |
| H. intensiva 7×5 (fuera de F-012) | 7,7,7,7,7 | 8/−1 cada día | con patrón explícito 7×5 vigente: 0 | F-011 sobre la misma tabla |
| I. recurso sin HE (MENC) | — | no se normaliza | no se normaliza | sin cambio |
| J. candef inválido (0/1) | 8,8,8,8,8 | 8 → 0 | patrón 8×5 → 0 | sin cambio |

Conclusión del análisis: el modelo «patrón semanal derivado (o
explícito) por trabajador, aplicado día a día» reproduce lo pedido,
mantiene la **regresión cero** para candef 8 / 40 h (la mayoría), corrige
la pérdida de extras del caso A', y es **compatible con el pipeline
actual** (grupo por (recurso, día), parte mensual, F-004) porque no
necesita ver la semana entera. El modelo alternativo «acumular la semana y
volcar la diferencia el viernes» se descarta (§10.1).

## 5. De dónde sale la jornada semanal particularizable (D1)

| fuente | ¿datos hoy? | quién la mantiene | pros | contras |
|---|---|---|---|---|
| **S1. Tabla propia `empleado_jornada` en la BBDD `partes`** (recomendada) | no; se crea vacía y todo cae al defecto 40 h | Administración desde el portal (D5) o el humano por SQL | control total; por DNI (misma clave que `empleado_alias`); vigencias; ambos servicios ya leen `partes`; el mismo sitio sirve a F-011 (patrón 7×5 con fechas) y admite `origen` sigrid/sesame en el futuro | schema en dos copias (F-010); otra verdad además del candef; hay que mantenerla a mano |
| S2. Sigrid: `auxtur` + `emphis.turide` (o `numhor`/`porjorlab`) | estructura sí, datos **no** (H7) | RRHH en Sigrid; nosotros solo leeríamos por sigrid-api | una sola verdad (Sigrid); sin schema aquí | depende de RRHH; `emphis` es histórico de nómina con semántica propia; NO se puede escribir desde aquí; el candef seguiría siendo otra fuente paralela |
| S3. Sesame (contrato / horarios) | **no**: 0/218 contratos (F-013); módulo horarios sin explorar; P1 pendiente | RRHH en Sesame | verdad de RRHH | plazo desconocido; sesame-api ni desplegado |
| S4. Fichero de parametrización versionado (por código `MO/NNNN`) | — | git | trivial | datos por persona en git (aunque sea por código); redeploy por cada cambio; sin vigencias cómodas. Descartado como fuente; a lo sumo semilla |

**Recomendación**: S1 ahora, con columna `origen` para que S2/S3 puedan
alimentarla más adelante sin cambiar el modelo. Los `candef` de Sigrid se
siguen leyendo como hasta ahora (son la base del patrón derivado); la
tabla solo aporta lo que Sigrid no tiene: la jornada semanal y, si hace
falta, el patrón explícito con fechas.

## 6. Modelo propuesto (para F-014)

### 6.1 Concepto

`PatronSemanal` = 7 floats (L…D) + `semanal` (suma) + `origen`
(`derivado` | `explicito`) + vigencia. Regla de resolución para (DNI,
fecha):

1. Fila vigente en `empleado_jornada` con patrón explícito → ese patrón.
2. Fila vigente sin patrón explícito pero con `jornada_semanal` → patrón
   derivado con esa S.
3. Sin fila → patrón derivado con `JORNADA_SEMANAL_POR_DEFECTO` (40).

Patrón derivado: `L–J = candef efectivo`; `V = max(0, S − 4 × candef
efectivo)`; `S/D = 0`. Con (8, 40) sale 8×5: **idéntico a hoy**.

### 6.2 Reglas de contorno (a validar por el humano)

- **El calendario manda sobre el patrón**: día no laborable (finde/festivo
  según `CalendarioLaboralPort` / `CalendarioProvider`) ⇒ jornada 0 y todo
  a extra, aunque el patrón diga otra cosa. Un patrón con sábado > 0 no
  convierte el sábado en laborable (si algún día se necesita, es otra
  decisión).
- **El viernes NO absorbe festivos ni ausencias**: es un valor fijo del
  patrón, no «lo que falte de lo trabajado». Semana con festivo el lunes y
  c=9/S=40: jornada teórica 9+9+9+4 = 31 (hoy sería 32 con 8×4). La
  alternativa «resto de lo realmente trabajado» daría viernes de 13 h en
  esa semana: absurda.
- **`hora_candef` se sigue persistiendo con el candef real** (diagnóstico,
  R19). La jornada del día aplicada se traza en log (R25); no se añade
  columna a `parte_registros` (misma decisión D3 de F-003: sin columnas
  nuevas en la tabla grande).
- **Recurso sin código HE**: sin cambios (no se normaliza nada).
- **DNI**: la clave de la tabla. sv3 lo toma del grupo (como
  `_es_no_laborable`); sin DNI ⇒ patrón derivado por defecto (R20).

### 6.3 Firma del resolutor (gemelo sv3/sv4)

```python
# application/services/jornada_resolver.py (ambas copias)
@dataclass(frozen=True)
class PatronSemanal:
    horas: tuple[float, float, float, float, float, float, float]  # L..D
    origen: str  # "derivado" | "explicito"
    semanal: float  # suma de horas

def patron_derivado(candef_efectivo: float, semanal: float) -> PatronSemanal: ...

def jornada_dia(fecha: date, *, candef: float | str | None, minimo: float,
                por_defecto: float, semanal: float,
                patron: PatronSemanal | None = None) -> float:
    """Jornada teórica del día: patrón explícito si lo hay; si no,
    derivado de jornada_efectiva(candef) y `semanal`. Sábado/domingo 0."""
```

`jornada_efectiva` y `candef_valido` **no cambian** (los usa el KPI y son
la base del patrón derivado).

### 6.4 sv3 — cómputo

- `RecursoConciliador.__init__` gana `jornada_semanal_horas: float = 40.0`
  y `jornadas: JornadaEmpleadoPort | None` (puerto de lectura de la tabla,
  con caché TTL en el conciliador como `_reshor_cache`).
- En `_reclasificar_extras_jornada`, la línea
  `candef_efectivo = jornada_efectiva(...)` pasa a
  `jornada_del_dia = jornada_dia(fecha, candef=candef_real, …,
  semanal=S_del_dni, patron=patron_del_dni)`; `objetivo_extra = total −
  jornada_del_dia`. Nada más del algoritmo cambia.
- Lectura de la tabla con `try/except` → WARNING y defecto (R16). Sin
  puerto cableado (`None`) ⇒ comportamiento actual (misma filosofía que
  `calendario=None`).

### 6.5 sv4 — avisos, KPI y «+ Nuevo»

- `trabajador_detail`: `candef_efectivo` → `jornada_dia(...)` por día del
  calendario; el KPI muestra el patrón (`candef_kpi` gana `patron`,
  `semanal`, `particularizada: bool`).
- `obra_detail`: `_eff` por fila y día → `jornada_dia(...)` con el DNI de
  la fila (ya está en `ObraMatrixRow.dni` desde F-003).
- `_sugerida` / `GET /api/sigrid/empleados`: no cambia salvo `jornada_dia`
  opcional cuando llega `fecha` (R23).
- Proveedor `JornadaEmpleadoProvider` (application) con caché TTL por DNI y
  fallback al defecto, cableado en `build_app` con inyección para tests
  (patrón `calendario_provider`).
- (D5 / F-015) rutas `/admin/jornadas` + plantilla + validaciones (R24).

## 7. Ficheros (para F-014; F-012 no crea ninguno fuera de `specs/`)

### Crear

| Fichero | Contenido |
|---|---|
| `services/partes-persistencia/domain/ports/jornada_empleado.py` | `JornadaEmpleadoRow` (dni_norm, semanal, horas L..D o None, desde, hasta, origen) y puerto `JornadaEmpleadoPort.fetch_jornadas() -> list[JornadaEmpleadoRow]` |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | implementación sobre `EmpleadoJornadaOrm` |
| `services/partes-persistencia/tests/test_f014_r*.py` | tests R10–R20, R25 (sin red ni BBDD: SQLite en memoria / dobles) |
| `services/partes-front/application/services/jornada_provider.py` | `JornadaEmpleadoProvider(repository, ttl_seconds, semanal_defecto)` → `patron_para(dni, fecha)` |
| `services/partes-front/tests/test_f014_r*.py` | tests R10–R17, R21–R23 (TestClient + SQLite) |
| (D5) `services/partes-front/templates/admin_jornadas.html` | mantenimiento (R24) |

### Modificar

| Fichero | Cambio |
|---|---|
| `services/partes-persistencia/application/services/jornada_resolver.py` | `PatronSemanal`, `patron_derivado`, `jornada_dia` (§6.3) |
| `services/partes-front/application/services/jornada_resolver.py` | gemelo, idéntico |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` (§8) |
| `services/partes-front/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` idéntico; `create_all` de sv4 la crea al arrancar |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | §6.4 |
| `services/partes-persistencia/config/settings.py` y `services/partes-front/config/settings.py` | `JORNADA_SEMANAL_POR_DEFECTO` (40.0), `JORNADA_CACHE_TTL_S` |
| `services/partes-persistencia/interface_adapters/api/app.py` | wiring del repositorio de jornadas al conciliador |
| `services/partes-front/infrastructure/database/parte_repository.py` | `get_jornadas_empleado(dni)` (+ `list/upsert/cerrar` si D5) |
| `services/partes-front/interface_adapters/web/app.py` | §6.5 (+ rutas admin si D5) |
| `services/partes-front/templates/trabajador_detail.html` | KPI con patrón (R22) |
| `services/partes-front/static/app.js` | solo si «+ Nuevo» usa `jornada_dia` (R23) o hay UI admin |
| `docs/ARCHITECTURE.md` | semántica 3 («exceso sobre la jornada DEL DÍA…») y 7 (cuatro tablas) |
| `docs/referencia/partes-proyecto.md` | §4.3 (cómputo) y §5 (tabla nueva) |
| `azure-apps/partes.md` | schema de la BBDD `partes` (tabla nueva) |
| `services/*/.env.example` | variables nuevas |

### NO se tocan

`services/partes-email/`, `services/partes-api/`, `services/partes-transfer/`
(el payload hacia sv5 y lo que sv5 escribe en Sigrid NO cambian);
`parte_registros` y `parte_documents` (ni una columna); los clientes
`infrastructure/sigrid/` y `infrastructure/sesame/` (sin SQL nuevo contra
Sigrid: el candef ya llega por `_SQL_RESHOR`); `_es_no_laborable`,
`revert_extras_auto`, `apply_extras_splits`; `jornada_efectiva` y
`candef_valido` (firma y semántica intactas); `infra/` (sin variables
secretas nuevas: los defaults valen).

## 8. SQL / schema (para F-014)

No hay ficheros `NN_nombre.sql` en este proyecto: el schema vive en
`orm_models.py` (duplicado sv3/sv4) y sv4 lo crea con
`Base.metadata.create_all` + `ALTER TABLE … ADD COLUMN IF NOT EXISTS` al
arrancar. La tabla nueva sigue ese camino (una clase ORM nueva en ambas
copias; `create_all` la crea; no hace falta ALTER).

Tabla `empleado_jornada` (nombre en la familia de `empleado_alias`):

| columna | tipo | notas |
|---|---|---|
| `id` | Integer PK autoincrement | |
| `dni_norm` | String(32) NOT NULL, index | DNI normalizado (misma función que `empleado_alias`) |
| `jornada_semanal` | Float NOT NULL | p. ej. 40, 42, 48, 35 |
| `h_lun` … `h_dom` | Float NULL (7 columnas) | patrón explícito; NULL = derivar de candef y `jornada_semanal` |
| `desde` | String(16) NOT NULL | ISO `YYYY-MM-DD` (mismo criterio que `parte_registros.fecha`) |
| `hasta` | String(16) NULL | ISO, exclusivo; NULL = abierta |
| `origen` | String(16) NOT NULL default `manual` | `manual` / `sigrid` / `sesame` (futuro) |
| `nota` | String(255) NULL | «cuadrilla 9×4+6 desde mayo 2026» |
| `is_active` | Boolean NOT NULL default true | papelera lógica (regla 8 de ARCHITECTURE) |
| `created_at_utc`, `created_by`, `updated_at_utc`, `updated_by` | String(64/255) | trazabilidad, como el resto de tablas |

Restricción de negocio (validada en aplicación, R24): sin solapes de
vigencia por `dni_norm`; horas 0–24. Semilla inicial: la hace el humano
(MANUAL) con las 7 filas de la cuadrilla H5 si D3 lo confirma; el resto
cae al defecto.

## 9. Decisiones abiertas para el humano

- **D1 · Fuente de la jornada semanal.** Recomendada **S1** (tabla
  `empleado_jornada` en `partes`, §5). Alternativa: pedir a RRHH que
  mantenga `auxtur`/`emphis.turide` en Sigrid (S2) y leerlo desde aquí;
  compatible con S1 vía `origen=sigrid` más adelante.
- **D2 · Regla del viernes.** Recomendada: viernes = `S − 4 × candef
  efectivo`, valor FIJO del patrón (no absorbe festivos ni ausencias,
  §6.2). Confirmar que en semana con festivo el viernes sigue siendo 4 h
  (c=9, S=40) y no «lo que falte».
- **D3 · La cuadrilla de 7 (H5): ¿42 h de jornada o 40 h + 2 extras?** Y
  antes, ¿48 h eran jornada? Determina si se les da fila con
  `jornada_semanal=42` (extras 0, como registran los humanos) o se les
  deja al defecto (+2 h/semana de extra automática). Es negocio, no
  técnica. Recomendación técnica: sembrar lo que reproduce la práctica
  registrada (42 desde 2026-05-01, 48 antes) y que Administración lo
  corrija si no es así.
- **D4 · ¿Se corrige el candef en Sigrid?** La cuadrilla tiene candef 8 y
  hace 9 L–J. Con patrón explícito en la tabla no hace falta tocar Sigrid;
  con patrón derivado sí (candef 9). Recomendación: patrón EXPLÍCITO para
  ellos (9,9,9,9,6) y no depender de RRHH; y avisar de que `MO/0037` no
  tiene DNI en `emp` (H2).
- **D5 · Mantenimiento de la tabla.** (a) UI de administración en el
  portal (R24) dentro de F-014; (b) UI en una F-015 posterior y mientras
  tanto SQL manual del humano; (c) solo SQL manual. Recomendación: **(b)**
  — que F-014 entregue la regla y la lectura con tests, y la UI llegue con
  su propia spec.
- **D6 · Orden respecto a F-010.** Recomendación: F-010 (resincronizar
  `orm_models.py`) ANTES de F-014, para no añadir una clase idéntica sobre
  dos ficheros que ya difieren en `parte_registros`. Si el humano prefiere
  no esperar, F-014 añade la clase en ambas copias y F-010 sigue igual.
- **D7 · Recomputación de líneas ya registradas (riesgo §10.5).**
  ¿Debe F-014 excluir de `revert_extras_auto`/splits las líneas con
  `sigrid_estado` en {encolado, registrado} (y las de documentos
  `approved`), en coherencia con F-004? Recomendación: sí, en F-014 o en
  una feature de saneamiento propia; con la jornada por día el problema
  deja de ser teórico (cambiar una fila de la tabla re-splitea el pasado).
- **D8 · Rigor y reparto.** F-012 no lleva código: se recomienda cerrarla
  con rigor `documental` (CHECKPOINTS lo prevé). F-014 `estandar`; F-015
  (UI) `estandar`; F-011 debería replantearse sobre `empleado_jornada` +
  `emphis.porjorlab` (H6/H7).

## 10. Riesgos y alternativas descartadas

1. **Modelo acumulativo semanal (descartado).** «Sumar la semana y volcar
   la diferencia contra S en el último día trabajado». Descartado porque:
   (a) el pipeline procesa por parte, y la semana puede llegar en dos
   partes (o dos meses: el parte mensual de Sigrid corta la semana);
   (b) exige recomputar el viernes cuando llegan días anteriores, lo que
   choca con la congelación de F-004 (líneas ya registradas en Sigrid);
   (c) el neto semanal del modelo diario con extras negativas YA coincide
   con el acumulativo en semanas completas (H3 lo demuestra en el
   histórico humano); (d) los avisos de sv4 se vuelven inexplicables
   («¿por qué mi jueves está incompleto?»). El patrón fijo por día da el
   mismo neto y es local al día.
2. **Columna `jornada_semanal` en `parte_registros` (descartada).**
   Congela un dato editable, toca la tabla grande en dos copias y no
   sirve para días sin registros (avisos, «+ Nuevo»). Igual que D3 de
   F-003.
3. **Variable de entorno por trabajador (descartada).** Secretos no son,
   pero son datos por persona en manifiestos versionados; y sin
   vigencias.
4. **Regresión silenciosa.** La regla nueva debe ser bit a bit igual con
   (candef 8, S 40). Mitigación: R11 exige que los casos dorados de F-003
   pasen sin tocar y el guardián de gemelos (R14).
5. **Recomputación total de sv3 sobre líneas registradas (preexistente,
   agravado).** Hoy `revert_extras_auto` no excluye nada; una fila nueva en
   `empleado_jornada` con vigencia pasada re-splitearía en `partes` líneas
   ya escritas en Sigrid (que no cambian allí: divergencia). Ver D7.
6. **Sin DNI no hay particularización.** `MO/0037` (el único candef 9)
   no tiene DNI en `emp`: hasta que Sigrid lo tenga, caerá al patrón
   derivado (9,9,9,9,4 con S=40), que quizá no sea el suyo. Aviso, no
   bloqueo.
7. **La tabla es otra verdad que mantener.** Mitigación: `origen`,
   `nota`, trazabilidad de quién/cuándo, y KPI del portal que enseña
   siempre el patrón aplicado y si es particularizado (R22): lo que se ve
   se corrige.

## Anexo A · SQL reproducible (solo lectura, `POST /api/sql/read`, base `ruesma`)

Distribución de candef (hora por defecto, recursos vivos):

```sql
SELECT reshor.candef, COUNT(*) AS n
FROM reshor JOIN res ON res.ide = reshor.reside JOIN con ON con.ide = res.ide
WHERE reshor.horide = res.horide AND (con.fecbaj IS NULL OR con.fecbaj = 0)
GROUP BY reshor.candef ORDER BY n DESC
```

Recursos con candef 9 (sin traer nombres al repo):

```sql
SELECT res.ide, con.cod, auxrestip.res AS restip,
       CASE WHEN emp.dni IS NULL THEN 'sin' ELSE 'si' END AS tiene_dni,
       (SELECT COUNT(*) FROM reshor r2 JOIN auxhor a2 ON a2.ide = r2.horide
         WHERE r2.reside = res.ide AND a2.cod LIKE 'HE%') AS n_he
FROM reshor JOIN res ON res.ide = reshor.reside JOIN con ON con.ide = res.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN emp ON emp.ide = res.conide
WHERE reshor.horide = res.horide AND reshor.candef = 9
  AND (con.fecbaj IS NULL OR con.fecbaj = 0)
```

Base de los patrones (`d2`: recurso × día con ordinarias `HL%`, extras
`HE%`, día de semana 1 = lunes, candef del recurso):

```sql
WITH d AS (
  SELECT h.reside, h.fec,
         SUM(CASE WHEN a.cod LIKE 'HL%' THEN h.can ELSE 0 END) AS ord,
         SUM(CASE WHEN a.cod LIKE 'HE%' THEN h.can ELSE 0 END) AS ext
  FROM hmores h JOIN auxhor a ON a.ide = h.horide
  WHERE h.fec >= 20250101 AND h.fec < 20260901
    AND (a.cod LIKE 'HL%' OR a.cod LIKE 'HE%')
  GROUP BY h.reside, h.fec),
d2 AS (
  SELECT reside, fec, ord, ext,
         ((DATEPART(dw, CONVERT(date, CONVERT(varchar(8), fec))) + @@DATEFIRST - 2) % 7) + 1 AS dow,
         (SELECT r.candef FROM reshor r JOIN res ON res.ide = r.reside
           WHERE r.reside = d.reside AND r.horide = res.horide) AS candef
  FROM d)
-- H3: pares (ord, ext) en viernes
SELECT ord, ext, COUNT(*) AS dias FROM d2
WHERE dow = 5 AND ord > 0 GROUP BY ord, ext ORDER BY dias DESC
```

Semanas completas (H4) y grupo > 40 h (H5):

```sql
-- sobre d2:
, s AS (
  SELECT reside, candef,
         DATEPART(isowk, CONVERT(date, CONVERT(varchar(8), fec))) AS wk,
         YEAR(CONVERT(date, CONVERT(varchar(8), fec))) AS yr,
         COUNT(*) AS dias, SUM(ord) AS ord, SUM(ext) AS ext
  FROM d2 WHERE ord > 0 AND dow <= 5
  GROUP BY reside, candef, DATEPART(isowk, ...), YEAR(...)
  HAVING COUNT(*) = 5)
SELECT candef, ord AS ord_semana, COUNT(*) AS semanas, COUNT(DISTINCT reside) AS recursos
FROM s GROUP BY candef, ord ORDER BY candef, semanas DESC;
-- recursos con semanas > 40:
SELECT reside, COUNT(*) AS semanas5d, SUM(CASE WHEN ord > 40 THEN 1 ELSE 0 END) AS sem_mas40
FROM s GROUP BY reside HAVING SUM(CASE WHEN ord > 40 THEN 1 ELSE 0 END) > 0
ORDER BY sem_mas40 DESC
```

Patrón por mes y día de semana del grupo H5 (`reside IN (…)`) y del
recurso `MO/0037`: misma CTE `d`, `GROUP BY fec/100, dow, ord`.

Campos de jornada en Sigrid (H7):

```sql
SELECT COUNT(*) AS n,
       SUM(CASE WHEN numhor <> 0 THEN 1 ELSE 0 END) AS con_numhor,
       SUM(CASE WHEN porjorlab <> 0 THEN 1 ELSE 0 END) AS con_porjorlab,
       SUM(CASE WHEN turide <> 0 THEN 1 ELSE 0 END) AS con_turide,
       SUM(CASE WHEN rjgl <> 0 THEN 1 ELSE 0 END) AS con_rjgl
FROM emphis;
SELECT numhor, porjorlab, COUNT(*) FROM emphis GROUP BY numhor, porjorlab;
SELECT ide, cod, res, horlun, hormar, hormie, horjue, horvie, horsab, hordom FROM auxtur;
SELECT COUNT(*) FROM resjor; SELECT COUNT(*) FROM caljor; SELECT COUNT(*) FROM e_jor;
SELECT COUNT(*) FROM auxjla; SELECT * FROM calcab; SELECT COUNT(*) FROM caltur;
```

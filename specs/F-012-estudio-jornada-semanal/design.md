<!-- specs/F-012-estudio-jornada-semanal/design.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Diseño técnico

> Este documento ES el entregable de F-012: estudio con datos reales
> (§3), análisis de la regla decidida (§4), fuentes (§5), modelo (§6),
> ficheros de la implementación (§7–§8), decisiones tomadas por el humano
> —ninguna queda abierta— (§9) y riesgos (§10). F-012 no cambia código.
>
> **Versión 2 (2026-08-18).** La primera versión proponía derivar la
> jornada semanal de una tabla por trabajador y aplicar el «resto» al
> viernes. El humano la revisó y decidió: **la jornada semanal se deriva
> del candef** (mapa configurable `{8: 40, 9: 42}`, Sigrid es la fuente y
> se corrige allí — F-014); **el «resto» va al último día laborable de la
> semana** según el calendario del trabajador, contando los festivos como
> jornada; y **las excepciones** (jornada distinta de la derivada) van a
> una tabla `empleado_jornada` que se espera vacía mucho tiempo, con
> pantalla de administración en una feature posterior. Reparto:
> **F-014** (candef en Sigrid, documental, prerrequisito) → **F-015**
> (regla en sv3 + sv4) → **F-016** (UI de excepciones).

## 1. Servicios que toca y por qué (regla LÍMITE DE SERVICIO)

**F-012 (este estudio): ninguno.** Solo `specs/F-012-estudio-jornada-semanal/`.
Las consultas del §3 se hicieron en modo SOLO LECTURA (`sigrid-api`
`POST /api/sql/read` sobre `ruesma`; `SELECT` sobre la BBDD `partes` de
desarrollo) desde un script de usar y tirar fuera del repositorio; el SQL
va en el anexo A para que cualquiera lo reproduzca.

**F-014 (prerrequisito, documental): ningún servicio.** Es un cambio de
datos maestros en Sigrid que hace RRHH/Administración a mano; los agentes
no escriben en Sigrid fuera de sv5. Entrega la petición redactada y la
comprobación posterior por sigrid-api en solo lectura (SQL del anexo A).

**F-015 (implementación de la regla)** tocaría, y por esto:

- **sv3 `partes-persistencia`**: aquí vive el cómputo de extras por exceso
  de jornada (`RecursoConciliador._reclasificar_extras_jornada`). La
  jornada del día deja de ser «candef plano» y pasa a depender de la
  jornada semanal derivada del candef, del calendario del trabajador
  (último laborable) y, excepcionalmente, de `empleado_jornada`. Ya tiene
  el calendario por DNI (`CalendarioLaboralPort`, F-003): solo hay que
  preguntarle por los otros días de la semana.
- **sv4 `partes-front`**: aquí viven los avisos de «jornada incompleta»
  (vista trabajador y matriz de obra), el KPI de jornada y la
  `jornada_sugerida` de «+ Nuevo». Los tres consumen `jornada_efectiva`,
  el resolutor que F-003 dejó como único punto de entrada precisamente
  para esto. Ya tiene el calendario por DNI (`CalendarioProvider`).
- **La regla se escribe DOS veces (resolutor gemelo)**, como ya ocurre con
  `jornada_resolver.py` desde F-003 y como manda `docs/ARCHITECTURE.md`
  (sin librería compartida). El guardián que compara ambas copias se
  amplía (R19). NO se propone un «servicio de jornadas»: sería un salto de
  red en cada persistencia y en cada vista para una función pura.
- **El mapa candef → jornada semanal es configuración**, no datos por
  persona: variable de entorno espejo en sv3 y sv4 (misma cadena en los
  dos, D9 en §9) con valor por defecto en código `8:40,9:42`; candef válido
  fuera del mapa ⇒ jornada plana 5×candef + WARNING (D10).
- **La tabla `empleado_jornada` entra en las DOS copias de
  `orm_models.py`** (duplicación tolerada del CLAUDE.md, trampa 3 de C3).
  Las copias ya están desincronizadas (F-010): recomendado hacer F-010
  antes (D6).
- **sv1, sv2 y sv5 NO se tocan.** sv5 recibe líneas ya desglosadas y no
  sabe de jornadas. `sigrid-api` tampoco (el candef ya llega por
  `_SQL_RESHOR`).
- **Sigrid NO se escribe desde aquí**: F-014 es una petición a RRHH.

## 2. Cómo funciona hoy (lo que el estudio pone en cuestión)

- **Jornada teórica = `reshor.candef` de la hora por defecto del recurso**
  (`res.horide`), y 8 h si el candef no es válido (≤ 2). Regla única en
  `jornada_efectiva(candef, minimo, por_defecto)` (F-003, R11/R12), con
  copias gemelas en sv3 y sv4. La jornada es **la misma todos los días
  laborables**: no distingue el último día ni sabe de semanas.
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
  desde cero. No excluye líneas ya registradas en Sigrid (riesgo §10.5,
  decisión D7).

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
  corregir en Sigrid → **F-014** lo incluye.

### H3 · Cómo se registran hoy los viernes (histórico `hmores`, candef 8)

Pares (ordinaria, extra) más frecuentes en **viernes** de recursos con
candef 8 (3.498 viernes con ordinarias). Medición del 2026-08-18 (sesión
de redacción, mañana):

| ord | extra | días | lectura |
|---|---|---|---|
| 8 | 0 | 836 | viernes de 8 h |
| 8 | **−2** | 810 | viernes de 6 h registrado como 8 − 2 |
| 8 | +1 | 678 | |
| 8 | **−3** | 328 | viernes de 5 h como 8 − 3 |
| 7 | 0 | 247 | intensiva (H6) |
| 8 | +2 | 234 | |
| 8 | −1 | 157 | |

*Nota de reproducibilidad*: las frecuencias fila a fila se mueven con las
ediciones diarias de Administración sobre los partes en curso (el reviewer
midió el mismo 2026-08-18, por la tarde, 803/764/648/326/241/230/154 para
las mismas siete filas, con el total de 3.498 idéntico y las mismas
conclusiones). Lo estable es el orden y las proporciones, no la última
unidad.

Suma neta de extras en viernes: **−1.101 h** (negativa); en L–J es
positiva (+4.600…+5.000 h por día de semana). Es decir: **la práctica
humana en Sigrid ya usa el modelo «jornada diaria + extra negativa el
viernes»**, exactamente lo que sv3 automatiza. No aparece NINGÚN viernes
de 4 h (n=0 de 3.498) ni de 9 h (n=1). El patrón «9+9+9+9+4» que
enunciaba la petición **no existe en el histórico**.

### H4 · Semanas completas (5 días laborables con horas): horas ordinarias

La tabla se limita a los recursos con **candef 8 y 9** (los que cobran por
horas y tienen jornada informada). Fuera de ella quedan 91 semanas de 40 h
en 3 recursos con candef 0 y 10 semanas de 40 h en 2 recursos con candef 1
(más 10 de 35 h, 1 de 38 y 1 de 39 con candef 0), que no cambian nada.

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
  no registradas? **Resuelto por el humano (2026-08-18)**: su jornada es
  42 h y se deriva del candef 9 (mapa `9: 42`) → **F-014** les pone
  candef 9 en Sigrid; no se siembra ninguna excepción.
- Su viernes NO es «el resto hasta 40» (sería 4): es 6. Solo con una
  jornada semanal de **42** la regla «último laborable = resto»
  reproduce lo que hacen: de ahí el mapa `{8: 40, 9: 42}`.
- El régimen cambia con el tiempo (48 → 42 → 35): por eso las
  excepciones de la tabla `empleado_jornada` llevan **vigencia**
  (desde/hasta), aunque hoy no haga falta sembrar ninguna.

### H6 · Hallazgo colateral: jornada intensiva de verano (7 × 5 = 35 h)

Julio-agosto 2025: 667/543 días de 7 h frente a 283/251 de 8 h; julio
2026: 754 frente a 311; agosto 2026 (parcial): 388 frente a 34. Los
humanos registran **7 ordinarias y 0 extra**; sv3 hoy registraría **8
ordinarias y −1 extra** cada día. No es objeto de F-012 (es F-011,
«jornada reducida por días»), pero la tabla de excepciones del §6 lo
cubre con un patrón explícito con vigencia (7×5) o, mejor, con una fuente
de RRHH que la alimente. Se anota para que F-011 se replantee sobre
`empleado_jornada` + `emphis.porjorlab` (H7) y no reinvente otra tabla.

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

## 4. Análisis: la regla decidida y sus casos

**Regla (decisión del humano, 2026-08-18).** Para un trabajador con
candef efectivo c y jornada semanal S = mapa[c] (y S = 5c + WARNING si c
es válido pero no está en el mapa), en una semana L–D:

- día no laborable (finde o festivo de SU calendario) → jornada 0
  (todo lo ordinario a extra, como hoy);
- día laborable que NO es el último laborable L–V de la semana → c;
- **último día laborable L–V de la semana → `max(0, S − 4c)`**. Los
  festivos L–V CUENTAN como jornada c a efectos del resto (lectura A):
  el último laborable recibe siempre `S − 4c`, haya o no festivos.
- Sábado y domingo nunca son candidatos; una semana sin laborables L–V
  no reparte resto.
- «Último laborable» se decide SOLO con el calendario, nunca con lo que
  haya registrado: ausencias, incidencias y días sin parte no lo mueven
  ni absorben horas.

Con (c 8, S 40) el último laborable recibe 40 − 32 = 8: **idéntico a
hoy** en toda semana, con o sin festivos.

| caso | c / S | horas trabajadas L–V | hoy (candef plano) | con la regla | comentario |
|---|---|---|---|---|---|
| A. cuadrilla H5, régimen 42 (tras F-014) | 9 / 42 | 9,9,9,9,6 | (c 8 hoy) +1×4, V −2 → **+2/sem**; (c 9) V 9/−3 → −3 | V jornada 6 → **0** | reproduce la práctica humana |
| A'. ídem, viernes de 9 h | 9 / 42 | 9,9,9,9,9 | (c 9) 0 extras (45 h sin extra) | V ord 6 + **3 extra** | hoy se PIERDEN extras |
| A''. ídem, viernes de 4 h | 9 / 42 | 9,9,9,9,4 | (c 9) V 9/−5 | V ord 6, extra **−2**; aviso «incompleto» el viernes (correcto) | |
| B. viernes festivo | 9 / 42 | 9,9,9,6,— | (c 9) J 9/−3 | **jueves** es último laborable → jornada 6 → 0 extra | el humano lo fijó así |
| B'. viernes festivo TRABAJADO 5 h | 9 / 42 | 9,9,9,6,5 | V todo a extra (5) | igual: V no laborable → 5 extra; J 6 → 0 | la regla no convierte festivos en laborables |
| C. miércoles festivo | 9 / 42 | 9,9,—,9,6 | X: 0; V −3 | X 0; **V** último laborable → 6 → 0 | el festivo cuenta como 9 |
| D. jueves y viernes festivos | 9 / 42 | 9,9,6,—,— | X 9/−3 | **X** último laborable → 6 → 0 | |
| E. solo lunes laborable | 9 / 42 | 6,—,—,—,— | L 9/−3 | L es último laborable → 6 → 0 | consecuencia de la lectura A |
| F. semana entera festiva | 9 / 42 | — | todo a extra si se trabaja | igual (nadie recibe resto) | |
| G. semana partida (X 30/06 · J 01/07) | 9 / 42 | 9,9,9,9,6 en dos partes | día a día | día a día: el viernes 03/07 sabe que es último laborable por calendario, esté o no el parte de junio | local al día |
| H. parte que solo trae L–M | 9 / 42 | 9,9 | 0 | 0 (L y M no son últimos) | el resto se calcula cuando llegue el viernes |
| I. ausencia el viernes (V) | 9 / 42 | 9,9,9,9,(V) | — | V sigue siendo el último laborable: jornada 6; sin ordinarias no se normaliza; **jueves NO absorbe** | R15 |
| J. sábado trabajado 6 h | 9 / 42 | + S 6 | 6 extra | 6 extra | sin cambio |
| K. c 8, S 40, festivo cualquiera | 8 / 40 | 8,8,8,8 | 8 | 8 (40 − 32) | **regresión cero** |
| L. c 9 sin corregir en Sigrid (S 40 por mapa) | 9 / 40 | 9,9,9,9,6 | V 9/−3 | V jornada 4 → ord 4 + 2 extra | por eso F-014 va ANTES |
| M. c válido fuera del mapa (10) | 10 / 50 (5c) | 10,10,10,10,8 | (c 10) V 10/−2 | igual que hoy: V jornada 10 → −2; **WARNING** «candef 10 sin entrada en el mapa» | decisión D10: jornada plana hasta que se añada al mapa o se corrija en Sigrid |
| N. intensiva 7×5 (fuera de F-012) | 8 / 40 | 7,7,7,7,7 | 8/−1 cada día | igual (F-011 sobre `empleado_jornada` + `emphis.porjorlab`) | H6/H7 |
| O. recurso sin HE (MENC) | — | — | no se normaliza | no se normaliza | sin cambio |
| P. candef inválido (0/1) | 8 (asignado) / 40 | 8,8,8,8,8 | 0 | 0 | sin cambio |
| Q. excepción en tabla: S 48 | 10 / 48 | 10,10,10,10,8 | — | V 8 → 0 | R16 |
| R. excepción en tabla: patrón 7×5 vigente | — | 7,7,7,7,7 | 8/−1 | 7 cada día → 0; festivo → 0 | R16 |

Lecturas: (1) la regla es **local al día** dado el calendario: no exige
ver la semana entera ni los registros de otros días → compatible con el
parte mensual, la llegada por partes y la congelación de F-004; (2) el
neto semanal coincide con el modelo acumulativo en semanas completas
(H3 lo muestra en el histórico humano), pero corrige los casos donde el
modelo diario plano pierde extras (A') o inventa negativas (A, B, C, D);
(3) los avisos de sv4 dejan de marcar el último día corto y pasan a marcar
solo lo realmente incompleto (A'').

## 5. Fuentes de la jornada semanal: inventario y decisión

| fuente | ¿datos hoy? | quién la mantiene | decisión |
|---|---|---|---|
| **`reshor.candef` de Sigrid + mapa candef → S** | sí para ~107 recursos (H1); F-014 corrige la cuadrilla | RRHH/Administración en Sigrid (dato maestro que ya mantienen) | **ELEGIDA (humano, 2026-08-18)**: una sola verdad, la que ya se usa; el mapa es configuración, no datos por persona |
| Sigrid `auxtur` + `emphis.turide` (patrón por día de semana) | estructura sí, datos **no** (H7) | RRHH en Sigrid | descartada como fuente hoy; posible `origen=sigrid` de una excepción futura (R18) |
| Sigrid `emphis.numhor` / `porjorlab` | `porjorlab` sí (87,5 / 75 / 50 %) | RRHH | no es jornada semanal; **sí sirve a F-011** (reducida) |
| Sesame (contrato / horarios) | **no**: 0/218 contratos (F-013); P1 pendiente | RRHH en Sesame | descartada hoy; posible `origen=sesame` futuro |
| **Tabla `empleado_jornada` en `partes`** | no; se crea vacía | Administración desde el portal (F-016); mientras, SQL manual | **ELEGIDA SOLO PARA EXCEPCIONES** (jornada ≠ derivada): S distinta y/o patrón explícito con vigencia. Se espera vacía mucho tiempo |
| Fichero de parametrización por código `MO/NNNN` | — | git | descartada (datos por persona en git; redeploy por cambio) |

## 6. Modelo (para F-015)

### 6.1 Resolución para (recurso, DNI, fecha d)

1. `c = jornada_efectiva(candef, minimo, por_defecto)` (sin cambios).
2. Excepción: fila vigente de `empleado_jornada` para el DNI normalizado
   (`desde ≤ d < hasta`), leída por el repositorio propio de cada
   servicio con caché TTL; tabla vacía o sin fila → sin excepción; fallo
   de lectura → WARNING y sin excepción (R17).
   - con patrón explícito → `jornada = patron[weekday(d)]` si d es
     laborable, 0 si no; FIN.
   - con solo `jornada_semanal` → `S = fila.jornada_semanal`.
3. Sin excepción de S: `S = mapa.get(c, 5 * c)`; si c no estaba en el mapa,
   WARNING (R10).
4. Regla del último laborable (R13–R15) con el calendario del trabajador:
   `es_laborable(x)` para x en los días L–V de la semana de d.
   - d no laborable → 0;
   - d laborable y existe x > d (L–V) laborable → c;
   - d laborable y ningún x > d laborable → `max(0, S − 4c)`.

Cinco consultas al calendario como mucho por día (los L–V de su semana),
todas cacheadas por (DNI × año) en ambos servicios (F-003, D5): coste
despreciable.

### 6.2 Firma del resolutor (gemelo sv3/sv4)

```python
# application/services/jornada_resolver.py (ambas copias)
def parsear_mapa_semanal(texto: str) -> dict[float, float]:
    """'8:40,9:42' -> {8.0: 40.0, 9.0: 42.0}; ValueError si está mal formado."""

def jornada_semanal_de(candef_efectivo: float, *, mapa: Mapping[float, float],
                       por_defecto: float) -> float: ...

def es_ultimo_laborable(d: date, es_laborable: Callable[[date], bool]) -> bool:
    """d es L–V, laborable, y ningún día posterior L–V de su semana lo es."""

@dataclass(frozen=True)
class Excepcion:
    semanal: float | None
    patron: tuple[float, ...] | None  # 7 valores L..D o None
    origen: str

def jornada_dia(d: date, *, candef: float | str | None, minimo: float,
                por_defecto: float, mapa: Mapping[float, float],
                es_laborable: Callable[[date], bool],
                excepcion: Excepcion | None = None) -> float: ...
```

`jornada_efectiva` y `candef_valido` **no cambian**. El resolutor es
puro: no sabe de BBDD ni de Sesame; recibe el calendario ya ligado al DNI
(sv3: `lambda x: not calendario.es_no_laborable(x.isoformat(), dni=dni)`;
sv4: `lambda x: calendario_provider.dia(x, dni).laborable`).

### 6.3 sv3 — cómputo

- `RecursoConciliador.__init__` gana `mapa_semanal: Mapping[float, float]`,
  `jornada_semanal_horas: float = 40.0` y `jornadas: JornadaEmpleadoPort |
  None = None` (excepciones; caché TTL como `_reshor_cache`).
- En `_reclasificar_extras_jornada`, `candef_efectivo = jornada_efectiva(...)`
  pasa a `jornada_del_dia = jornada_dia(fecha, candef=candef_real, …,
  es_laborable=<ligado al DNI del grupo>, excepcion=<fila o None>)`;
  `objetivo_extra = total − jornada_del_dia`. La rama «no laborable» del
  algoritmo se conserva tal cual (sigue delante). Nada más cambia.
- La señal de degradación del calendario (F-003 R26) se recoge también en
  las consultas de «último laborable» (R23): mismo `_recoger_degradacion`.
- Sin calendario cableado (`calendario=None`, tests antiguos): todo día es
  laborable y el último laborable es el viernes (D11).

### 6.4 sv4 — avisos, KPI y «+ Nuevo»

- `trabajador_detail`: `candef_efectivo` → `jornada_dia(...)` por día del
  calendario; el KPI muestra c, S (y si viene de excepción) y la jornada
  del último laborable (R25).
- `obra_detail`: `_eff` por fila y día → `jornada_dia(...)` con el DNI de la
  fila (`ObraMatrixRow.dni`, F-003) (R24).
- `_sugerida` / `GET /api/sigrid/empleados`: `jornada_dia` opcional cuando
  llega `fecha` (R26).
- `JornadaEmpleadoProvider` (application): lectura de excepciones con caché
  TTL y fallback silencioso; inyectable en `build_app` para tests.
- (F-016) rutas `/admin/jornadas` + plantilla + validaciones (R27).

## 7. Ficheros (para F-015; F-012 no crea ninguno fuera de `specs/`)

### Crear

| Fichero | Contenido |
|---|---|
| `services/partes-persistencia/domain/ports/jornada_empleado.py` | `JornadaEmpleadoRow` (dni_norm, semanal, patrón 7 valores o None, desde, hasta, origen) y puerto `JornadaEmpleadoPort.fetch_jornadas() -> list[JornadaEmpleadoRow]` |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | implementación sobre `EmpleadoJornadaOrm` |
| `services/partes-persistencia/tests/test_f015_r*.py` | tests R10–R23, R28 (sin red ni BBDD: SQLite en memoria / dobles / calendario fake) |
| `services/partes-front/application/services/jornada_provider.py` | `JornadaEmpleadoProvider(repository, ttl_seconds)` → `excepcion_para(dni, fecha)` |
| `services/partes-front/tests/test_f015_r*.py` | tests R10–R19, R24–R26 (TestClient + SQLite + doble de calendario) |

### Modificar

| Fichero | Cambio |
|---|---|
| `services/partes-persistencia/application/services/jornada_resolver.py` | §6.2 |
| `services/partes-front/application/services/jornada_resolver.py` | gemelo, idéntico |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` (§8) |
| `services/partes-front/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` idéntico; `create_all` de sv4 la crea al arrancar |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | §6.3 (+ D7: excluir registrado/encolado/approved del re-split) |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | D7: `revert_extras_auto` / `fetch_registros_para_recurso` excluyen líneas congeladas |
| `services/partes-persistencia/config/settings.py` y `services/partes-front/config/settings.py` | `JORNADA_SEMANAL_POR_CANDEF` (`8:40,9:42`; variable espejo, misma cadena en ambos), `JORNADA_CACHE_TTL_S`; validación fail-fast del mapa |
| `services/partes-persistencia/interface_adapters/api/app.py` | wiring (mapa + repositorio de excepciones al conciliador) |
| `services/partes-front/infrastructure/database/parte_repository.py` | `get_jornadas_empleado(dni)` |
| `services/partes-front/interface_adapters/web/app.py` | §6.4 |
| `services/partes-front/templates/trabajador_detail.html` | KPI (R25) |
| `services/partes-front/static/app.js` | solo si «+ Nuevo» usa `jornada_dia` (R26) |
| `infra/manifests/sv3/`, `infra/manifests/sv4/` (o scripts de despliegue) | variable NO secreta `JORNADA_SEMANAL_POR_CANDEF` con el mismo valor en ambos (D9: variable espejo) |
| `docs/ARCHITECTURE.md` | semántica 3 («exceso sobre la jornada DEL DÍA: candef, salvo el último laborable de la semana, que recibe el resto de la jornada semanal derivada del candef…») y 7 (cuatro tablas) |
| `docs/referencia/partes-proyecto.md` | §4.3 (cómputo) y §5 (tabla nueva) |
| `azure-apps/partes.md` | schema de la BBDD `partes` (tabla nueva) y variables nuevas |
| `services/*/.env.example` | variables nuevas |

### NO se tocan

`services/partes-email/`, `services/partes-api/`, `services/partes-transfer/`
(el payload hacia sv5 y lo que sv5 escribe en Sigrid NO cambian);
`parte_registros` y `parte_documents` (ni una columna); los clientes
`infrastructure/sigrid/` y `infrastructure/sesame/` (sin SQL nuevo contra
Sigrid); `CalendarioLaboralPort` (firma) y `CalendarioProvider` (se
consumen, no se cambian); `_es_no_laborable`; `apply_extras_splits`;
`jornada_efectiva` y `candef_valido` (firma y semántica intactas).

## 8. SQL / schema (para F-015)

No hay ficheros `NN_nombre.sql` en este proyecto: el schema vive en
`orm_models.py` (duplicado sv3/sv4) y sv4 lo crea con
`Base.metadata.create_all` + `ALTER TABLE … ADD COLUMN IF NOT EXISTS` al
arrancar. La tabla nueva sigue ese camino (clase ORM nueva en ambas
copias; `create_all` la crea; no hace falta ALTER).

Tabla `empleado_jornada` (excepciones; nombre en la familia de
`empleado_alias`):

| columna | tipo | notas |
|---|---|---|
| `id` | Integer PK autoincrement | |
| `dni_norm` | String(32) NOT NULL, index | DNI normalizado (misma función que `empleado_alias`) |
| `jornada_semanal` | Float NULL | S de la excepción; NULL si solo hay patrón |
| `h_lun` … `h_dom` | Float NULL (7 columnas) | patrón explícito; NULL = usar S (regla del último laborable) |
| `desde` | String(16) NOT NULL | ISO `YYYY-MM-DD` (mismo criterio que `parte_registros.fecha`) |
| `hasta` | String(16) NULL | ISO, exclusivo; NULL = abierta |
| `origen` | String(16) NOT NULL default `manual` | `manual` / `sigrid` / `sesame` (futuro) |
| `nota` | String(255) NULL | |
| `is_active` | Boolean NOT NULL default true | papelera lógica (regla 8 de ARCHITECTURE) |
| `created_at_utc`, `created_by`, `updated_at_utc`, `updated_by` | String(64/255) | trazabilidad, como el resto de tablas |

Restricciones de negocio (validadas en aplicación, R27): al menos uno de
`jornada_semanal` / patrón; sin solapes de vigencia por `dni_norm`; horas
0–24. Sin semilla: la tabla nace y se queda vacía hasta que haya una
excepción real.

## 9. Decisiones

### 9.1 Tomadas por el humano (2026-08-18) — FIRMES

- **D1 · Fuente**: la jornada semanal se deriva del candef por el mapa
  `{8: 40, 9: 42}` (configurable); Sigrid es la fuente y se corrige allí.
  Sustituye a la propuesta de tabla-fuente. (Candef válido fuera del mapa:
  ver D10.)
- **D2 · Regla del resto**: el último día laborable L–V de la semana del
  trabajador (calendario F-003), con los festivos contando como jornada
  (lectura A). No «el viernes».
- **D3 / D4 · La cuadrilla H5 y `MO/0037`**: su jornada es 42 h y sale del
  candef 9 → **F-014** pone candef 9 a `MO/0006`, `MO/0007`, `MO/0008`,
  `MO/0031`, `MO/0366`, `MO/0405`, `MO/0456` y DNI en `emp` a `MO/0037`.
  No se siembra ninguna excepción. F-014 se cierra ANTES de implementar.
- **D5 · Excepciones**: tabla `empleado_jornada` (opción a) mantenida
  desde una pantalla de administración del portal en **F-016**; mientras,
  SQL manual. Resolutor preparado para `origen` sigrid/sesame.
- **D6 · Orden con F-010**: F-010 (resincronizar `orm_models.py`) antes de
  F-015 (recomendación mantenida).
- **D7 · Recomputación de líneas registradas**: sí — F-015 (o saneamiento
  propio) excluye de `revert_extras_auto`/splits las líneas con
  `sigrid_estado` en {encolado, registrado} y las de documentos
  `approved`, en coherencia con F-004.
- **D8 · Rigor y reparto**: F-012 `documental`; F-014 `documental`; F-015 y
  F-016 `estandar`; F-011 se replantea sobre `empleado_jornada` +
  `emphis.porjorlab`.

- **D9 · Dónde vive el mapa candef → S** (2026-08-18): variable de entorno
  `JORNADA_SEMANAL_POR_CANDEF` **espejo en sv3 y sv4** (misma cadena;
  default en código `8:40,9:42`; no es secreto: va en los manifiestos
  versionados). Descartada la tabla de configuración (schema y UI para dos
  filas). Riesgo: desincronizar sv3 y sv4; mitigación: documentarla como
  variable «espejo» y que el KPI de sv4 enseñe la S aplicada (R25).
- **D10 · Candef válido fuera del mapa (≠ 8/9, > 2)** (2026-08-18): **S =
  5 × candef (jornada plana = comportamiento actual) + WARNING
  obligatorio** en log (R10), para que quien lo vea añada la clave al mapa
  o corrija el candef en Sigrid. Hoy no existe ninguno (H1). Descartadas
  S = 40 fija (daría último laborable 0 h y 8 h de extra un viernes normal
  con candef 10) y el silencio.
- **D11 · Calendario sin cablear (sv3 con `calendario=None`)**
  (2026-08-18): sin calendario no hay regla de no laborable y «último
  laborable» = viernes. Los tests antiguos siguen valiendo; en producción
  el calendario está cableado desde F-003.

### 9.2 Abiertas

Ninguna: todas las decisiones del estudio están tomadas por el humano
(2026-08-18). Lo que quede por decidir en la implementación lo abrirá la
spec de F-015 en su propio `design.md`.

## 10. Riesgos y alternativas descartadas

1. **Modelo acumulativo semanal (descartado).** «Sumar la semana y volcar
   la diferencia contra S en el último día trabajado». (a) El pipeline
   procesa por parte y la semana puede llegar en dos partes o dos meses;
   (b) exigiría recomputar días anteriores, chocando con la congelación
   de F-004; (c) el neto semanal de la regla del último laborable ya
   coincide en semanas completas; (d) los avisos serían inexplicables. La
   regla decidida es local al día dado el calendario.
2. **«Resto = lo que falte de lo trabajado» (descartado, y así lo fijó el
   humano).** Absorbería festivos y ausencias (semana con festivo el
   lunes: viernes de 13 h). El festivo cuenta como jornada (lectura A).
3. **Columna `jornada` en `parte_registros` (descartada).** Congela un
   dato editable, toca la tabla grande en dos copias y no sirve para días
   sin registros. Igual que D3 de F-003.
4. **Regresión silenciosa.** La regla nueva debe ser bit a bit igual con
   (c 8, S 40), con o sin festivos. Mitigación: R11 exige que los casos
   dorados de F-003 pasen sin tocar y el guardián de gemelos (R19).
5. **Recomputación total de sv3 sobre líneas registradas (preexistente,
   agravado).** Con la regla nueva, corregir un candef en Sigrid (F-014) o
   añadir una excepción re-splitea en `partes` líneas ya escritas en Sigrid
   (que no cambian allí: divergencia). D7 lo cierra excluyéndolas.
6. **F-014 antes que F-015 (orden duro).** Si la regla se despliega con la
   cuadrilla aún a candef 8, su viernes de 6 h se marcará incompleto y se
   generará +2 h/semana de extra automática (caso L). Mitigación: F-014
   documental y verificable por SQL antes de mergear F-015.
7. **Calendario degradado decide el «último laborable».** Un festivo no
   visto (Sesame caído, respaldo) puede mover el resto de día. Mitigación:
   mismo régimen de F-003 (review_required en sv3, banner/bloqueo en sv4),
   R23; no se inventa un tercer régimen.
8. **Mapa desincronizado entre sv3 y sv4** (D9: env espejo). Mitigación:
   default idéntico en código, variable documentada como «espejo», KPI
   visible.
9. **`MO/0037` sin DNI** hasta que F-014 lo corrija: cae al calendario por
   defecto y sin excepción posible; con candef 9 → S 42 igual que la
   cuadrilla. Aviso, no bloqueo.

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

Semanas completas (H4), ejecutable tal cual:

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
  FROM d),
s AS (
  SELECT reside, candef,
         DATEPART(isowk, CONVERT(date, CONVERT(varchar(8), fec))) AS wk,
         YEAR(CONVERT(date, CONVERT(varchar(8), fec))) AS yr,
         COUNT(*) AS dias, SUM(ord) AS ord, SUM(ext) AS ext
  FROM d2 WHERE ord > 0 AND dow <= 5
  GROUP BY reside, candef,
           DATEPART(isowk, CONVERT(date, CONVERT(varchar(8), fec))),
           YEAR(CONVERT(date, CONVERT(varchar(8), fec)))
  HAVING COUNT(*) = 5)
SELECT candef, ord AS ord_semana, COUNT(*) AS semanas,
       COUNT(DISTINCT reside) AS recursos, ROUND(AVG(ext), 1) AS ext_media
FROM s GROUP BY candef, ord ORDER BY candef, semanas DESC
```

Recursos con semanas de más de 40 h (H5), ejecutable tal cual (misma
cabecera `WITH d AS (...), d2 AS (...)` que la consulta anterior):

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
         ((DATEPART(dw, CONVERT(date, CONVERT(varchar(8), fec))) + @@DATEFIRST - 2) % 7) + 1 AS dow
  FROM d),
s AS (
  SELECT reside,
         DATEPART(isowk, CONVERT(date, CONVERT(varchar(8), fec))) AS wk,
         YEAR(CONVERT(date, CONVERT(varchar(8), fec))) AS yr,
         COUNT(*) AS dias, SUM(ord) AS ord
  FROM d2 WHERE ord > 0 AND dow <= 5
  GROUP BY reside,
           DATEPART(isowk, CONVERT(date, CONVERT(varchar(8), fec))),
           YEAR(CONVERT(date, CONVERT(varchar(8), fec)))
  HAVING COUNT(*) = 5)
SELECT reside, COUNT(*) AS semanas5d,
       SUM(CASE WHEN ord > 40 THEN 1 ELSE 0 END) AS sem_mas40,
       SUM(CASE WHEN ord = 40 THEN 1 ELSE 0 END) AS sem_40,
       SUM(CASE WHEN ord < 40 THEN 1 ELSE 0 END) AS sem_menos40,
       MAX(ord) AS max_sem
FROM s GROUP BY reside
HAVING SUM(CASE WHEN ord > 40 THEN 1 ELSE 0 END) > 0
ORDER BY sem_mas40 DESC
```

Categoría, DNI (solo si existe) y códigos HE del grupo H5:

```sql
SELECT res.ide AS reside, con.cod AS cod, auxrestip.res AS restip,
       CASE WHEN emp.dni IS NULL THEN 'sin' ELSE 'si' END AS tiene_dni,
       (SELECT COUNT(*) FROM reshor r2 JOIN auxhor a2 ON a2.ide = r2.horide
         WHERE r2.reside = res.ide AND a2.cod LIKE 'HE%') AS n_he,
       (SELECT MAX(r3.candef) FROM reshor r3
         WHERE r3.reside = res.ide AND r3.horide = res.horide) AS candef
FROM res JOIN con ON con.ide = res.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN emp ON emp.ide = res.conide
WHERE res.ide IN (1555819, 2146402, 2146404, 1392590, 1336571, 2146403, 2714845)
```

Patrón por mes y día de semana del grupo H5 (tabla de H5; cambiar el
rango de fechas o el `IN` para `MO/0037`, `res.ide` 2798044):

```sql
WITH d AS (
  SELECT h.reside, h.fec,
         SUM(CASE WHEN a.cod LIKE 'HL%' THEN h.can ELSE 0 END) AS ord,
         SUM(CASE WHEN a.cod LIKE 'HE%' THEN h.can ELSE 0 END) AS ext
  FROM hmores h JOIN auxhor a ON a.ide = h.horide
  WHERE h.fec >= 20250101 AND h.fec < 20260901
    AND h.reside IN (1555819, 2146402, 2146404, 1392590, 1336571, 2146403, 2714845)
    AND (a.cod LIKE 'HL%' OR a.cod LIKE 'HE%')
  GROUP BY h.reside, h.fec)
SELECT fec / 100 AS anomes,
       ((DATEPART(dw, CONVERT(date, CONVERT(varchar(8), fec))) + @@DATEFIRST - 2) % 7) + 1 AS dow,
       ord, COUNT(*) AS dias, ROUND(SUM(ext), 0) AS ext_total
FROM d WHERE ord > 0
GROUP BY fec / 100,
         ((DATEPART(dw, CONVERT(date, CONVERT(varchar(8), fec))) + @@DATEFIRST - 2) % 7) + 1,
         ord
ORDER BY anomes, dow, dias DESC
```

Líneas registradas de `MO/0037` (H2):

```sql
SELECT h.fec, a.cod, h.can
FROM hmores h JOIN auxhor a ON a.ide = h.horide
WHERE h.reside = 2798044 AND h.fec >= 20250101
ORDER BY h.fec, a.cod
```

Jornada intensiva por mes (H6):

```sql
WITH d AS (
  SELECT h.reside, h.fec, SUM(h.can) AS ord
  FROM hmores h JOIN auxhor a ON a.ide = h.horide
  WHERE h.fec >= 20250101 AND h.fec < 20260901 AND a.cod LIKE 'HL%'
  GROUP BY h.reside, h.fec)
SELECT fec / 100 AS anomes,
       SUM(CASE WHEN ord = 8 THEN 1 ELSE 0 END) AS n8,
       SUM(CASE WHEN ord = 7 THEN 1 ELSE 0 END) AS n7,
       SUM(CASE WHEN ord = 9 THEN 1 ELSE 0 END) AS n9,
       SUM(CASE WHEN ord >= 10 THEN 1 ELSE 0 END) AS n10mas,
       COUNT(*) AS dias
FROM d WHERE ord > 0 GROUP BY fec / 100 ORDER BY fec / 100
```

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

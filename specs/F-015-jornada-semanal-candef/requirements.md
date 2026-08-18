<!-- specs/F-015-jornada-semanal-candef/requirements.md -->
# F-015 · Jornada del día por jornada semanal derivada del candef y último laborable — Requisitos (EARS)

> **De dónde sale esta spec.** El estudio **F-012**
> (`specs/F-012-estudio-jornada-semanal/`) hizo el análisis con datos reales y
> el humano aprobó sus decisiones **firmes** el 2026-08-18 (design §9.1,
> D1–D11). Este documento **hereda literalmente** los requisitos del bloque B
> de `specs/F-012-estudio-jornada-semanal/requirements.md` (R10–R28), los
> completa y les añade criterios de aceptación. **Se conserva la numeración
> original** para que la trazabilidad F-012 → F-015 → test sea directa y para
> que los nombres de test ya propuestos (`test_f015_rNN_…`) valgan tal cual.
> Los requisitos **R29–R35 son nuevos de F-015**: cubren lo que el estudio
> dejó como decisión de diseño (D7, guardián de F-010, variable espejo,
> documentación) y la puerta de entrega.
>
> **R27 NO se implementa aquí**: es la pantalla de administración, y es
> **F-016**. El número queda reservado para no romper la trazabilidad.

Servicios que toca: **sv3 `partes-persistencia`** (cómputo de extras) y
**sv4 `partes-front`** (avisos, KPI y «+ Nuevo»), más la suite de la **raíz
del monorepo** (guardianes de las copias gemelas). Justificación en
`design.md` §1. **sv1, sv2 y sv5 no se tocan.**

## Vocabulario (idéntico al de F-012, bloque B)

- **candef efectivo** (`c`): lo que ya devuelve `jornada_efectiva(candef,
  minimo, por_defecto)` — el candef de Sigrid si es válido (`> minimo`), si
  no la jornada por defecto (8). **No cambia de firma ni de semántica.**
- **jornada semanal** (`S`): horas ordinarias teóricas de la semana.
- **semana**: lunes a domingo. Los días candidatos a jornada son **L–V**.
- **laborable**: lo que diga el calendario del trabajador (F-003:
  `CalendarioLaboralPort` en sv3, `CalendarioProvider` en sv4, con su cascada
  de respaldo). Un día no laborable es fin de semana o festivo **suyo**.
- **último laborable** de una semana: el mayor día L–V de esa semana que sea
  laborable para ese trabajador.
- **jornada del día**: horas ordinarias teóricas de un día concreto. Es lo
  que F-015 introduce; hoy es siempre `c`.
- **línea congelada** (F-004): registro con `sigrid_estado` en
  {`encolado`, `registrado`} o cuyo documento está `approved`.

## Estado de partida (verificado en el árbol el 2026-08-19)

- `jornada_efectiva` / `candef_valido` viven duplicados en
  `services/partes-persistencia/application/services/jornada_resolver.py` y
  `services/partes-front/application/services/jornada_resolver.py` (gemelos
  por comportamiento desde F-003, con test que los compara).
- sv3 aplica jornada **plana**: `_reclasificar_extras_jornada` calcula
  `candef_efectivo` una vez por (recurso, día) y `objetivo_extra = total −
  candef_efectivo`. La rama «día no laborable» va **antes** y manda todo lo
  ordinario a extra.
- sv4 aplica la misma jornada plana en tres sitios: `dias_incompletos`
  (vista trabajador), `incompletos` (matriz de obra) y `_sugerida`
  (`GET /api/sigrid/empleados`).
- La base `partes` tiene **cuatro** tablas y el guardián de F-010
  (`tests/test_f010_orm_models_gemelos.py`) lo afirma con una lista literal:
  añadir una quinta tabla **obliga** a tocar ese guardián (R29).
- `revert_extras_auto()` revierte **todos** los `extra_auto` y
  `fetch_registros_para_recurso()` devuelve **todos** los registros de
  documentos activos, sin mirar `sigrid_estado` ni `approved` (R31/R32).

---

## Jornada semanal derivada del candef

- **R10** (dirigido por evento + comportamiento no deseado). CUANDO el
  sistema necesite la jornada semanal `S` de un recurso, debe derivarla del
  candef efectivo mediante un mapa configurable candef → S
  (`JORNADA_SEMANAL_POR_CANDEF`, por defecto la cadena `8:40,9:42`, **la
  misma en sv3 y en sv4**). SI el candef efectivo es válido pero NO está en
  el mapa, ENTONCES `S = 5 × c` (jornada plana: el comportamiento de hoy) y
  el sistema debe emitir **un WARNING** en log con el candef y el recurso,
  **una sola vez por recurso y por pasada (sv3) o por vista (sv4)**. SI la
  cadena del mapa está mal formada, ENTONCES el servicio debe **fallar al
  arrancar** (fail-fast en el cableado), nunca en caliente ni en silencio.
  - *Criterios*: `8 → 40`; `9 → 42`; `10 → 50` **con** WARNING; `8` y `9`
    sin WARNING; con el mapa `8:40,9:42,10:48`, `10 → 48` sin WARNING; el
    mismo recurso con dos días fuera del mapa en la misma pasada produce
    **un** WARNING, no dos; `"8:40,9"`, `"x:40"`, `"8:40,8:41"` (clave
    repetida) y `""` → error de configuración al construir la app.
  - *Test*: `test_f015_r10_mapa_candef` (sv3 y sv4),
    `test_f015_r10_fail_fast_wiring` (sv3 y sv4).

- **R11** (dirigido por estado). MIENTRAS el candef efectivo sea 8 y su `S`
  sea 40, el sistema debe producir **exactamente** el mismo desglose de
  horas y los mismos avisos que antes de F-015 (jornada 8 en todo día
  laborable, con festivos o sin ellos): **regresión cero**.
  - *Criterios*: los tests dorados de F-003 pasan **sin modificarlos**
    (`services/partes-persistencia/tests/test_f003_r15_splits_dorados.py`,
    `test_f003_r11_jornada_resolver.py`,
    `services/partes-front/tests/test_f003_r12_jornada_resolver.py`); una
    semana con festivo en miércoles y candef 8 sigue dando 8 h el viernes;
    con `calendario=None` (D11) todo día L–V sigue dando 8 h y un sábado
    sigue dando 8 h de jornada, como hoy.
  - *Test*: `test_f015_r11_regresion_candef8` (sv3) + la suite F-003 intacta.

- **R12** (comportamiento no deseado). SI el candef no es válido (vacío,
  no numérico o ≤ `CANDEF_MINIMO_VALIDO`), ENTONCES el sistema debe usar el
  candef efectivo por defecto (8) y su `S` del mapa (40), y seguir marcando
  el valor como «asignado» en el KPI del portal, como hoy.
  - *Criterios*: candef `0`, `1`, `2`, `None`, `""`, `"ocho"` → jornada 8 en
    todos los laborables, 8 el último laborable, `candef_valido` False.
  - *Test*: `test_f015_r12_candef_invalido` (sv3 y sv4).

## Regla del último día laborable

- **R13** (dirigido por evento). CUANDO el sistema calcule la jornada del día
  `d` de un trabajador con candef efectivo `c` y jornada semanal `S`, debe
  aplicar, en este orden: (1) si `d` **no es laborable** → 0; (2) si `d` es
  laborable pero **no es L–V** → `c` (situación solo alcanzable sin
  calendario cableado, D11; ver R14); (3) si `d` es laborable, es L–V y **no
  es el último laborable** de su semana → `c`; (4) si `d` **es el último
  laborable** de su semana → `max(0, S − 4 × c)`. Los festivos L–V cuentan
  como jornada `c` a efectos del resto: el último laborable recibe siempre
  `S − 4c`, haya o no festivos en la semana (lectura A del humano).
  - *Criterios* (c 9, S 42, semana del 2026-03-16 al 2026-03-20): semana
    normal → L–J 9 y **V 6**; viernes festivo → **J 6** y V 0; miércoles
    festivo → X 0, L/M/J 9 y **V 6**; jueves y viernes festivos → **X 6**;
    solo lunes laborable → **L 6**. Con c 8 y S 40 → 8 todos los días.
    Con el mapa `9:40` → último laborable 4. Con c 10 fuera del mapa
    (S = 50) → último laborable 10 (jornada plana). Con `S < 4c`
    (p. ej. mapa `9:30`) → último laborable **0**, nunca negativo.
  - *Test*: `test_f015_r13_ultimo_laborable` (sv3 y sv4, misma tabla).

- **R14** (ubicuo + comportamiento no deseado). El sistema no debe
  considerar nunca sábado ni domingo candidatos a «último laborable». Con el
  calendario cableado (situación de producción desde F-003) sábado y domingo
  son no laborables y por tanto su jornada es 0 y todo lo ordinario va a
  extra, como hoy. SI una semana no tiene **ningún** día laborable L–V,
  ENTONCES ningún día recibe el resto (todos 0).
  - *Criterios*: sábado trabajado 6 h con calendario → 6 h extra; semana
    entera festiva → jornada 0 los cinco días; un viernes festivo no
    convierte al sábado en último laborable.
  - *Test*: `test_f015_r14_finde_y_semana_festiva` (sv3).

- **R15** (ubicuo). El sistema debe determinar «último laborable» mirando
  **solo el calendario** del trabajador (fin de semana + festivos por DNI) y
  nunca los registros que haya o no en la BBDD: una ausencia, una incidencia
  o un día sin parte no cambian qué día es el último laborable ni absorben
  horas. Una semana partida entre dos meses o dos partes se resuelve día a
  día con el mismo calendario.
  - *Criterios*: la misma semana con y sin registros del jueves da el mismo
    reparto del viernes; los días 2026-06-30 (M) y 2026-07-01 (X) procesados
    en dos partes distintos dan lo mismo que procesados juntos; un viernes
    con incidencia y sin horas sigue siendo el último laborable y el jueves
    **no** recibe el resto.
  - *Test*: `test_f015_r15_calendario_no_registros` (sv3).

## Excepciones por trabajador (tabla `empleado_jornada`)

- **R16** (opcional / DONDE). DONDE exista una fila **vigente y activa** de
  `empleado_jornada` para el DNI normalizado del trabajador (`desde ≤ fecha`
  y (`hasta` nulo o `fecha < hasta`), `is_active` verdadero), el sistema
  debe: si la fila trae **patrón explícito** (7 valores L…D) → jornada del
  día = `patrón[weekday(d)]` cuando `d` es laborable y 0 cuando no lo es (sin
  regla del resto); si la fila trae **solo `jornada_semanal`** → usar esa `S`
  en la regla del último laborable (R13) en lugar de la del mapa. Sin fila
  vigente → R10.
  - *Criterios*: fila `S = 48` con c 10 → último laborable 8; fila con patrón
    `7,7,7,7,7,0,0` vigente en julio → 7 h cada día laborable y 0 en festivo;
    fecha fuera de la vigencia → regla del mapa; dos filas para el mismo DNI
    con vigencias disjuntas → cada fecha coge la suya; fila con `is_active`
    falso → se ignora.
  - *Test*: `test_f015_r16_excepciones` (sv3 y sv4).

- **R17** (comportamiento no deseado). SI la lectura de `empleado_jornada`
  falla (BBDD caída, tabla inexistente, error de driver), ENTONCES el sistema
  debe continuar con la jornada derivada (R10–R15) y dejar un WARNING en log,
  sin abortar nunca la conciliación de sv3 ni la vista de sv4. Con la tabla
  **vacía** —situación esperada durante mucho tiempo— no debe haber ni
  WARNING ni ninguna diferencia respecto a R10–R15.
  - *Criterios*: repositorio doble que lanza → mismo resultado que sin tabla,
    con WARNING; tabla vacía → mismo resultado, **sin** WARNING; el fallo se
    registra una vez por pasada, no una por registro.
  - *Test*: `test_f015_r17_tabla_caida_o_vacia` (sv3 y sv4).

- **R18** (ubicuo). El schema de `empleado_jornada` debe declararse en las
  **dos** copias de `infrastructure/database/orm_models.py` (sv3 y sv4) con
  la misma definición, incluida la columna `origen`
  (`manual`/`sigrid`/`sesame`) para que en el futuro la excepción pueda venir
  de Sigrid (`auxtur`) o de Sesame sin cambiar el modelo, y la papelera
  lógica `is_active` (regla 8 de `docs/ARCHITECTURE.md`).
  - *Criterios*: `EmpleadoJornadaOrm` existe en ambas copias con las mismas
    columnas, tipos, `nullable` y defaults; `Base.metadata.create_all` sobre
    SQLite en memoria crea la tabla `empleado_jornada` en los dos servicios;
    `parte_registros` **no gana ni pierde ninguna columna**.
  - *Test*: `test_f015_r18_orm_empleado_jornada` (sv3 y sv4) + R29.

## Resolutor gemelo

- **R19** (ubicuo). La regla (R10–R16) debe vivir en **un** resolutor por
  servicio (`application/services/jornada_resolver.py` de sv3 y de sv4), como
  **función pura** que recibe el calendario como *callable*
  `es_laborable(date) -> bool` ya ligado al DNI, sin saber de BBDD, de red ni
  de Sesame; y las dos copias deben exponer la misma API pública y producir
  el mismo resultado para la misma entrada.
  - *Criterios*: las dos copias declaran `parsear_mapa_semanal`,
    `jornada_semanal_de`, `es_ultimo_laborable`, `Excepcion`,
    `DetalleJornada`, `jornada_dia` y `detalle_jornada_dia` con firmas
    idénticas (`inspect.signature`); una tabla de ≥ 20 casos (los de R13, R14
    y R16 incluidos) ejecutada contra **ambas** implementaciones da el mismo
    resultado; `jornada_efectiva` y `candef_valido` siguen siendo gemelas
    (test de F-003 intacto).
  - *Test*: `tests/test_f015_r19_jornada_resolver_gemelo.py` (raíz del
    monorepo, como el guardián de F-010).

## Cómputo de extras (sv3)

- **R20** (dirigido por evento). CUANDO sv3 normalice el desglose
  ordinaria/extra de un (recurso, día), debe usar como jornada **la jornada
  del día** (R10–R16) en lugar del candef efectivo plano. El resto del
  algoritmo no cambia: rama de día no laborable primero, recorte por
  `registro_id` descendente, extra automática negativa única sobre el
  registro de mayor id, día sin horas ordinarias no se normaliza, recurso sin
  código HE no se toca.
  - *Criterios* (c 9, S 42): lunes 9 h → sin split; viernes 6 h → sin split;
    viernes 9 h → ordinaria 6 + **3 extra**; viernes 4 h → ordinaria 6,
    extra **−2**; viernes festivo con jueves de 6 h → sin split; viernes
    festivo trabajado 5 h → 5 extra; recurso sin HE → sin split aunque la
    jornada del día cambie.
  - *Test*: `test_f015_r20_computo_ultimo_laborable`.

- **R21** (ubicuo). El sistema debe seguir persistiendo `hora_candef` con el
  candef **real** de Sigrid (valor de diagnóstico, puede ser `None`/0) y **no
  debe añadir ni una columna a `parte_registros`**.
  - *Criterios*: en todo split generado, `hora_candef` es el valor crudo de
    `reshor.candef`, nunca el efectivo ni la jornada del día; la huella de
    columnas de `parte_registros` del guardián de F-010 no cambia.
  - *Test*: `test_f015_r21_hora_candef_intacto`.

- **R22** (comportamiento no deseado). El sistema debe resolver el calendario
  y la excepción por el DNI del grupo (el primer `empleado_dni` no vacío del
  grupo, el mismo criterio que `_es_no_laborable`). SI el grupo no tiene DNI,
  ENTONCES debe usar el calendario por defecto y la `S` del mapa, sin
  excepción y sin fallar.
  - *Criterios*: grupo sin DNI → misma jornada que con el calendario por
    defecto, ninguna consulta a `empleado_jornada` por DNI vacío.
  - *Test*: `test_f015_r22_sin_dni`.

- **R23** (comportamiento no deseado). SI alguna de las consultas de
  calendario que deciden el «último laborable» se resolvió **degradada**
  (señal `consumir_degradacion` de F-003), ENTONCES el parte debe quedar
  `review_required = true` igual que hoy (R26 de F-003). F-015 **no** añade
  un tercer régimen de resiliencia.
  - *Criterios*: calendario doble que se declara degradado al mirar el
    viernes de la semana → `marcar_review_required` recibe el `document_id`
    del grupo; calendario fiable → no se marca nada.
  - *Test*: `test_f015_r23_degradado_review`.

## Avisos, KPI y «+ Nuevo» (sv4)

- **R24** (dirigido por evento). CUANDO sv4 evalúe «jornada incompleta» (vista
  trabajador y matriz de obra), debe comparar las horas ordinarias del día con
  **la jornada del día** (R10–R16) y no con el candef efectivo plano.
  - *Criterios* (c 9, S 42): viernes de 6 h → **no** incompleto; lunes de 8 h
    → **sí** incompleto; en semana con viernes festivo, jueves de 6 h → **no**
    incompleto; con c 8 / S 40 el conjunto de días marcados es idéntico al de
    hoy (regresión, R11).
  - *Test*: `test_f015_r24_avisos` (TestClient + SQLite + doble de
    calendario; comprueba `dias_incompletos` e `incompletos` del contexto).

- **R25** (ubicuo). El KPI de jornada de la vista trabajador debe mostrar el
  candef efectivo, la `S` aplicada —marcada como procedente de **excepción**
  cuando lo sea— y la jornada del último laborable; y debe seguir marcando
  «asignado» cuando el candef no venga de Sigrid (R12).
  - *Criterios*: el contexto de la vista lleva `jornada_kpi` con `candef`,
    `semanal`, `origen` (`mapa`|`excepcion`|`plana`) y `ultimo_laborable`; con
    c 9 / S 42 muestra «9 h · 42 h/sem · último laborable 6 h»; con excepción
    de patrón muestra el patrón; render visual **MANUAL (humano)**.
  - *Test*: `test_f015_r25_kpi` (contexto) + parseo Jinja2 de la plantilla.

- **R26** (opcional / DONDE). `GET /api/sigrid/empleados` («+ Nuevo») debe
  seguir devolviendo `jornada_sugerida` con el candef efectivo, sin cambios;
  y DONDE la petición traiga el parámetro `fecha` (ISO `YYYY-MM-DD`), debe
  devolver **además** `jornada_dia` para esa fecha aplicando R13.
  - *Criterios*: sin `fecha` → respuesta byte a byte compatible con la de hoy
    (mismas claves, `jornada_dia` ausente); con `fecha` de un viernes y c 9 →
    `jornada_dia = 6`; con `fecha` mal formada → HTTP 422 o campo ausente con
    aviso, nunca 500.
  - *Test*: `test_f015_r26_sugerida_fecha`.

- **R27** — **RESERVADO PARA F-016** (pantalla de administración de
  `empleado_jornada`). **Fuera del alcance de F-015.** Mientras tanto, las
  filas se cargan por SQL manual del humano.

## Trazabilidad

- **R28** (dirigido por evento). CUANDO sv3 normalice una línea con una
  jornada del día **distinta** del candef efectivo, debe dejar en el log de
  esa operación la marca
  `jornada_dia=<h> (semanal=<S>, origen=<mapa|excepcion|plana>, ultimo_laborable=<si|no>)`.
  - *Criterios*: `caplog` contiene la marca en el mensaje de jornada
    incompleta y en el de recorte a extra; con c 8 / S 40 y día no último
    (jornada = candef) la marca **no** aparece (no se ensucia el log en el
    caso normal).
  - *Test*: `test_f015_r28_log_trazable`.

## Nuevos de F-015

- **R29** (ubicuo). Las dos copias de `orm_models.py` deben seguir siendo
  **byte-idénticas** después de añadir `EmpleadoJornadaOrm`, y el guardián de
  F-010 (`tests/test_f010_orm_models_gemelos.py`) debe actualizarse para
  declarar **cinco** tablas y las columnas literales de la nueva, sin relajar
  ninguna de sus comprobaciones.
  - *Criterios*: `test_f010_r1_las_dos_copias_son_byte_identicas` en verde;
    la constante `TABLAS` del guardián pasa a cinco nombres; la lista literal
    de las 56 columnas de `parte_registros` **no cambia**; el guardián sigue
    fallando si se altera una sola copia (sus casos parametrizados sobre
    `tmp_path` siguen pasando).
  - *Test*: `tests/test_f010_orm_models_gemelos.py` (actualizado) +
    `test_f015_r29_guardian_cinco_tablas`.

- **R30** (ubicuo). El arranque de sv3 y de sv4 debe crear la tabla
  `empleado_jornada` sin intervención manual: `Base.metadata.create_all` la
  crea si no existe y `ddl_complementario()` genera para ella, **derivadas
  del propio ORM**, las sentencias `ALTER TABLE … ADD COLUMN IF NOT EXISTS` y
  `CREATE INDEX IF NOT EXISTS` correspondientes. No se escribe DDL a mano ni
  se añaden ficheros `NN_nombre.sql` (este proyecto no los tiene).
  - *Criterios*: `ddl_complementario()` incluye una sentencia por cada
    columna no primaria de `empleado_jornada` y el `CREATE INDEX` de
    `dni_norm`; el número total de sentencias crece exactamente en lo que
    aporta la tabla nueva; ninguna columna `NOT NULL` sin `server_default`
    (rompería el `ALTER` si la tabla llegara a existir con filas).
  - *Test*: `test_f015_r30_ddl_empleado_jornada` (sv3 y sv4).

- **R31** (comportamiento no deseado; decisión D7 de F-012). SI un registro
  está **congelado** —`sigrid_estado` en {`encolado`, `registrado`} o su
  documento `approved`—, ENTONCES `revert_extras_auto()` no debe borrarlo ni
  restaurar sus `horas_orig`: lo que ya viajó a Sigrid no se recalcula.
  - *Criterios*: un `extra_auto` con `sigrid_estado='registrado'` sobrevive a
    la reversión; un normal recortado de un documento `approved` conserva sus
    `horas` y su `horas_orig`; los no congelados se revierten como hoy; el
    contador devuelto solo cuenta los revertidos de verdad.
  - *Test*: `test_f015_r31_revert_respeta_congelados`.

- **R32** (dirigido por estado; decisión D7 de F-012). MIENTRAS un
  (recurso, día) contenga líneas congeladas, el sistema debe **contarlas en
  el total del día** (para no desequilibrar el reparto) pero **no
  modificarlas**: el recorte y la extra automática solo pueden caer sobre
  líneas no congeladas. SI el día no se puede cuadrar sin tocar una línea
  congelada, ENTONCES no se genera ningún split y se emite un WARNING con el
  recurso y el día.
  - *Criterios*: día con una obra registrada (8 h) y otra pendiente (2 h) con
    jornada 8 → las horas registradas cuentan, el ajuste cae en la línea
    pendiente; día enteramente congelado y descuadrado → **cero** splits + un
    WARNING; día sin congelados → comportamiento idéntico al de hoy
    (regresión, R11).
  - *Test*: `test_f015_r32_congelados_cuentan_no_se_tocan`.

- **R33** (ubicuo). La configuración del mapa debe ser una **variable
  espejo**: el mismo nombre (`JORNADA_SEMANAL_POR_CANDEF`), el mismo valor
  por defecto **en el código de los dos servicios**, documentada en los dos
  `.env.example` y en el script de provisión con el mismo valor. No es un
  secreto y no viaja por Key Vault.
  - *Criterios*: un test carga los dos `config/settings.py` por ruta y
    compara el valor por defecto de `jornada_semanal_por_candef` y de
    `jornada_cache_ttl_s`; ambos `.env.example` contienen la variable con el
    mismo valor comentado; ninguna variable nueva contiene credenciales.
  - *Test*: `tests/test_f015_r33_variable_espejo.py` (raíz).

- **R34** (ubicuo). La documentación normativa debe quedar alineada con la
  regla nueva antes de cerrar la feature: `docs/ARCHITECTURE.md` semántica 3
  (el exceso se mide sobre la jornada **del día**) y semántica 7 (cinco
  tablas), `docs/referencia/partes-proyecto.md` §4.3 y §5, y
  `azure-apps/partes.md` (tabla nueva de la base `partes` y variables nuevas
  de sv3/sv4).
  - *Criterios*: `grep -n "Cuatro tablas" docs/ARCHITECTURE.md` sin
    resultados; la semántica 3 menciona el último laborable y el mapa; el
    documento de `azure-apps` lista `empleado_jornada` y
    `JORNADA_SEMANAL_POR_CANDEF`; commit local en `azure-apps` (ese repo no
    tiene remoto), sin push.
  - *Test*: revisión del reviewer contra C3/C5 (+ el `grep` anterior).

- **R35** (comportamiento no deseado; **requisito de PROCESO**, no de
  software). SI **F-014 no está verificada en Sigrid** (los 7 recursos de la
  cuadrilla con `candef = 9` en su hora por defecto y el octavo con DNI en
  `emp`), ENTONCES la rama `feature/F-015-jornada-semanal-candef` **no debe
  mergearse a `dev` ni desplegarse**. Decisión del humano (F-012 §10.6, D3).
  - *Criterios*: `harness/features.json` tiene F-014 en `done` y su
    verificación por sigrid-api (solo lectura) anotada en `progress/`.
  - *Verificación*: **MANUAL (humano)**. Comando exacto y resultado esperado
    en `progress/peticion_F-014.md` (rama `feature/F-014-candef-9-sigrid`),
    apartado 6.
  - *Aviso operativo* que el humano debe conocer (ver `design.md` §11.2): la
    ventana peligrosa es la **inversa** de la que suele temerse. F-015 sin
    F-014 es regresión cero; **F-014 sin F-015 sí hace daño** (candef 9 con
    jornada plana ⇒ −3 h/semana de extra negativa a esos 7 recursos). El
    cambio en Sigrid y el despliegue de F-015 deben ir **seguidos**.

---

## Trazabilidad: escenarios de F-012 → requisito → test

| Escenario (F-012 §4) | Requisito | Test |
|---|---|---|
| A · cuadrilla, régimen 42, viernes 6 h | R13, R20 | `test_f015_r20_computo_ultimo_laborable` |
| A' · viernes de 9 h (hoy se pierden extras) | R20 | ídem |
| A'' · viernes de 4 h (extra −2 + aviso) | R20, R24 | ídem + `test_f015_r24_avisos` |
| B · viernes festivo | R13 | `test_f015_r13_ultimo_laborable` |
| B' · viernes festivo trabajado | R14, R20 | `test_f015_r14_finde_y_semana_festiva` |
| C · miércoles festivo | R13 | `test_f015_r13_ultimo_laborable` |
| D · jueves y viernes festivos | R13 | ídem |
| E · solo lunes laborable | R13 | ídem |
| F · semana entera festiva | R14 | `test_f015_r14_finde_y_semana_festiva` |
| G · semana partida entre meses/partes | R15 | `test_f015_r15_calendario_no_registros` |
| H · parte que solo trae L–M | R15 | ídem |
| I · ausencia el viernes | R15 | ídem |
| J · sábado trabajado | R14 | `test_f015_r14_finde_y_semana_festiva` |
| K · c 8 / S 40 con festivos (**regresión**) | R11 | `test_f015_r11_regresion_candef8` + dorados F-003 |
| L · cuadrilla **antes** de F-014 | R11, R35 | `test_f015_r11_regresion_candef8` + MANUAL |
| M · candef válido fuera del mapa | R10 | `test_f015_r10_mapa_candef` |
| N · intensiva 7×5 | **fuera de alcance** (F-011) | — |
| O · recurso sin código HE | R20 | `test_f015_r20_computo_ultimo_laborable` |
| P · candef inválido | R12 | `test_f015_r12_candef_invalido` |
| Q · excepción con `S = 48` | R16 | `test_f015_r16_excepciones` |
| R · excepción con patrón 7×5 | R16 | ídem |

## Fuera de alcance (explícito)

- **F-016**: pantalla de administración de `empleado_jornada` (R27). F-015
  crea la tabla **vacía** y no siembra ninguna fila.
- **F-011**: jornada reducida por días (intensiva 7×5, `emphis.porjorlab`).
  F-015 deja la tabla preparada para que F-011 se apoye en ella.
- **F-014**: el cambio de datos maestros en Sigrid. F-015 **no escribe** en
  Sigrid: ni una consulta nueva, ni una columna nueva del lado del ERP.
- **sv1, sv2 y sv5**: no se tocan. El payload hacia sv5 y lo que sv5 escribe
  en el ERP no cambian (llegan líneas ya desglosadas).
- Cualquier columna nueva en `parte_registros` o `parte_documents` (R21).
- Un «servicio de jornadas» o una librería compartida entre servicios:
  `docs/ARCHITECTURE.md` lo prohíbe y sería un salto de red por línea.

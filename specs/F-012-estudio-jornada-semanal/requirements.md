<!-- specs/F-012-estudio-jornada-semanal/requirements.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Requisitos

> F-012 es un **ESTUDIO**: su entregable es el análisis con datos reales y la
> propuesta de diseño que viven en `design.md`. NO cambia código ni schema.
> Por eso los requisitos van en dos bloques: **A** (lo que debe cumplir el
> estudio, verificable leyendo `design.md`) y **B** (lo que debe cumplir la
> implementación que el estudio propone, redactado ya en EARS para que la
> feature de implementación —propuesta como **F-014**— lo herede tal cual
> una vez el humano tome las decisiones abiertas D1–D7 de `design.md`).
> Ningún requisito del bloque B se implementa en F-012.

Petición literal del humano (2026-08-16): «hay que estudiar la gente que
tiene 9h como candef, cómo se comportan los viernes (deberían ser el resto
de horas hasta las 40 semanales, pero hay que dejar que esas 40 semanales
sean particularizables, porque hay algún trabajador que hace más de 40h
semanales)».

## Bloque A — Requisitos del estudio (F-012)

- **R1.** El estudio debe cuantificar, con datos reales de Sigrid leídos
  SOLO a través de `sigrid-api` (`POST /api/sql/read`, base `ruesma`),
  cuántos recursos vivos tienen `candef = 9` en su hora por defecto, qué
  otros valores de `candef` existen y con qué frecuencia, y qué códigos de
  hora tienen esos recursos.
  *Verificación: MANUAL (humano) — `design.md` §3 (hallazgos H1–H2) con las
  cifras y el SQL reproducible en el anexo.*
- **R2.** El estudio debe describir, con el histórico real de partes
  registrados en Sigrid (`hmores`, 2025-01 → 2026-08), cómo se registran
  hoy los viernes y las semanas de los trabajadores con jornada de 9 h o
  más de 40 h semanales (pares ordinaria/extra por día de semana,
  distribución de horas semanales), y cuántos trabajadores muestran ese
  patrón.
  *Verificación: MANUAL (humano) — `design.md` §3 (H3–H6).*
- **R3.** El estudio debe inventariar las fuentes candidatas de la jornada
  semanal particularizable (campos de Sigrid, tabla propia en la BBDD
  `partes`, Sesame) indicando para cada una si HOY tiene datos, quién la
  mantendría y qué le falta, y recomendar una.
  *Verificación: MANUAL (humano) — `design.md` §5 y decisión D1.*
- **R4.** El estudio debe proponer un modelo de jornada teórica que
  reproduzca la regla pedida («los viernes, el resto hasta la jornada
  semanal») y demostrar con ejemplos numéricos cómo cambiarían el cómputo
  de extras de sv3 y los avisos de jornada incompleta de sv4 respecto a
  hoy, incluyendo los casos límite (semana con festivo, semana partida
  entre dos meses/partes, semana incompleta, día no laborable, recurso sin
  código HE, candef no válido).
  *Verificación: MANUAL (humano) — `design.md` §4 y §6.*
- **R5.** El estudio debe declarar qué servicios tocaría la implementación
  y por qué (regla LÍMITE DE SERVICIO), qué ficheros exactos se crearían
  o modificarían, y qué NO se toca.
  *Verificación: MANUAL (humano) — `design.md` §1, §7 y §8.*
- **R6.** El estudio debe dejar listadas y numeradas las decisiones que
  solo el humano puede tomar, cada una con la opción recomendada y su
  motivo, y proponer el reparto en features de implementación.
  *Verificación: MANUAL (humano) — `design.md` §9 y `tasks.md`.*
- **R7.** El estudio no debe versionar datos personales: ni DNIs ni nombres
  de trabajadores; los recursos se citan por su código Sigrid (`MO/NNNN`)
  o su `ide`. Tampoco URLs ni claves de sigrid-api.
  *Verificación: `grep -nE "[0-9]{8}[A-Z]" specs/F-012-estudio-jornada-semanal/*.md`
  sin resultados; revisión visual del anexo SQL.*

## Bloque B — Requisitos de la implementación propuesta (heredables por F-014)

Vocabulario: **jornada del día** = horas ordinarias teóricas de un día
concreto para un trabajador; **patrón semanal** = jornada del día para cada
día de la semana (L…D); **jornada semanal** = suma del patrón (por defecto
40 h). El **candef efectivo** es el que ya devuelve `jornada_efectiva`
(candef si > mínimo, si no la jornada por defecto).

### Regla de jornada (resolutor único, sv3 y sv4 gemelos)

- **R10.** El sistema debe calcular la jornada del día de un trabajador a
  partir de su patrón semanal; y MIENTRAS el trabajador no tenga un patrón
  explícito, el sistema debe derivarlo así: lunes a jueves = candef
  efectivo; viernes = jornada semanal − 4 × candef efectivo (nunca
  negativo); sábado y domingo = 0.
  *Test: `test_f014_r10_patron_derivado` — (candef 8, semanal 40) → 8,8,8,8,8;
  (9, 40) → 9,9,9,9,4; (9, 42) → 9,9,9,9,6; (10, 48) → 10,10,10,10,8;
  (9, 30) → viernes 0, no −6.*
- **R11.** MIENTRAS el trabajador no tenga jornada semanal particularizada,
  el sistema debe usar la jornada semanal por defecto configurable
  (`JORNADA_SEMANAL_POR_DEFECTO`, 40.0), de modo que con candef 8 el
  resultado sea IDÉNTICO al comportamiento actual (regresión cero).
  *Test: `test_f014_r11_regresion_candef8` — los casos dorados de F-003
  (`test_f003_r15_splits_dorados.py`, `test_f003_r11/r12`) pasan sin
  cambios con la nueva firma.*
- **R12.** SI el candef no es válido (vacío o ≤ mínimo), ENTONCES el
  sistema debe derivar el patrón con la jornada por defecto diaria (8 h) y
  seguir marcando el valor como «asignado», exactamente como hoy.
  *Test: `test_f014_r12_candef_invalido` — candef 0/1/None → 8,8,8,8,8 y
  `candef_valido` False.*
- **R13.** CUANDO exista un patrón semanal explícito por día para el
  trabajador (siete valores) vigente en la fecha consultada, el sistema
  debe usarlo con prioridad sobre el patrón derivado, y CUANDO existan
  varios registros de jornada para el mismo trabajador el sistema debe
  elegir el vigente por rango de fechas (`desde` ≤ fecha < `hasta`, `hasta`
  nulo = abierto), sin solapes.
  *Test: `test_f014_r13_patron_explicito` — patrón 7×5 desde 2026-07-01
  hasta 2026-09-01: día de julio → 7; día de junio → derivado.*
- **R14.** Las dos copias del resolutor (`services/partes-front/…` y
  `services/partes-persistencia/…/application/services/jornada_resolver.py`)
  deben producir el mismo resultado para la misma entrada.
  *Test: `test_f014_r14_gemelos` — tabla de casos ejecutada contra ambas
  implementaciones (patrón del guardián de F-003).*

### Fuente de la jornada semanal

- **R15.** El sistema debe leer la jornada semanal particularizada y el
  patrón explícito de una tabla `empleado_jornada` de la BBDD `partes`,
  identificando al trabajador por DNI normalizado (misma clave que
  `empleado_alias`), y DONDE la tabla no tenga fila para ese DNI debe
  aplicar el valor por defecto (R11).
  *Test: `test_f014_r15_lectura_tabla` — SQLite en memoria con dos filas;
  DNI con fila → semanal 42; DNI sin fila → 40.* La creación de la tabla en
  PostgreSQL real es `MANUAL (humano)`.
- **R16.** SI la lectura de `empleado_jornada` falla (BBDD caída, tabla
  inexistente), ENTONCES el sistema debe continuar con el valor por defecto
  y dejar WARNING en log; nunca abortar la conciliación ni la vista.
  *Test: `test_f014_r16_tabla_caida` — repositorio doble que lanza; el
  cómputo produce lo mismo que sin tabla.*
- **R17.** El schema de la tabla debe declararse en las DOS copias de
  `infrastructure/database/orm_models.py` (sv3 y sv4) con la misma
  definición.
  *Test: `test_f014_r17_orm_gemelos` — compara columnas/tipos de
  `EmpleadoJornadaOrm` en ambas copias.*

### Cómputo de extras (sv3)

- **R18.** CUANDO sv3 normalice el desglose ordinaria/extra de un
  (recurso, día) laborable, debe usar como jornada la jornada del día
  (R10–R13) en lugar del candef efectivo plano; el resto del algoritmo
  (recorte por id descendente, extra negativa única, día no laborable → todo
  extra, recurso sin HE → sin normalizar) no cambia.
  *Test: `test_f014_r18_viernes_9x4` — recurso candef 9, semanal 40:
  L 9 h → 0 extra; V 4 h → 0 extra; V 6 h → +2; V 3 h → ordinaria 4, extra
  −1. Con semanal 42: V 6 h → 0 extra.*
- **R19.** El sistema debe seguir persistiendo `hora_candef` con el candef
  REAL de Sigrid (diagnóstico) y NO debe añadir columnas a
  `parte_registros`.
  *Test: `test_f014_r19_hora_candef_intacto` — los splits llevan
  `hora_candef` = candef real aunque la jornada del día sea otra.*
- **R20.** El sistema debe resolver la jornada del día por DNI del grupo
  (primer `empleado_dni` no vacío del grupo, como `_es_no_laborable`);
  SI el grupo no tiene DNI, ENTONCES aplica el patrón derivado con la
  jornada semanal por defecto.
  *Test: `test_f014_r20_sin_dni` — grupo sin DNI → viernes 40 − 4×candef.*

### Avisos y vistas (sv4)

- **R21.** CUANDO sv4 evalúe «jornada incompleta» (vista trabajador y
  matriz de obra), debe comparar las horas ordinarias del día con la
  jornada del día (R10–R13), de modo que un viernes de 4 h con candef 9 y
  semanal 40 NO se marque incompleto y un lunes de 8 h con candef 9 SÍ.
  *Test: `test_f014_r21_avisos_viernes` — TestClient con repositorio SQLite
  y filas de fixture; comprueba `dias_incompletos` / `incompletos` del
  contexto.*
- **R22.** El KPI de jornada de la vista trabajador debe mostrar el patrón
  aplicado (p. ej. «9 h L–J · 4 h V · 40 h/sem») y si la jornada semanal es
  particularizada o por defecto.
  *Test: `test_f014_r22_kpi_patron` — contexto de la vista contiene el
  patrón; el render se verifica MANUAL.*
- **R23.** La `jornada_sugerida` de `GET /api/sigrid/empleados` («+ Nuevo»)
  debe seguir devolviendo el candef efectivo (jornada L–J) — no cambia — y
  DONDE la petición traiga `fecha`, debe devolver además `jornada_dia` para
  esa fecha.
  *Test: `test_f014_r23_sugerida_fecha` — sin fecha: solo `jornada_sugerida`;
  con fecha viernes y candef 9: `jornada_dia` = 4.*
- **R24.** DONDE se decida mantenimiento desde el portal (decisión D5), el
  sistema debe ofrecer una vista de administración para crear/editar/cerrar
  filas de `empleado_jornada` (DNI, jornada semanal, patrón opcional,
  desde/hasta, nota), registrando quién y cuándo, y validando: horas
  0–24 por día, `desde` < `hasta`, sin solapes por DNI.
  *Test: `test_f014_r24_admin_jornadas` — TestClient: alta válida 200,
  solape 422, horas 25 → 422.* (Se puede diferir a F-015, ver tasks.)

### Trazabilidad

- **R25.** Toda línea normalizada con una jornada del día distinta del
  candef efectivo debe poder rastrearse: el log de sv3 anota
  `jornada_dia=<h> (patron=<derivado|explicito>, semanal=<h>)` en el
  mensaje de recorte / jornada incompleta.
  *Test: `test_f014_r25_log_trazable` — `caplog` contiene la marca.*

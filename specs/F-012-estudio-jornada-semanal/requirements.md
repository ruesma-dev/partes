<!-- specs/F-012-estudio-jornada-semanal/requirements.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Requisitos

> F-012 es un **ESTUDIO**: su entregable es el análisis con datos reales y la
> propuesta de diseño que viven en `design.md`. NO cambia código ni schema.
> Los requisitos van en dos bloques: **A** (lo que debe cumplir el estudio,
> verificable leyendo `design.md`) y **B** (lo que debe cumplir la
> implementación, ya en EARS, para que la feature de implementación
> —**F-015**— lo herede tal cual). Ningún requisito del bloque B se
> implementa en F-012.
>
> **Versión 2 (2026-08-18)**: rehecha con las decisiones FIRMES del humano
> tras revisar la primera versión: (1) la jornada semanal SE DERIVA DEL
> CANDEF por un mapa configurable `{8: 40, 9: 42}` y Sigrid es la fuente
> (F-014 corrige allí los candef); (2) el «resto» no es «el viernes», es el
> **último día laborable de la semana** del trabajador según su calendario,
> contando los festivos como jornada; (3) las excepciones van a una tabla
> `empleado_jornada` (vacía mucho tiempo), con UI de administración en una
> feature posterior (**F-016**).

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
  *Verificación: MANUAL (humano) — `design.md` §3 (H1–H2) y anexo A.*
- **R2.** El estudio debe describir, con el histórico real de partes
  registrados en Sigrid (`hmores`, 2025-01 → 2026-08), cómo se registran
  hoy los viernes y las semanas de los trabajadores con jornada de 9 h o
  más de 40 h semanales, y cuántos trabajadores muestran ese patrón.
  *Verificación: MANUAL (humano) — `design.md` §3 (H3–H6).*
- **R3.** El estudio debe inventariar las fuentes candidatas de la jornada
  semanal (candef de Sigrid, otros campos de Sigrid, tabla propia, Sesame)
  indicando si HOY tienen datos, quién las mantendría y qué les falta, y
  reflejar la decisión tomada.
  *Verificación: MANUAL (humano) — `design.md` §5.*
- **R4.** El estudio debe formular la regla decidida («el último día
  laborable de la semana = jornada semanal − candef × los otros cuatro
  días L–V, festivos incluidos») y demostrar con ejemplos numéricos cómo
  cambian el cómputo de extras de sv3 y los avisos de sv4 respecto a hoy,
  incluyendo los casos límite: festivo en viernes / miércoles / jueves y
  viernes, semana con todos los días festivos, semana partida entre dos
  meses o partes, semana incompleta, sábado/domingo trabajado, ausencias,
  recurso sin código HE, candef no válido, candef fuera del mapa.
  *Verificación: MANUAL (humano) — `design.md` §4 y §6.*
- **R5.** El estudio debe declarar qué servicios tocaría la implementación
  y por qué (LÍMITE DE SERVICIO), qué ficheros exactos se crearían o
  modificarían, y qué NO se toca.
  *Verificación: MANUAL (humano) — `design.md` §1, §7 y §8.*
- **R6.** El estudio debe registrar las decisiones ya tomadas por el humano
  con su fecha, dejar numeradas SOLO las que sigan abiertas (con opción
  recomendada), listar los MANUAL del humano y el reparto en features
  (F-014 prerrequisito, F-015 regla, F-016 UI).
  *Verificación: MANUAL (humano) — `design.md` §9 y `tasks.md`.*
- **R7.** El estudio no debe versionar datos personales: ni DNIs ni nombres
  de trabajadores; los recursos se citan por su código Sigrid (`MO/NNNN`)
  o su `ide`. Tampoco URLs ni claves de sigrid-api.
  *Verificación: `grep -nE "[0-9]{8}[A-Z]" specs/F-012-estudio-jornada-semanal/*.md`
  sin resultados; revisión visual del anexo SQL.*

## Bloque B — Requisitos de la implementación (heredables por F-015)

Vocabulario: **candef efectivo** = lo que ya devuelve `jornada_efectiva`
(candef si > mínimo, si no la jornada diaria por defecto, 8). **Jornada
semanal** S = horas ordinarias teóricas de la semana. **Semana** = lunes a
domingo; los días candidatos a jornada son L–V. **Laborable** = ni fin de
semana ni festivo según el calendario del trabajador (F-003:
`CalendarioLaboralPort` en sv3, `CalendarioProvider` en sv4, con su
cascada de respaldo). **Último laborable** de una semana = el mayor día
L–V de esa semana que sea laborable para ese trabajador. **Jornada del
día** = horas ordinarias teóricas de un día concreto.

### Jornada semanal derivada del candef

- **R10.** El sistema debe derivar la jornada semanal S del candef efectivo
  del recurso mediante un mapa configurable candef → S
  (`JORNADA_SEMANAL_POR_CANDEF`, por defecto `8:40,9:42`); SI el candef
  efectivo no está en el mapa, ENTONCES S = `JORNADA_SEMANAL_POR_DEFECTO`
  (40.0).
  *Test: `test_f015_r10_mapa_candef` — 8 → 40; 9 → 42; 10 → 40 (mapa por
  defecto); mapa `8:40,9:42,10:48` → 10 → 48; mapa mal formado → error de
  configuración al arrancar (fail-fast), no en caliente.*
- **R11.** MIENTRAS el candef efectivo sea 8 y S 40, el sistema debe
  producir EXACTAMENTE el mismo desglose y los mismos avisos que hoy
  (jornada 8 todos los días laborables): regresión cero.
  *Test: `test_f015_r11_regresion_candef8` — los casos dorados de F-003
  (`test_f003_r15_splits_dorados.py`, `test_f003_r11/r12`) pasan sin
  cambios; además una semana con festivo y candef 8 sigue dando 8 h el
  último laborable.*
- **R12.** SI el candef no es válido (vacío o ≤ mínimo), ENTONCES el sistema
  debe usar el candef efectivo por defecto (8) y su S del mapa (40), y
  seguir marcando el valor como «asignado» en el portal, como hoy.
  *Test: `test_f015_r12_candef_invalido` — candef 0/1/None → jornada 8 en
  todos los laborables y `candef_valido` False.*

### Regla del último laborable

- **R13.** CUANDO el sistema calcule la jornada del día d (L–V) de un
  trabajador, debe aplicar: si d NO es laborable → 0; si d es laborable y
  NO es el último laborable de su semana → candef efectivo; si d ES el
  último laborable de su semana → `max(0, S − 4 × candef efectivo)`. Los
  festivos L–V cuentan como jornada de candef a efectos del «resto»
  (lectura A del humano): el último laborable recibe siempre
  `S − 4 × candef`, haya o no festivos en la semana.
  *Test: `test_f015_r13_ultimo_laborable` — candef 9, S 42: semana normal
  → V 6; viernes festivo → J 6 (y V 0); miércoles festivo → X 0, V 6;
  jueves y viernes festivos → X 6; solo lunes laborable → L 6. Candef 8,
  S 40 → siempre 8. Candef 9, S 40 → último 4. Candef 10, S 40 (fuera del
  mapa) → último 0.*
- **R14.** El sistema debe considerar sábado y domingo NUNCA candidatos a
  último laborable ni a jornada (jornada 0: todo lo ordinario a extra,
  como hoy); y SI una semana no tiene ningún día laborable L–V, ENTONCES
  ningún día recibe el «resto» (todos 0).
  *Test: `test_f015_r14_finde_y_semana_festiva` — sábado trabajado 6 h →
  6 extra; semana entera festiva → 0 jornada todos los días.*
- **R15.** El sistema debe determinar «último laborable» mirando SOLO el
  calendario del trabajador (fin de semana + festivos por DNI), nunca los
  registros que haya o no en la BBDD: una ausencia, una incidencia o un
  día sin parte NO cambian qué día es el último laborable ni absorben
  horas; y la semana partida entre dos meses o dos partes se resuelve día a
  día con el mismo calendario (el último laborable puede estar en el otro
  parte y no hace falta tenerlo).
  *Test: `test_f015_r15_calendario_no_registros` — misma semana con y sin
  registros del jueves: el viernes recibe el resto en ambos casos; semana
  30/06–04/07 con partes de junio y julio por separado → cada día igual
  que si se procesaran juntos.*

### Excepciones (tabla `empleado_jornada`)

- **R16.** DONDE exista una fila vigente en `empleado_jornada` para el DNI
  normalizado del trabajador (`desde` ≤ fecha < `hasta`, `hasta` nulo =
  abierta), el sistema debe: si la fila trae patrón explícito (7 valores
  L…D) → usar `patrón[día]` como jornada del día (sin regla del resto; el
  calendario sigue mandando: día no laborable → 0); si trae solo
  `jornada_semanal` → usar esa S en la regla del último laborable (R13) en
  lugar de la del mapa. Sin fila → R10.
  *Test: `test_f015_r16_excepciones` — fila S=48 con candef 10 → último
  laborable 8; fila patrón 7×5 vigente en julio → 7 cada día, 0 en festivo;
  fecha fuera de vigencia → regla del mapa.*
- **R17.** SI la lectura de `empleado_jornada` falla (BBDD caída, tabla
  inexistente), ENTONCES el sistema debe continuar con la jornada derivada
  (R10–R15) y dejar WARNING en log; nunca abortar la conciliación ni la
  vista. Con la tabla vacía (situación esperada durante mucho tiempo) no
  debe haber ni WARNING ni diferencia alguna respecto a R10–R15.
  *Test: `test_f015_r17_tabla_caida_o_vacia` — repositorio doble que
  lanza → mismo resultado que sin tabla + WARNING; tabla vacía → mismo
  resultado sin WARNING.*
- **R18.** El schema de `empleado_jornada` debe declararse en las DOS
  copias de `infrastructure/database/orm_models.py` (sv3 y sv4) con la
  misma definición, con columna `origen` (`manual`/`sigrid`/`sesame`) para
  que en el futuro la excepción pueda venir de Sigrid (`auxtur`) o Sesame
  sin cambiar el modelo.
  *Test: `test_f015_r18_orm_gemelos` — compara columnas/tipos de
  `EmpleadoJornadaOrm` en ambas copias.*

### Resolutor gemelo

- **R19.** La regla (R10–R16) debe vivir en UN resolutor por servicio
  (`application/services/jornada_resolver.py` de sv3 y de sv4), como
  función pura que recibe el calendario como *callable* `es_laborable(date)
  -> bool` ya ligado al DNI; y las dos copias deben producir el mismo
  resultado para la misma entrada.
  *Test: `test_f015_r19_gemelos` — tabla de casos (incluidos los de R13)
  ejecutada contra ambas implementaciones.*

### Cómputo de extras (sv3)

- **R20.** CUANDO sv3 normalice el desglose ordinaria/extra de un
  (recurso, día), debe usar como jornada la jornada del día (R10–R16) en
  lugar del candef efectivo plano; el resto del algoritmo (recorte por id
  descendente, extra negativa única, día no laborable → todo extra,
  recurso sin HE → sin normalizar) no cambia.
  *Test: `test_f015_r20_computo_ultimo_laborable` — candef 9, S 42: L 9 h
  → 0 extra; V 6 h → 0 extra; V 9 h → ordinaria 6 + 3 extra; V 4 h →
  ordinaria 6, extra −2; viernes festivo y J 6 h → 0 extra; V (festivo)
  trabajado 5 h → 5 extra.*
- **R21.** El sistema debe seguir persistiendo `hora_candef` con el candef
  REAL de Sigrid (diagnóstico) y NO debe añadir columnas a
  `parte_registros`.
  *Test: `test_f015_r21_hora_candef_intacto`.*
- **R22.** El sistema debe resolver el calendario y la excepción por el DNI
  del grupo (primer `empleado_dni` no vacío, como `_es_no_laborable`); SI
  el grupo no tiene DNI, ENTONCES usa el calendario por defecto y la S del
  mapa (sin excepción).
  *Test: `test_f015_r22_sin_dni`.*
- **R23.** SI el calendario que decide «último laborable» se resolvió
  degradado (señal `consumir_degradacion` de F-003), ENTONCES el parte
  queda `review_required=true` igual que hoy (R26 de F-003): la regla del
  resto no añade un tercer régimen de resiliencia.
  *Test: `test_f015_r23_degradado_review` — calendario fake degradado →
  `marcar_review_required` recibe el documento.*

### Avisos y vistas (sv4)

- **R24.** CUANDO sv4 evalúe «jornada incompleta» (vista trabajador y
  matriz de obra), debe comparar las horas ordinarias del día con la
  jornada del día (R10–R16), de modo que con candef 9 / S 42 un viernes de
  6 h NO se marque incompleto, un lunes de 8 h SÍ, y en semana con viernes
  festivo el jueves de 6 h NO.
  *Test: `test_f015_r24_avisos` — TestClient + SQLite + doble de
  calendario; comprueba `dias_incompletos` / `incompletos` del contexto.*
- **R25.** El KPI de jornada de la vista trabajador debe mostrar el candef
  efectivo, la S derivada (o la de la excepción, marcada como tal) y la
  jornada del último laborable (p. ej. «9 h · 42 h/sem · último laborable
  6 h»).
  *Test: `test_f015_r25_kpi` — contexto de la vista; render MANUAL.*
- **R26.** La `jornada_sugerida` de `GET /api/sigrid/empleados` («+ Nuevo»)
  debe seguir devolviendo el candef efectivo, y DONDE la petición traiga
  `fecha`, debe devolver además `jornada_dia` para esa fecha (R13).
  *Test: `test_f015_r26_sugerida_fecha`.*
- **R27.** (F-016) DONDE exista la pantalla de administración de
  `empleado_jornada`, el sistema debe permitir crear/editar/cerrar filas
  (DNI, S y/o patrón, desde/hasta, nota), registrando quién y cuándo, y
  validando horas 0–24, `desde` < `hasta` y ausencia de solapes por DNI.
  *Test: `test_f016_r27_admin` — alta 200; solape 422; horas 25 → 422.*

### Trazabilidad

- **R28.** Toda línea normalizada con una jornada del día distinta del
  candef efectivo debe poder rastrearse: el log de sv3 anota
  `jornada_dia=<h> (semanal=<S>, origen=<mapa|excepcion>, ultimo_laborable=<si|no>)`
  en el mensaje de recorte / jornada incompleta.
  *Test: `test_f015_r28_log_trazable` — `caplog` contiene la marca.*

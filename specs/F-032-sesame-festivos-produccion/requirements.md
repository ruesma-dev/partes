<!-- specs/F-032-sesame-festivos-produccion/requirements.md -->
# F-032 · Activar Sesame en producción: festivos de cada trabajador

Spec rehecha el 2026-11-17 con el diseño del humano: los festivos se guardan en `partes` y
solo se traen al ingerir. Rigor **crítico** (DA10). Toca sv3, sv4, el ORM gemelo, `infra/` y
docs; sesame-api lo despliega el humano. DA1–DA20 decididas, DA11 retirada (design §9).
Partida (design §1): F-003 apagada, caché solo en memoria y bloqueo `[SIN-SESAME]` en sv4.

Glosario. **Fila**: registro de `festivos_trabajador` por (DNI normalizado, año).
**Incompleto**: menos festivos del año que `SESAME_FESTIVOS_MINIMOS` (defecto 1). **Respaldo
actual**: el de hoy sin Sesame (sv3 `config/calendario_laboral.json`; sv4 `holidays` Madrid
más extras). **Cascada de lectura** (DA19): fila del DNI; sin ella o sin DNI, respaldo
actual. **Congelada**: línea con `_congelado` verdadero en el conciliador.

## A. Tabla `festivos_trabajador` (ORM gemelo, DA14)

- **R1.** Los dos `orm_models.py` (sv3 y sv4) deben declarar, byte a byte iguales, la tabla
  `festivos_trabajador`: `id`, `dni_norm`, `ano`, `festivos_json`, `n_festivos` y
  `leido_en_utc`, con índice único (`dni_norm`, `ano`) y `server_default` en toda columna
  NOT NULL. El guardián de F-010 debe pasar a nueve tablas. `festivos_json` es
  `{fecha ISO: nombre o null}` con solo días de `ano`; `n_festivos`, su tamaño.
- **R2.** CUANDO arranca sv3 o sv4 contra una base sin la tabla, `create_all` debe crearla
  sin tocar las tablas existentes, y `ddl_complementario` debe incluir su índice. (capa: integración)
- **R3.** Ningún log, mensaje de excepción ni informe Markdown nuevo debe contener un DNI:
  los logs dan recuentos. Tampoco la clave `SESAME_API_KEY` (solo su longitud).

## B. Refresco en la ingesta (sv3, DA15, DA4 y DA5)

- **R4.** CUANDO sv3 ingiere un parte nuevo con Sesame cableado, antes de guardarlo debe
  pedir a sesame-api los festivos de cada DNI distinto de sus líneas, para cada año de la
  semana ISO de la fecha del parte (sin fecha: hoy). Las respuestas buenas se escriben por
  upsert con `leido_en_utc`. Las líneas sin DNI no piden nada.
- **R5.** CUANDO sesame-api responde 404 a un DNI, no debe escribirse ni borrarse fila: usa
  la que tuviera o el respaldo actual (DA19). Un 404 no es fallo ni sube el parte a revisión.
- **R6.** SI una respuesta es incompleta, ENTONCES no debe guardarse y cuenta como fallo.
  `SESAME_FESTIVOS_MINIMOS` es entero ≥ 0 (0 no controla). SI es negativo o no entero,
  ENTONCES sv3 no debe arrancar. El log `[sesame][wiring] CABLEADO` lo incluye.
- **R7.** SI pedir los festivos de un (DNI, año) falla (excepción, plazo o incompleto) y ya
  hay fila, ENTONCES debe conservarse sin tocar y el parte no sube a revisión por ello.
- **R8.** SI falla un (DNI, año) del parte y no hay fila, ENTONCES el parte debe guardarse
  con `review_required = true` (nivel de F-003) y un WARNING con el recuento.
- **R9.** El refresco nunca debe impedir guardar el parte: todo error va por R7–R8.
- **R10.** CUANDO el parte es un duplicado por `sha256`, no debe pedirse nada a Sesame.
- **R11.** Dos upserts de una clave, también de dos réplicas, dejan una fila. (capa: integración)
- **R12.** MIENTRAS sv3 no tenga Sesame cableado, no debe refrescar ni leer la tabla: el
  calendario es el JSON de siempre y el log dice `DESACTIVADO`.

## C. El cómputo de extras lee la tabla (sv3)

- **R13.** MIENTRAS sv3 tenga Sesame cableado, el calendario de `RecursoConciliador` debe
  dar no laborable al fin de semana y a los festivos de la cascada de lectura: la fila del
  DNI y, sin fila o sin DNI, el JSON.
- **R14.** Las pasadas de `conciliar_todos` (las de cada ingesta y las de los mensajes
  `recalcular` de sv4) no deben llamar nunca a sesame-api.
- **R15.** Las filas leídas deben cachearse ≤ 60 s. El refresco debe invalidar las claves que
  escribe, para que la pasada de esa misma ingesta ya las use.
- **R16.** SI falla la lectura de la tabla, ENTONCES ese día debe resolverse con el JSON y un
  WARNING, sin subir partes a revisión. Las pasadas no marcan degradación: solo marca R8.
- **R17.** `SesameCalendarioLaboral` y su test de F-003 deben retirarse; sv3 deja de leer
  `SESAME_CACHE_TTL_S`. `recurso_conciliador.py` no cambia.

## D. Portal: festivos desde la tabla, sin bloqueo (sv4, DA16–DA18)

- **R18.** MIENTRAS sv4 tenga `SESAME_API_*` (DA18), `CalendarioProvider` debe resolver los
  festivos con la cascada de lectura: fila del DNI ⇒ fuente `sesame`, fiable; sin fila o sin
  DNI ⇒ fuente `sin_fila`, respaldo `holidays`, **no fiable** (solo enciende el aviso).
- **R19.** sv4 no debe llamar a `festivos` ni a `calendario_por_defecto` de sesame-api.
  Solo puede llamar a `jornada` (DA8).
- **R20.** SI falla la lectura de la tabla, ENTONCES debe usarse el respaldo como no fiable,
  con un WARNING. Las filas leídas se cachean ≤ 60 s.
- **R21.** sv4 no debe bloquear el registro en Sigrid por el calendario en ningún caso
  (DA17): el preflight no lleva `sesame_bloqueo`, `/api/aprobar/ejecutar` y
  `/api/aprobar/encolar` registran o publican cada obra sin override, `forzar_sin_sesame`
  se ignora y ninguna línea nueva se marca `[SIN-SESAME]`. (capa: integración)
- **R22.** CUANDO alguna línea de una obra del preflight no es fiable, su grupo debe llevar
  `aviso_sesame`, pintado como aviso y sin cambiar el título del modal. (capa: integración)
- **R23.** El día de ajuste de F-056 debe calcularse con el calendario resuelto aunque no
  sea fiable (sin el motivo «calendario Sesame no disponible»). (capa: integración)
- **R24.** Las líneas que ya lleven `[SIN-SESAME]` en `sigrid_motivo` deben conservar texto
  y badge en las vistas. (capa: integración)
- **R25.** Los tres avisos degradados (trabajador, obra, «+ Nuevo») y `aviso_sesame` deben
  decir «Sin calendario de Sesame», en vez de «Sesame no disponible». Con Sesame apagado no
  deben salir. (capa: integración)

## E. Festivos por persona en la rejilla de obra (sv4, DA13)

- **R26.** CUANDO sv4 sirve `/obras/{obra_key}`, cada celda debe marcarse como festivo
  (`is_holiday`, `mx-hol`, nombre en `title`) con el calendario del DNI de **su fila**. Una
  fila sin DNI usa el respaldo. (capa: integración)
- **R27.** La cabecera de día solo debe marcar fin de semana y fecha futura, no festivos.
  (capa: integración)
- **R28.** El teñido y el aviso de jornada incompleta de una fila deben usar el mismo
  calendario. El aviso degradado se evalúa sobre (DNI de cada fila × año), sin consultar
  (`None`, año) por la cabecera. Su texto dice «Los festivos marcados en la rejilla y los
  avisos de jornada incompleta…». (capa: integración)

## F. Contraste previo (consola de sv3, DA6 y DA12)

- **R29.** `contrastar_festivos_sesame.py --ano N` debe pedir una vez `GET
  /api/v1/calendarios-festivos` y comparar cada calendario con el JSON de sv3 (consultado
  día a día): días solo-Sesame y solo-respaldo, de lunes a viernes, recuento y si es el
  calendario por defecto.
- **R30.** Debe marcar `INCOMPLETO` (menos de `--festivos-minimos`, por defecto el de
  settings o 1) y `FALTAN DEL RESPALDO` (le falta algún festivo del JSON: la puerta de DA12).
- **R31.** Se configura con `--base-url`/`--api-key` o `SESAME_API_*`, y con `--calendario`.
  Escribe `contraste_festivos_<N>_<YYYYMMDD-HHMM>.md` y `.csv` (UTF-8 con BOM, `;`) en
  `logs/` y sale 0. SI fallan la configuración o el listado, ENTONCES sale ≠ 0 y no escribe.
- **R32.** DONDE se pasa `--impacto`, debe leer en solo lectura las líneas de partes activos
  (`fetch_registros_para_recurso`). Pide los festivos de cada DNI (404 ⇒ respaldo, como R5) y
  clasifica cada línea con horas, fuera de la papelera, en un día que cambia o en una semana
  ISO afectada: `libre`, `reajustable` o `dura` (`clase_linea` y `_congelado` importados).
  Recuentos por año, obra × mes, clase, sentido y días mixtos; un DNI que falla es una fila
  de error; los DNIs, solo en el CSV.
- **R33.** No debe escribir en `partes` ni en Sigrid, ni llamar a sesame-api fuera de `GET`.

## G. Encendido y apagado (`infra/`, DA2 y DA3)

- **R34.** CUANDO el humano ejecuta `infra/add_sesame_partes.ps1`, el script debe, en
  `ca-sv3-persistencia` y luego en `ca-sv4-front`, crear el secreto `sesame-key`
  (`keyvaultref` a `SESAME-API-KEY` por `$MI_ID`) y fijar `SESAME_API_BASE_URL`,
  `SESAME_API_KEY=secretref:sesame-key`, `SESAME_API_TIMEOUT_S` y, solo en sv3,
  `SESAME_FESTIVOS_MINIMOS` (sv4: `SESAME_CACHE_TTL_S`). Idempotente; no encola ni lee claves.
- **R35.** SI `$SESAME_BASE_URL` está vacía o no empieza por `http`, o falta `SESAME-API-KEY`
  en `$KV`, ENTONCES el script debe abortar sin tocar ninguna Container App.
- **R36.** Con `-Quitar`, debe retirar de las dos apps sus variables `SESAME_*`.
- **R37.** El bloque Sesame de `create_capps_partes.ps1` (sv3) debe llevar
  `SESAME_FESTIVOS_MINIMOS` y no `SESAME_CACHE_TTL_S`. `create_sv4_front.ps1` no cambia.
  Ningún fichero versionado debe llevar la URL real, claves ni tokens.

## H. Recálculo de lo ya conciliado (DA7)

- **R38.** Encender no debe recalcular nada por sí solo. CUANDO llega el primer parte de un
  trabajador tras encender, la pasada de esa ingesta debe recalcular con su fila el reparto
  ordinaria/extra de **todas** sus líneas libres de partes activos de ese año. Un día que pasa
  a festivo manda sus ordinarias a extra; uno que deja de serlo las devuelve a ordinarias.
- **R39.** Las líneas congeladas no deben recalcularse. MIENTRAS `REPARTO_REAJUSTE` esté
  encendido, un (recurso, día) con reajustables y alguna libre cuyo ideal cambie debe
  quedar propuesto en `reparto_pendiente` (F-046), sin escribir en Sigrid.

## I. Alcance y documentación

- **R40.** No cambia la jornada teórica (`candef`, mapa, `empleado_jornada`) ni `/jornada`.
- **R41.** `azure-apps/partes.md` (consumo de sesame-api, tabla nueva, variable, script,
  enlace a `sesame-api.md`), `docs/ARCHITECTURE.md` (tabla, herramienta, flujo de festivos,
  fin del bloqueo) e `infra/README_partes.md` deben actualizarse en el mismo trabajo.
- **R42.** La cascada y el formato de `festivos_json` deben vivir en el módulo puro gemelo
  `application/services/festivos_guardados.py` (sv3 y sv4, lista cerrada de `CLAUDE.md`, DA20).
  Un guardián de la raíz se pone rojo si las copias difieren en fuente o festivos.

Verificación manual **M1–M7** (humano): design §7.

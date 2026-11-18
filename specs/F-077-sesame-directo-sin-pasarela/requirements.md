<!-- specs/F-077-sesame-directo-sin-pasarela/requirements.md -->
# F-077 · sv3 lee los festivos de la API oficial de Sesame HR, sin la pasarela sesame-api

Rigor **crítico** (DA4). Toca sv3, sv4, `infra/`, la raíz (guardianes) y docs; `sesame-api` no
se toca (DA2). DA1–DA4 decididas el 2026-11-18; DA5–DA14 abiertas (design §9). Todo lo de
F-032 que no se nombra aquí se conserva: tabla `festivos_trabajador`, refresco al ingerir,
cascada gemela, portal sin bloqueo y semántica de sus R5–R16 (design §1).

Glosario. **Sesame HR**: la API oficial (`SESAME_BASE_URL`). **Índice**: mapa en memoria de sv3
DNI normalizado → empleado de Sesame. **No encontrado**: DNI ausente de un índice bien cargado
(equivale al 404 de la pasarela). **Fallo**: cualquier otro error (red, plazo, HTTP, cuerpo).
**Corte**: ventana tras un fallo de disponibilidad en la que sv3 no llama a Sesame.

## A. Cliente HTTP de Sesame HR (sv3)

- **R1.** El cliente debe mandar `Authorization: Bearer <token>` y `Accept: application/json`
  en cada petición, y solo peticiones `GET` a `SESAME_BASE_URL` más la ruta.
- **R2.** Los listados deben paginarse con `limit` (100) y `page` (desde 1) hasta
  `meta.lastPage` (ausente ⇒ 1); un `data` objeto cuenta como lista de uno. SI una página
  responde 404 o llega sin datos antes de `lastPage`, o se supera el tope de filas, ENTONCES es
  fallo (`RuntimeError`), nunca un listado recortado.
- **R3.** CUANDO Sesame responde 429, 500, 502, 503 o 504, el cliente debe reintentar hasta
  `max_reintentos` (2) esperando `Retry-After` en segundos (tope 30 s; ausente o no numérico ⇒
  `1 + intento`). Un error de red reintenta con `1 · (intento + 1)` s. Agotados ⇒
  `SesameNoDisponible`. Las esperas se inyectan: los tests no duermen.
- **R4.** SI la respuesta es 401, 403 u otro 4xx que no sea 404, ENTONCES `SesameNoDisponible`
  sin reintentar. SI el cuerpo no es JSON, ENTONCES `RuntimeError`.
- **R5.** El texto de toda excepción del cliente debe llevar solo el estado HTTP o el tipo del
  error de red y la ruta **sin** query: nunca el cuerpo, los parámetros, la URL ni el token.
- **R6.** `empleados()` debe pedir `GET /core/v3/employees` con `status[in]=active,inactive`
  (DA7) y quedarse por fila solo con `id`, DNI normalizado (`nid`, DA5) y si está activo. Nombre,
  apellidos, email, código y tipo de documento se descartan al leer la fila.
- **R7.** `festivos_de_empleado(id, ano)` debe pedir `GET /schedule/v1/holidays?employeeId=&
  year=` paginado y tomar de cada fila `dayOff.date` y `dayOff.name` (y, si una fila trae lista
  `daysOff`, cada uno de sus días). Descarta filas sin fecha o de otro año y ordena por fecha.
  SI responde 404, ENTONCES es fallo (`RuntimeError`), no «no encontrado» (DA6).
- **R8.** `calendarios_festivos()` debe pedir `GET /schedule/v1/holiday-calendar` paginado y dar
  por calendario `id`, `name`, `default` y los días de `daysOff` (o `dayOff`) con fecha.
- **R9.** El cliente no debe tener ningún método ni llamada que escriba: un guardián falla si
  su módulo o el adaptador usan algo distinto de `GET`, y todos los `MockTransport` de sus tests
  rechazan cualquier otro método.

## B. Índice y festivos por DNI (sv3)

- **R10.** `FestivosSesameHr.festivos(dni, ano)` debe devolver `None` si el DNI normalizado
  (DA5) está vacío o no está en el índice, y si está, la lista `FestivoDia` de su empleado.
  Es el contrato que ya consume `RefrescoFestivos`, que no cambia.
- **R11.** El índice debe construirse una vez por TTL (600 s) y servir a todas las llamadas;
  vive solo en memoria y guarda por DNI únicamente el id y si está activo.
- **R12.** Con DNIs repetidos debe quedarse el empleado activo y, a igualdad, el primero; las
  filas sin DNI se omiten. El log de construcción da solo recuentos (empleados, duplicados,
  sin DNI, páginas).
- **R13.** SI falla cualquier página del índice (R2–R4) o salen
  0 empleados, ENTONCES el índice no se guarda y la llamada es fallo (DA8). La siguiente
  llamada fuera del corte lo vuelve a intentar.
- **R14.** CUANDO falla el índice o una llamada de festivos acaba en `SesameNoDisponible`, las
  llamadas de los 60 s siguientes deben fallar con `SesameNoDisponible` sin tocar la red (DA8).
  Un 404 de festivos o un cuerpo ilegible de un empleado no abren el corte.
- **R15.** CUANDO sv3 ingiere un parte con Sesame cableado, el pipeline real con el adaptador
  real sobre `MockTransport` debe dar lo de F-032: lista buena ⇒ upsert; no encontrado ⇒ sin
  fila ni revisión; fallo con fila ⇒ se conserva; fallo sin fila ⇒ `review_required`; las
  pasadas de `conciliar_todos` no hacen ninguna petición. (capa: integración)

## C. Configuración y cableado de sv3

- **R16.** sv3 debe leer `SESAME_BASE_URL`, `SESAME_TOKEN`, `SESAME_TIMEOUT_S` (10) y
  `SESAME_FESTIVOS_MINIMOS` (como F-032). `sesame_enabled` exige URL y token no en blanco.
  SI `SESAME_BASE_URL` tiene valor y no empieza por `https://`, ENTONCES sv3 no arranca (DA14).
- **R17.** El log de arranque debe decir `[sesame][wiring] CABLEADO base_url=… token_len=…
  festivos_minimos=… festivos=tabla` o `DESACTIVADO (faltan SESAME_BASE_URL/SESAME_TOKEN)`;
  nunca el token.

## D. Privacidad

- **R18.** Con la `configure_logging` REAL de sv3 en INFO, el cliente y el adaptador reales
  sobre `MockTransport` y `RefrescoFestivos` (índice en dos páginas; 200; no encontrado; 404 de
  festivos; 429 seguido de 200; 500 agotado; error de red; 401), ningún registro, fichero de
  log ni texto de excepción debe contener DNI (crudo o normalizado), nombre, apellido, email,
  token ni id de empleado; `httpx` queda en WARNING. (capa: integración)
- **R19.** Del listado de empleados no debe guardarse nada fuera de memoria: ni tabla, ni
  columna, ni fichero, ni caché en disco. Lo persistido sigue siendo la fila de F-032.

## E. sv4 deja de llamar a Sesame (DA1, DA9, DA10)

- **R20.** sv4 no debe tener cliente de Sesame (`infrastructure/sesame/` retirado) ni leer
  `SESAME_API_*` ni `SESAME_CACHE_TTL_S` (si siguen en un `.env`, se ignoran). Un guardián
  falla si su código de producción importa `infrastructure.sesame` o nombra `SESAME_TOKEN`.
- **R21.** DONDE `FESTIVOS_SESAME_ENABLED` es verdadera, `CalendarioProvider` debe resolver con
  la cascada de F-032 (sus R18 y R20: `sesame`, `sin_fila`, `respaldo`, caché ≤ 60 s);
  si es falsa (defecto), fuente `sin_sesame` sin leer la tabla. Log `[sesame][wiring]
  CABLEADO festivos=tabla` o `DESACTIVADO`. (capa: integración)
- **R22.** La vista de trabajador no debe pedir ni pintar la jornada del contrato de Sesame
  (badge «contrato:» y aviso de divergencia fuera); KPI y avisos de jornada siguen con el
  candef, con los mismos números que hoy. (capa: integración)
- **R23.** `validar_datos_sesame.py` (F-013) y su test se retiran (DA9).

## F. Herramienta de contraste (sv3)

- **R24.** `contrastar_festivos_sesame.py --ano N` debe listar una vez los calendarios con R8 y
  contrastarlos como F-032 (sus R29–R30 sin cambios: días, `INCOMPLETO`, `FALTAN DEL RESPALDO`).
- **R25.** La URL sale de `--base-url` o `SESAME_BASE_URL` (solo `https://`); el token, solo de
  `SESAME_TOKEN` (entorno o `.env` de sv3) o pedido por consola sin eco; no hay `--token` ni
  `--api-key` (DA12). SI falta la URL o el token queda vacío, ENTONCES sale ≠ 0 sin escribir.
- **R26.** Con `--impacto`, los festivos de cada DNI deben salir de R10: no encontrado ⇒
  respaldo; fallo ⇒ fila de error. El Markdown no lleva DNIs; ningún informe lleva nombres ni
  emails. Sin escrituras en `partes` ni en Sigrid y solo `GET` (R9).

## G. Encendido y apagado (`infra/`)

- **R27.** `add_sesame_partes.ps1` debe, en `ca-sv3-persistencia`, crear el secreto
  `sesame-token` (`keyvaultref` a `SESAME-TOKEN` por `$MI_ID`) y fijar `SESAME_BASE_URL`,
  `SESAME_TOKEN=secretref:sesame-token`, `SESAME_TIMEOUT_S` y `SESAME_FESTIVOS_MINIMOS`; después,
  en `ca-sv4-front`, solo `FESTIVOS_SESAME_ENABLED=true`, sin secreto. Retira de cada app las
  retiradas que tenga (`SESAME_API_BASE_URL`, `SESAME_API_KEY`, `SESAME_API_TIMEOUT_S`,
  `SESAME_CACHE_TTL_S`). Idempotente; espera a la revisión lista.
- **R28.** SI `$SESAME_BASE_URL` está vacía o no empieza por `https://`, o falta `SESAME-TOKEN`
  en `$KV`, ENTONCES aborta sin tocar ninguna Container App.
- **R29.** Con `-Quitar` debe retirar de sv3 sus cuatro `SESAME_*` y de sv4
  `FESTIVOS_SESAME_ENABLED`, más las retiradas de R27, **solo las que la app tenga**.
- **R30.** `create_capps_partes.ps1` (sv3) y `create_sv4_front.ps1` (sv4) deben cablear lo mismo
  que R27 cuando `$SESAME_BASE_URL` tiene valor; `add_secrets_partes.ps1` pide `SESAME-TOKEN` y
  no `SESAME-API-KEY`; `00_vars_partes.ps1` deja la URL vacía (DA13). Ningún `.ps1` versionado
  lleva URL de Sesame, token ni clave; los `.ps1` tocados, CRLF sin BOM.

## H. Límites y documentación

- **R31.** Ningún código de producción de sv3 ni sv4 debe nombrar la pasarela (`x-api-key`,
  `/api/v1/festivos`, `/api/v1/jornada`, `/api/v1/calendarios-festivos`, `SESAME_API_`).
- **R32.** No cambian (salvo docstrings) `festivos_trabajador`, `festivos_guardados.py` (su
  guardián sigue verde), `RefrescoFestivos`, `TablaCalendarioLaboral`, `recurso_conciliador.py`
  ni la jornada (candef).
- **R33.** `CLAUDE.md` (los clientes `infrastructure/sesame/` salen de la lista cerrada; queda
  `festivos_guardados.py`), `harness/servicios.json` (sv3 deja de depender del cliente de sv4),
  `docs/ARCHITECTURE.md`, `infra/README_partes.md`, `README.md` y `azure-apps/partes.md` deben
  actualizarse en el mismo trabajo.

Verificación manual **M0–M6** (humano): design §7.

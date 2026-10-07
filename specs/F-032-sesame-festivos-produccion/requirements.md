<!-- specs/F-032-sesame-festivos-produccion/requirements.md -->
# F-032 · Activar Sesame en producción: festivos de cada trabajador

Humano, 2026-10-06. Rigor **estándar** (design §9, DA10). Toca **sv3**,
**sv4**, `infra/` y documentación; **sesame-api es otro repositorio** y su
despliegue lo hace el humano (design §2). Decisiones abiertas DA1–DA10 en
design §8: **a aprobar antes de implementar**.

Punto de partida (verificado en el código, design §1): la integración de F-003
ya existe y está **apagada** porque faltan `SESAME_API_*`. Encendida, cada
servicio pregunta a sesame-api los festivos por (DNI × año) con caché de 6 h y,
si falla, cae a caché caducada o al respaldo local (sv3: `calendario_laboral.json`
= nacionales + 28-feb; sv4: librería `holidays`, subdivisión `MD`), y entonces
sv3 marca el parte `review_required` y sv4 avisa en la vista y **bloquea el
registro** salvo override `[SIN-SESAME]` (R22–R26 de F-003).

Glosario. **Calendario incompleto**: respuesta de Sesame a un (DNI × año), o
al calendario por defecto, con menos festivos de ese año que el mínimo
`SESAME_FESTIVOS_MINIMOS`. **Día que cambia**: día L–V que es festivo con
Sesame y laborable con el respaldo de sv3, o al revés. **Congelada**: línea
para la que `esta_congelado` (sv3) es verdadero (parte aprobado, o
`sigrid_estado` `encolado`/`registrado`/`dedicacion`).

## A. Calendario incompleto ⇒ resolución degradada (sv3 y sv4, DA5)

- **R1.** El `SesameApiClient` de sv3 y el de sv4 deben aceptar el parámetro
  `festivos_minimos` (entero ≥ 0; por defecto 0, que no controla nada).
- **R2.** SI `festivos(dni, ano)` recibe respuesta 2xx con menos de
  `festivos_minimos` festivos de ese año y `festivos_minimos` > 0, ENTONCES
  el cliente debe lanzar `CalendarioIncompletoError` (subclase de
  `RuntimeError`) con el año y el recuento, sin DNI ni nombres en el mensaje.
- **R3.** SI `calendario_por_defecto(ano)` encuentra el calendario
  `por_defecto` con menos de `festivos_minimos` festivos de ese año (y el
  mínimo > 0), ENTONCES debe lanzar `CalendarioIncompletoError`.
- **R4.** CUANDO sesame-api responde 404 a un DNI o no hay calendario por
  defecto, el cliente debe devolver `None` como hoy: el mínimo no aplica.
- **R5.** sv3 y sv4 deben leer `SESAME_FESTIVOS_MINIMOS` (entero ≥ 0, por
  defecto 8; variable **espejo**, mismo nombre y defecto en los dos) y su
  cableado debe pasarlo al cliente; el log `[sesame][wiring] CABLEADO` debe
  incluir el valor. SI el valor es negativo o no entero, el servicio no debe
  arrancar.
- **R6.** CUANDO el cómputo de extras de sv3 evalúa un día de un trabajador
  cuyo calendario es incompleto, sv3 debe resolver ese día con la cascada
  degradada existente (caché caducada o JSON) y dejar el parte
  `review_required=true` (R26 de F-003), sin pedirle a Sesame el calendario
  por defecto para ese DNI.
- **R7.** CUANDO sv4 resuelve el calendario de un trabajador cuyo calendario
  es incompleto, la resolución debe ser no fiable: aviso en la vista (R22 de
  F-003) y `fiable_para` falso, que bloquea el registro salvo override (R23–R25).
- **R8.** Los dos clientes deben ser idénticos salvo el docstring de módulo, y
  un test guardián de la raíz debe ponerse rojo si divergen (lista cerrada de
  `CLAUDE.md`: clientes `infrastructure/sesame/`).
- **R9.** `validar_datos_sesame.py` (F-013) no debe cambiar de comportamiento:
  construye el cliente sin mínimo.

## B. Contraste previo al encendido (herramienta de consola de sv3, DA6)

- **R10.** CUANDO se ejecuta `services/partes-persistencia/
  contrastar_festivos_sesame.py --ano N`, el sistema debe pedir una vez
  `GET /api/v1/calendarios-festivos` y, por cada calendario, comparar sus
  festivos del año N con los del respaldo de sv3 (`JsonCalendarioLaboral`,
  sin DNI), listando los días solo-Sesame y solo-respaldo, cuáles caen de
  lunes a viernes, el número de festivos y si es el calendario por defecto.
- **R11.** CUANDO un calendario tiene menos festivos del año que
  `--festivos-minimos` (por defecto `SESAME_FESTIVOS_MINIMOS` o 8), el
  informe debe marcarlo `INCOMPLETO`.
- **R12.** La herramienta debe configurarse con `--base-url`/`--api-key` o
  `SESAME_API_BASE_URL`/`SESAME_API_KEY`, y `--calendario` (ruta del JSON;
  por defecto la de `CALENDARIO_LABORAL_PATH`); sin `--impacto` no debe
  tocar la BBDD.
- **R13.** La herramienta debe escribir `contraste_festivos_<N>_<YYYYMMDD-HHMM>.md`
  y su `.csv` (UTF-8 con BOM, `;`) en `services/partes-persistencia/logs/`,
  carpeta ignorada por git, y salir con código 0.
- **R14.** SI falla la configuración o el listado de calendarios, ENTONCES
  debe salir con código ≠ 0 y un mensaje, sin escribir informe.
- **R15.** DONDE se pasa `--impacto`, la herramienta debe leer en solo lectura
  las líneas activas de la base `partes` con el método existente
  `fetch_registros_para_recurso` (sin SQL nuevo), pedir los festivos de cada
  DNI distinto de los años presentes (404 ⇒ calendario por defecto) y
  clasificar cada línea con horas ≠ 0 en un día que cambia como
  `recalculable` o `congelada` según `esta_congelado`, sin copiar esa regla.
- **R16.** El informe de impacto debe dar recuentos por año, obra × mes,
  clase (`recalculable`/`congelada`) y sentido del cambio (pasa a festivo /
  deja de serlo), los años sin calendario o con calendario incompleto, y
  ningún nombre de persona; los DNIs solo en el CSV de `logs/`.
- **R17.** SI falla la consulta de un DNI, ENTONCES esa persona debe salir
  como fila de error del informe y el barrido debe continuar.
- **R18.** La herramienta no debe escribir en la base `partes`, ni en Sigrid,
  ni llamar a sesame-api fuera de `GET`.

## C. Encendido y apagado (`infra/`, DA2 y DA3)

- **R19.** CUANDO el humano ejecuta `infra/add_sesame_partes.ps1` con
  `$SESAME_BASE_URL` no vacía, el script debe, en `ca-sv3-persistencia` y
  `ca-sv4-front`, crear el secreto de la app `sesame-key` como `keyvaultref`
  al secreto `SESAME-API-KEY` de `$KV` por la identidad `$MI_ID`, y fijar
  `SESAME_API_BASE_URL`, `SESAME_API_KEY=secretref:sesame-key`,
  `SESAME_API_TIMEOUT_S`, `SESAME_CACHE_TTL_S` y `SESAME_FESTIVOS_MINIMOS`
  con el mismo valor en los dos. Debe ser idempotente.
- **R20.** SI `$SESAME_BASE_URL` está vacía o no empieza por `http`, o falta
  el secreto `SESAME-API-KEY` en `$KV`, ENTONCES el script debe abortar sin
  tocar ninguna Container App.
- **R21.** CUANDO se ejecuta con `-Quitar`, el script debe quitar las cinco
  variables `SESAME_*` de sv3 y sv4 (vuelta al comportamiento apagado).
- **R22.** Los bloques Sesame de `create_capps_partes.ps1` y
  `create_sv4_front.ps1` deben incluir `SESAME_FESTIVOS_MINIMOS` con el mismo
  valor que `add_sesame_partes.ps1`.
- **R23.** Ningún fichero versionado debe contener la URL real de sesame-api,
  su clave ni su token; el script no debe imprimir valores de secretos.

## D. Recálculo de lo ya conciliado (DA7)

- **R24.** MIENTRAS Sesame esté cableado, la siguiente pasada de
  `conciliar_todos` de sv3 debe recalcular con el calendario de cada
  trabajador el reparto ordinaria/extra de **todas** las líneas no congeladas
  de partes activos: en un día que pasa a festivo, sus horas ordinarias pasan
  a extra (con `HE%`); en uno que deja de serlo, vuelven a ordinarias.
- **R25.** Las líneas congeladas no deben recalcularse ni marcarse; su único
  rastro es el informe de R15–R16.

## E. Alcance y documentación

- **R26.** La feature no debe cambiar la jornada teórica: el `candef`, el mapa
  `JORNADA_SEMANAL_POR_CANDEF` y `empleado_jornada` siguen mandando (F-011
  fuera; Sesame tiene 0 contratos).
- **R27.** `azure-apps/partes.md` debe quedar actualizado en el mismo trabajo:
  consumo de sesame-api (estado, variable nueva, script de encendido y
  apagado, calendario incompleto, precondiciones) y un enlace a
  `azure-apps/sesame-api.md`, sin duplicar su contenido.
- **R28.** `docs/ARCHITECTURE.md` (herramientas de consola) e
  `infra/README_partes.md` deben listar la herramienta de B y el script de C.
- **R29.** Ningún log nuevo debe escribir `SESAME_API_KEY` (solo su longitud).

## F. Verificación manual (humano, design §7)

- **M1–M7**: despliegue de sesame-api, contraste, impacto, redespliegue
  apagado, encendido, comprobación en el portal y apagado de prueba.

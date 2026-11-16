<!-- specs/F-032-sesame-festivos-produccion/requirements.md -->
# F-032 · Activar Sesame en producción: festivos de cada trabajador

Spec del 2026-10-06, **refrescada el 2026-11-16** contra `dev` (`95982ac`). Rigor
**estándar** (DA10). Toca **sv3**, **sv4**, `infra/` y documentación; sesame-api es
otro repositorio y lo despliega el humano (design §2). El humano decidió DA1–DA10 el
2026-11-16 (DA5 = mínimo **1**, no 8); DA11–DA13 son nuevas (design §9).

Punto de partida (design §1): la integración de F-003 existe y está **apagada**.
Encendida, sv3 y sv4 piden a sesame-api los festivos por (DNI × año) con caché de 6 h
y, si falla, caen a caché caducada o al respaldo (sv3: `calendario_laboral.json` =
nacionales + 28-feb; sv4: `holidays` `MD`); sv3 marca el parte `review_required` y sv4
avisa y **bloquea el registro** salvo override `[SIN-SESAME]` (R22–R26 de F-003).

Glosario. **Calendario incompleto**: respuesta de Sesame a un (DNI × año), o al
calendario por defecto, con menos festivos de ese año que `SESAME_FESTIVOS_MINIMOS`
(por defecto 1: un calendario con 0 festivos del año). **Día que cambia**: día L–V
festivo con Sesame y laborable con el respaldo de sv3, o al revés. **Semana
afectada**: semana ISO con algún día que cambia (puede mover el último laborable,
F-015). **Congelada**: línea para la que la regla del conciliador (`_congelado`:
`esta_congelado` o `congelada_por_pareja`) es verdadera.

## A. Calendario incompleto ⇒ resolución degradada (sv3 y sv4, DA5)

- **R1.** Los `SesameApiClient` de sv3 y sv4 deben aceptar `festivos_minimos` (entero
  ≥ 0; por defecto 0, que no controla nada).
- **R2.** SI `festivos(dni, ano)` recibe un 2xx con menos de `festivos_minimos`
  festivos de ese año y el mínimo es > 0, ENTONCES debe lanzar
  `CalendarioIncompletoError` (subclase de `RuntimeError`) con año y recuento, sin DNI
  ni nombres en el mensaje.
- **R3.** SI `calendario_por_defecto(ano)` encuentra el calendario `por_defecto` con
  menos festivos del año que el mínimo (> 0), ENTONCES debe lanzar
  `CalendarioIncompletoError`.
- **R4.** CUANDO sesame-api responde 404 a un DNI o no hay calendario por defecto, el
  cliente debe devolver `None` como hoy: el mínimo no aplica.
- **R5.** sv3 y sv4 deben leer `SESAME_FESTIVOS_MINIMOS` (entero ≥ 0, **por defecto
  1**; variable espejo: mismo nombre y defecto en los dos) y pasarlo al cliente; el log
  `[sesame][wiring] CABLEADO` debe incluir `festivos_minimos=`. SI el valor es negativo
  o no entero, el servicio no debe arrancar.
- **R6.** CUANDO el cómputo de extras de sv3 evalúa un día de un trabajador con
  calendario incompleto, debe resolverlo con la cascada degradada existente (caché
  caducada o JSON) y dejar el parte `review_required=true`, sin pedir el calendario por
  defecto para ese DNI.
- **R7.** CUANDO sv4 resuelve un calendario incompleto, la resolución debe ser no
  fiable: aviso en la vista y `fiable_para` falso (bloqueo salvo override).
- **R8.** Los dos clientes deben ser idénticos salvo el docstring de módulo, y
  `SESAME_FESTIVOS_MINIMOS` debe tener el mismo defecto en los dos `settings.py`; un
  test guardián de la raíz debe ponerse rojo si divergen.
- **R9.** `validar_datos_sesame.py` (F-013) no debe cambiar: construye el cliente sin
  mínimo.

## B. Festivos por persona en la rejilla de obra (sv4, DA13)

- **R10.** CUANDO sv4 sirve `/obras/{obra_key}`, cada celda debe marcarse festivo
  (`is_holiday`, clase `mx-hol`) con el calendario del DNI de **su fila** (fila sin DNI
  ⇒ calendario por defecto), y su `title` debe incluir el nombre del festivo: el mismo
  día puede ser festivo para una fila y laborable para otra. (capa: integración)
- **R11.** La cabecera de día de la rejilla de obra no debe marcar festivos (ni
  `mx-hol` ni nombre en el `title`): solo fin de semana y fecha futura. (capa: integración)
- **R12.** El teñido de la celda y el aviso de jornada incompleta de una fila deben
  usar el mismo calendario (el de su DNI); `get_obra` no debe consultar el calendario
  por defecto para filas con DNI. (capa: integración)
- **R13.** El aviso degradado de obra debe evaluarse sobre los (DNI de cada fila ×
  año del periodo), sin la consulta (`None`, año) que hoy añade la cabecera, y decir
  «Los festivos marcados en la rejilla y los avisos de jornada incompleta salen del
  respaldo local…». (capa: integración)

## C. Contraste previo al encendido (consola de sv3, DA6)

- **R14.** CUANDO se ejecuta `services/partes-persistencia/contrastar_festivos_sesame.py
  --ano N`, debe pedir una vez `GET /api/v1/calendarios-festivos` y, por calendario,
  comparar sus festivos del año N con el respaldo de sv3 (`JsonCalendarioLaboral`, sin
  DNI): días solo-Sesame y solo-respaldo, cuáles caen L–V, recuento y si es el por defecto.
- **R15.** El informe debe marcar `INCOMPLETO` el calendario con menos festivos del año
  que `--festivos-minimos` (por defecto `SESAME_FESTIVOS_MINIMOS` o 1) y `FALTAN DEL
  RESPALDO` el que no traiga algún festivo del respaldo (nacionales y 28-feb) (DA12).
- **R16.** Debe configurarse con `--base-url`/`--api-key` o `SESAME_API_BASE_URL`/
  `SESAME_API_KEY`, y `--calendario` (por defecto `CALENDARIO_LABORAL_PATH`); sin
  `--impacto` no debe construir repositorio ni tocar la BBDD.
- **R17.** Debe escribir `contraste_festivos_<N>_<YYYYMMDD-HHMM>.md` y su `.csv`
  (UTF-8 con BOM, `;`) en `services/partes-persistencia/logs/` (ignorada por git) y salir 0.
- **R18.** SI falla la configuración o el listado de calendarios, ENTONCES debe salir
  con código ≠ 0 y un mensaje, sin escribir informe.
- **R19.** DONDE se pasa `--impacto`, debe leer en solo lectura las líneas de partes
  activos con `fetch_registros_para_recurso` (sin SQL nuevo), pedir los festivos de
  cada DNI distinto en los años presentes (404 ⇒ por defecto) y clasificar cada línea
  con horas ≠ 0, fuera de la papelera, en un día que cambia o en una semana afectada
  como `libre`, `reajustable` o `dura` con `clase_linea` (F-046) sobre `_congelado`,
  importadas, sin copiar ninguna regla.
- **R20.** El informe de impacto debe dar recuentos por año, obra × mes, clase, sentido
  (pasa a festivo / deja de serlo / semana afectada) y días mixtos (libre y reajustable
  en el mismo DNI × día: candidatos a propuesta de F-046), los años sin calendario o
  incompletos, y ningún nombre; los DNIs solo en el CSV de `logs/`.
- **R21.** SI falla la consulta de un DNI, ENTONCES esa persona debe salir como fila de
  error y el barrido debe continuar.
- **R22.** La herramienta no debe escribir en `partes` ni en Sigrid, ni llamar a
  sesame-api fuera de `GET`.

## D. Encendido, apagado y pasada de sv3 (`infra/`, DA2, DA3 y DA11)

- **R23.** CUANDO el humano ejecuta `infra/add_sesame_partes.ps1` con
  `$SESAME_BASE_URL` no vacía, el script debe, en este orden: en `ca-sv3-persistencia`
  crear el secreto `sesame-key` (`keyvaultref` a `SESAME-API-KEY` de `$KV` por
  `$MI_ID`) y fijar `SESAME_API_BASE_URL`, `SESAME_API_KEY=secretref:sesame-key`,
  `SESAME_API_TIMEOUT_S`, `SESAME_CACHE_TTL_S` y `SESAME_FESTIVOS_MINIMOS`; esperar a
  que su revisión nueva esté lista; pedir una pasada (R26); y repetir lo primero en
  `ca-sv4-front` con los mismos valores. Debe ser idempotente.
- **R24.** SI `$SESAME_BASE_URL` está vacía o no empieza por `http`, o falta
  `SESAME-API-KEY` en `$KV`, ENTONCES debe abortar sin tocar ninguna Container App.
- **R25.** CUANDO se ejecuta con `-Quitar`, debe quitar las cinco `SESAME_*` de sv3 y
  sv4 y pedir la pasada (motivo `apagado_sesame`).
- **R26.** `infra/pedir_recalculo_partes.py` debe encolar en `q-persistencia` UN mensaje
  `{"tipo": "recalcular", "motivo": <encendido_sesame|apagado_sesame>, "document_id":
  null, "solicitado_por", "solicitado_at_utc"}` que el `clasificar` de sv3 trate como
  recálculo (test de contrato de la raíz); SI encolar falla, el `.ps1` debe avisar con
  el comando para repetirlo y seguir, sin deshacer el cambio de variables.
- **R27.** Los bloques Sesame de `create_capps_partes.ps1` y `create_sv4_front.ps1`
  deben incluir `SESAME_FESTIVOS_MINIMOS` con el valor de `00_vars_partes.ps1`.
- **R28.** Ningún fichero versionado debe contener la URL real de sesame-api, su clave,
  su token ni la clave de la storage; los scripts no deben imprimir secretos.

## E. Recálculo de lo ya conciliado (DA7)

- **R29.** Encender no debe recalcular nada por sí solo (sv3 escala a 0); la primera
  pasada de `conciliar_todos` tras el encendido (la de R26 o la de cualquier ingesta o
  recálculo de sv4) debe recalcular con el calendario de cada trabajador el reparto
  ordinaria/extra de todas las líneas libres de partes activos: día que pasa a festivo
  ⇒ sus ordinarias pasan a extra; que deja de serlo ⇒ vuelven a ordinarias.
- **R30.** Las líneas congeladas no deben recalcularse. MIENTRAS `REPARTO_REAJUSTE`
  esté encendido, un (recurso, día) con reajustables y alguna libre cuyo reparto ideal
  cambie debe quedar propuesto en `reparto_pendiente` (F-046) sin escribir en Sigrid
  hasta que el humano pulse «Aplicar»; sin libres, el día no se propone.

## F. Alcance y documentación

- **R31.** La feature no debe cambiar la jornada teórica (`candef`,
  `JORNADA_SEMANAL_POR_CANDEF`, `empleado_jornada`); F-011 fuera (0 contratos).
- **R32.** `azure-apps/partes.md` debe actualizarse en el mismo trabajo: consumo de
  sesame-api (estado, variable nueva, scripts, calendario incompleto, precondiciones),
  motivos `encendido_sesame`/`apagado_sesame` y enlace a `sesame-api.md` sin duplicarlo.
- **R33.** `docs/ARCHITECTURE.md` (herramientas de consola) e `infra/README_partes.md`
  deben listar la herramienta de C y los scripts de D.
- **R34.** Ningún log nuevo debe escribir `SESAME_API_KEY` (solo su longitud).

## G. Verificación manual (humano, design §7)

- **M1–M8**: despliegue de sesame-api, contraste (puerta DA12), impacto, redespliegue
  apagado, encendido con pasada, portal (rejilla por persona), apagado de prueba.

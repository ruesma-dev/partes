<!-- specs/F-003-sesame-festivos-jornada/requirements.md -->
# F-003 · Integración sesame-api: festivos y jornada reales — Requisitos

Notación EARS. Cada R se traduce a >= 1 test con nombre trazable
(`test_f003_rN_...`). Rigor: **critico**.

## Definiciones

- **«Sesame configurado»**: `SESAME_API_BASE_URL` y `SESAME_API_KEY` no
  vacíos en el `Settings` del servicio (propiedad `sesame_enabled`, mismo
  patrón que `sigrid_lookup_enabled`).
- **«Calendario del trabajador»**: los festivos que sesame-api devuelve
  para su DNI normalizado (`GET /api/v1/festivos?dni=&ano=`).
- **«Calendario por defecto»**: el calendario con `por_defecto=true` de
  `GET /api/v1/calendarios-festivos`.
- **«Respaldo»**: la fuente actual de cada servicio — sv4: librería
  `holidays` (`Spain(subdiv=HOLIDAYS_SUBDIV)`) + `HOLIDAYS_EXTRA`;
  sv3: `JsonCalendarioLaboral` (JSON + festivos nacionales).
- **«Día no laborable»**: sábado, domingo o festivo. El fin de semana se
  calcula siempre en local (`weekday() >= 5`); Sesame solo aporta festivos.
- **«Jornada teórica»**: horas ordinarias diarias esperadas. Hoy:
  `candef` si `candef > CANDEF_MINIMO_VALIDO`, si no
  `JORNADA_POR_DEFECTO`/`JORNADA_ORDINARIA_HORAS` (8.0).

## A. Festivos reales en sv4 (portal)

- **R1.** DONDE Sesame está configurado, sv4 debe obtener los festivos de
  cada trabajador desde sesame-api identificándolo por su DNI normalizado,
  con la clave en cabecera `x-api-key`.
- **R2.** CUANDO sv4 calcula los avisos de jornada incompleta (vista
  trabajador y matriz de obra), el sistema debe excluir del aviso los
  fines de semana y los días festivos **según el calendario del trabajador
  evaluado**, no según un calendario global.
- **R3.** CUANDO sv4 pinta el calendario mensual de la vista trabajador,
  DONDE Sesame está configurado, los festivos marcados (punto `cal-fest` y
  su `title`) deben ser los del calendario del trabajador, con el nombre
  del festivo que devuelve Sesame.
- **R4.** SI un trabajador no tiene DNI o sesame-api responde 404 para su
  DNI, ENTONCES sv4 debe usar para él los festivos del calendario por
  defecto (y si este tampoco se puede obtener, el respaldo).
- **R5.** SI sesame-api no responde o falla (error de red, timeout, 5xx,
  respuesta no válida), ENTONCES el sistema debe reutilizar la última
  respuesta cacheada aunque su TTL haya expirado (*stale-while-error*);
  si no existe caché previa debe usar el respaldo, registrando WARNING.
  Ninguna vista del portal debe romperse por un fallo de Sesame.
- **R6.** MIENTRAS una consulta de festivos (DNI × año, o calendario por
  defecto × año) tenga caché vigente (TTL `SESAME_CACHE_TTL_S`, defecto
  21600 s), sv4 no debe repetir la llamada a sesame-api.
- **R7.** DONDE Sesame NO está configurado, sv4 debe comportarse
  exactamente como hoy (respaldo `holidays` + extras), sin ninguna
  llamada de red y con log de wiring `DESACTIVADO`.

## B. Festivos reales en sv3 (cómputo de extras)

- **R8.** DONDE Sesame está configurado, CUANDO el cómputo de extras
  evalúa si un día es no laborable para un grupo (recurso × fecha), sv3
  debe consultar el calendario del trabajador (DNI del registro) a través
  del puerto `CalendarioLaboralPort`, implementado por un nuevo
  `SesameCalendarioLaboral` (finde local + festivos Sesame).
- **R9.** SI sesame-api falla o el DNI no casa, ENTONCES
  `SesameCalendarioLaboral` debe degradar en cascada (caché expirada →
  calendario por defecto → respaldo `JsonCalendarioLaboral`) registrando
  WARNING; la persistencia del parte no debe fallar nunca por Sesame.
- **R10.** DONDE Sesame NO está configurado, sv3 debe seguir usando
  `JsonCalendarioLaboral` exactamente como hoy.

## C. Jornada teórica (contrato)

> sesame-api HOY NO expone la jornada numérica (horas/día ni horas/semana)
> del contrato — solo `tipo` (texto) y `reducida` (heurística). La
> sustitución numérica del `candef` queda condicionada a la petición P1
> del design. Estos requisitos preparan el enchufe y explotan lo que sí
> existe.

- **R11.** sv3 debe obtener la jornada teórica usada por el cómputo de
  extras a través de un resolutor único inyectable (`JornadaResolver`),
  que hoy aplica la regla actual del `candef`; los tests de regresión
  deben fijar esa regla (candef válido → candef; `None`/<=umbral → 8.0).
- **R12.** sv4 debe obtener la jornada teórica de sus tres usos (aviso
  vista trabajador, aviso matriz de obra, `jornada_sugerida` de
  `/api/sigrid/empleados`) del mismo helper único, eliminando las tres
  copias actuales de la regla.
- **R13.** DONDE Sesame está configurado, la vista trabajador debe
  mostrar junto al KPI de jornada el tipo de jornada del contrato
  (`tipo`, `reducida` de `/api/v1/jornada`); SI Sesame no lo puede dar,
  el KPI se muestra como hoy, sin el dato del contrato.
- **R14.** SI Sesame indica `reducida=true` para un trabajador Y la
  jornada teórica aplicada es >= `JORNADA_POR_DEFECTO`, ENTONCES la vista
  trabajador debe mostrar un aviso de posible divergencia entre el
  contrato (jornada reducida) y la jornada aplicada.
- **R15.** MIENTRAS sesame-api no exponga la jornada numérica del
  contrato, el cómputo de extras y los avisos deben producir exactamente
  el mismo resultado numérico que hoy (mismos splits, mismos días
  incompletos) — verificado con tests de regresión sobre casos dorados.

## D. Aviso al registrar horas en festivo/domingo (sv4)

- **R16.** CUANDO el front pide `GET /api/calendario?desde=&hasta=[&dni=]`,
  sv4 debe responder por día `{fecha, laborable, fin_de_semana, festivo,
  festivo_nombre}` usando el proveedor de calendario (del trabajador si
  llega `dni`, si no el por defecto), con las mismas degradaciones
  R4–R5; rango máximo 62 días → 422.
- **R17.** CUANDO en «+ Nuevo» la selección de días incluye festivos o
  domingos, el portal debe marcarlos visualmente en la rejilla y, al
  enviar, pedir una confirmación no bloqueante («N día(s) son
  festivo/domingo — ¿continuar?»); confirmada, el alta procede sin más
  cambios.
- **R18.** CUANDO el preflight de aprobación contiene líneas con horas
  (> 0) en día festivo o domingo, el modal debe añadir un aviso
  informativo por línea afectada (no bloqueante: no altera qué se
  registra).

## E. Transversales

- **R19.** Los unit tests de F-003 no deben tocar red ni BBDD real: el
  cliente Sesame debe aceptar un transporte httpx inyectable
  (`httpx.MockTransport`) y los proveedores deben admitir dobles.
- **R20.** El sistema no debe escribir `SESAME_API_KEY` en ningún log ni
  fichero del repo: los logs de wiring/instanciación registran como mucho
  `key_len`, igual que el cliente Sigrid.
- **R21.** El documento `azure-apps/partes.md` debe quedar actualizado en
  esta misma feature declarando el nuevo consumo de sesame-api (endpoints
  usados, autenticación, degradación). *Verificación documental.*

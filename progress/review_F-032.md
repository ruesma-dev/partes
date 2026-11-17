Revisión incremental desde 85b4c02 (pasada 2, principal): delta 85b4c02..ad98864 (f63c05d, 495caf9..b6e5440)

# F-032 · Review del reviewer: activar Sesame en producción (festivos por trabajador)

- **Veredicto: APPROVED** (pasada principal). Abre `qa-e2e` (N/A) y la pasada de campaña (T27).
- **Pasada 1** (`85b4c02`, CHANGES_REQUESTED). Pidió tres cambios:
  1. R3 en sv3: el DNI salía en claro en el log INFO de httpx;
  2. R3 en sv4: httpx de `/jornada` y el WARNING de `jornada_contrato` con `dni_norm`;
  3. papeleo: los comandos de las M y `spec_aprobada`.

  El resto de la feature quedó revisado y bien en esa pasada, y no se vuelve a leer. El detalle
  está en el commit `ad98864`.
- **Rigor:** `critico`, declarado en `features.json` (DA10 = B). Exige:
  - fase RED;
  - cobertura ≥ 90 % de las líneas cambiadas;
  - mutación exigida: uno por línea, 60 % en [100, 300], semilla 20261030, y cero
    supervivientes sin aceptar;
  - RM1–RM7.
- **Mutación (T27):** sin lanzar, a propósito. Va en la pasada de campaña, después de este
  APPROVED; sus puntos quedan como «pendiente: pasada de evidencias».

## Ejecución

`ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ `ENTORNO LISTO`, exit 0.

| Suite / puerta | Resultado |
|---|---|
| raíz | 2517 passed / 48 skipped |
| sv1 | 74 |
| sv2 | 422 |
| sv3 | 2572 / 2 skipped (+4 nuevos) |
| sv4 | 3889 (+4 nuevos) |
| sv5 | 1628 |
| `PUERTA COBERTURA` | 95.5 % (589/617), umbral 90 % |
| `PUERTA TAMAÑO` | OK |
| `CAPA E2E` | N/A: ningún servicio declara el bloque e2e |

El aviso de `spec_aprobada` ya no sale. Ruff pasa de 1060 a 1063 avisos (ver «Observaciones»).
El diff no toca `harness/rigor.local.json`.

## Qué cambió el delta y cómo se verificó

- **Cambio 1 (R3 en sv3): resuelto.** `services/partes-persistencia/config/logging_config.py` fija
  `logging.getLogger("httpx").setLevel(logging.WARNING)` después de `dictConfig`, como sv5.
  - Repetí la reproducción de la pasada 1 sobre HEAD: misma `configure_logging(…, "INFO")`, el
    cliente real con `MockTransport` y `RefrescoFestivos.refrescar(['12345678Z'], {2026})`. El
    DNI sale **0** veces en la salida (antes salía en la línea `HTTP Request: GET …?dni=…`).
  - Las dos entradas reales llaman a `configure_logging`: `main.py:15` y `main_worker.py:41`.
    El `dictConfig` que aplica después uvicorn (con `disable_existing_loggers=False`) no restaura
    el nivel de httpx.
- **Cambio 2 (R3 en sv4): resuelto.**
  - `services/partes-front/config/logging_config.py` hace lo mismo con httpx.
  - `main.py:77` llama a `configure_logging` antes de `uvicorn.run`.
  - El WARNING de `CalendarioProvider.jornada_contrato` queda solo con `type(exc).__name__`: sin
    `dni_norm` ni `exc!r`, que llevaba la URL y el cuerpo de Sesame. Es el único log con DNI que
    tenía el fichero.
- **Tests nuevos: `tests/test_f032_logs_sin_dni.py`, en sv3 y en sv4.** Usan el cliente REAL, la
  `configure_logging` REAL del servicio en INFO, un handler que captura todos los loggers y
  también leen el fichero de log.
  - sv3: 200, 404 y 500 (cuyo cuerpo repite el DNI), más el nivel efectivo de httpx.
  - sv4: 200, 404, el WARNING de un 500 sin el cuerpo (y con `RuntimeError`), y el nivel de httpx.
  - Restauran el logging al terminar.
  - RED real en `progress/impl_F-032.md`: 4 + 4 fallos, entre ellos la línea de httpx con el DNI.
    Ahora están en verde dentro de las suites.
- **Cambio 3 (papeleo): resuelto.**
  - `progress/current.md` enlaza los comandos de M1–M7 a design §7 y a «Verificaciones manuales
    pendientes» de `impl_F-032.md`.
  - El líder puso `spec_aprobada: "2026-11-17"` (f63c05d).
  - El comentario desfasado de `obra_detail` en `web/app.py` está al día (R27).
- **Alcance.** La enmienda del humano del 2026-11-17 («1 a 3 ok») está anotada en `tasks.md`
  como T32–T34, todas `[x]` y con su commit `F-032 Tn:` (ccc2f32, 0b95cd0, 60f728b). El delta
  toca solo los ficheros que la enmienda declara, más sus tests, `current.md` e `impl`.
- **¿Invalida algo ya aprobado?** No:
  - no cambia ninguna firma pública ni mueve ningún fichero;
  - `calendario_provider.py` solo cambia el texto de un log;
  - el alcance que medirá la campaña gana tres líneas de producción (dos `setLevel` y el log),
    todas cubiertas.

## Checkpoints (estado tras el delta)

- **C1**
  - [x] `init.sh` sin caché, en verde.
  - [x] Ficheros base.
- **C2**
  - [x] Una sola feature activa.
  - [x] Rama correcta.
  - [x] Orden de prioridad.
  - [x] `current.md`.
  - N/A `history.md`: la feature no está `done`.
- **C3**
  - [x] Arquitectura hexagonal.
  - [x] Primera línea con la ruta, también en los 2 tests nuevos.
  - [x] Sin prints de debug, secretos ni dependencias nuevas: la «clave» de los tests es
    literal de prueba y el DNI es sintético.
  - [x] ORM gemelo, byte-idéntico (sin cambios en el delta).
  - [x] Reglas de dominio, R3 incluida (cambios 1 y 2).
- **C3 bis / ter, C4 ter:** N/A. No entran documentos de fuera, no se registra ninguna
  conversación y no hay rutas sensibles.
- **C3 quater** (`azure-apps` `af27d0c`): [x], sin cambios en el delta. El delta no toca lo que
  partes expone ni lo que consume.
- **C4**
  - [x] Trazabilidad: R3 ahora con tests sobre el cliente real.
  - [x] Tests sin red ni BBDD real (`MockTransport`).
  - [x] M1–M7 con sus comandos enlazados desde `current.md`.
  - [x] Dobles: los nuevos tests no usan dobles del cliente; `_Repo` expone `leer_todas` y
    `guardar`, como el real.
- **C4 bis**
  - [x] Rigor declarado.
  - [x] RED real, incluida la de T32.
  - [x] Cobertura 95,5 %.
  - [x] «Evidencias»; la fila de mutantes queda pendiente.
  - [x] Capa e2e N/A, con el motivo impreso.
  - Pendiente de la pasada de evidencias (ni `[ ]` ni N/A): mutación, supervivientes, muertos
    comprobados, tiempo, CAMPAÑA NO VÁLIDA, RM1, RM2, RM5 y RM6.
  - RM7 hecho en la pasada 1: las dos mutaciones de orden del refresco las caza la suite de la
    feature. El delta no toca `persist_parte_pipeline.py`.
- **C5**
  - [x] T1–T26 y T31–T34 `[x]`, con un commit por tarea. T27 está pendiente a propósito; T28–T30
    son manuales del humano.
  - [x] Árbol limpio.
  - [x] `features.json` con el estado y `spec_aprobada`.

## Cobertura: requisito → test

Sin cambios desde la pasada 1, salvo **R3**, que ahora tiene `test_f032_logs_sin_dni.py` en sv3
y en sv4 además de `refresco` y `wiring`.

| Requisito | Tests |
|---|---|
| R1–R2 | `contrato_festivos` y los guardianes F-010/F-015 |
| R4–R10 | `refresco`, `ingesta` |
| R11 | `repositorio` |
| R12–R17 | `wiring`, `tabla_calendario`, `test_f003_r10` |
| R18–R20 | `provider_tabla` |
| R21–R24 | `sin_bloqueo` |
| R25 | `avisos` |
| R26–R28 | `rejilla_obra` |
| R29–R33 | `contraste` |
| R34–R37 | `infra_sesame` |
| R38–R39 | `recalculo` |
| R40 | por el diff |
| R41 | por lectura |
| R42 | `festivos_guardados_gemelos` |

## Para la pasada de campaña (T27)

- Comando: `python -m harness.mutacion --feature F-032`.
- El informe tiene que traer:
  - el SHA completo de HEAD (RM1);
  - la línea base y la media por mutante (RM2);
  - la demostración ejecutable de cada «equivalente» (RM5: reproduciré uno);
  - si se quita una guarda `is None`, la verificación en el origen del dato (RM6).
- La línea base de sv4 ronda los 27 min.

## Observaciones (no bloquean)

- Los dos `test_f032_logs_sin_dni.py` suben ruff de 1060 a 1063: es el orden de imports (I001),
  que `--fix` corrige.
- Se mantiene la de la pasada 1: con Sesame colgado, cada DNI puede tardar 10 s, así que con
  `COLA_VISIBILITY_S = 300` caben unas 25–30 claves por parte. Vigilarlo en M5.

## Automejora (propuesta, no aplicada)

Sigue en pie la de la pasada 1: añadir a `CHECKPOINTS.md` C3 una trampa (4), «una llamada HTTP
nueva con un dato personal en la query exige comprobar el log de httpx en INFO con la
configuración de logging REAL del servicio». Lo ha confirmado esta misma feature: el test con un
cliente falso estaba en verde y el DNI salía igual.

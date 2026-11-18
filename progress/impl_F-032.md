# F-032 · Informe del implementer (`critico`)

Activar Sesame en producción: festivos de cada trabajador leídos de Sesame HR.
Rama `feature/F-032-sesame-festivos-produccion`, T1–T26, T31 y, tras la review 1, T32–T34
hechas, y T27 en la pasada de campaña. Spec: `specs/F-032-sesame-festivos-produccion/`.

## Qué cambió

- **Tabla `festivos_trabajador`** (sv3 y sv4, las dos copias de `orm_models.py`): una fila
  por DNI normalizado × año, con `festivos_json`, `n_festivos` y `leido_en_utc`, y un índice
  único `ux_festivos_trabajador_dni_ano` (R1, R2).
- **Cascada gemela `festivos_guardados.py`** (sv3 = sv4: `del_ano`, `a_json`, `fila_de`,
  `elegir`), que vigila `tests/test_f032_festivos_guardados_gemelos.py`. La fila manda; sin
  fila, cada servicio usa su respaldo (R42).
- **sv3 escribe**. `RefrescoFestivos` (`refresco_festivos.py`) es el único que pide
  festivos a Sesame. Corre al ingerir, antes de `save_parte`, por los años de la semana ISO
  (R4–R10).
  - Un 404 deja al trabajador sin fila.
  - Un fallo, o menos de `SESAME_FESTIVOS_MINIMOS`, conserva la fila; si no la hay, el
    parte va a revisión.
  - Escribe con `SqlAlchemyFestivosRepository` (upsert).
  - `TablaCalendarioLaboral` sustituye a `SesameCalendarioLaboral`, que se retira (R12–R17).
    Tiene una caché de ≤ 60 s que el refresco invalida.
- **sv4 lee**. `CalendarioProvider` lee la tabla entera mediante `list_festivos_trabajador`
  y añade `fuente_para`. A Sesame solo le pide la jornada (R18–R20).
- **Fin del bloqueo `[SIN-SESAME]`** (DA17 = B, R21–R24):
  fuera `sesame_bloqueo`, el 422, `forzar_sin_sesame` y las marcas nuevas; el preflight lleva
  `aviso_sesame`; el ajuste de F-056 se decide igual; las líneas ya marcadas conservan su badge.
- **Avisos** «Sin calendario de Sesame» en la vista de trabajador, la de obra y «+ Nuevo»
  (R25).
- **Rejilla de obra por persona** (R26–R28, T20/T21):
  `get_obra(holiday_name_de=…)` resuelve cada fila con su DNI (sin DNI, el respaldo);
  `ObraMatrixCell.holiday_name` va al `title`; la cabecera ya no marca festivos; sin `(None, año)`.
- **Herramienta `contrastar_festivos_sesame.py`** (sv3, solo lectura, R29–R33). Contrasta cada
  calendario de Sesame con el respaldo y marca `INCOMPLETO` / `FALTAN DEL RESPALDO`. Con
  `--impacto` cuenta las líneas afectadas. Escribe un Markdown sin DNIs y un CSV.
- **Infra** (R34–R37):
  `infra/add_sesame_partes.ps1` enciende sv3 y después sv4 (secreto `keyvaultref` +
  `identityref`, variables `SESAME_*`, espera a la revisión), valida URL y secreto antes de tocar
  nada y `-Quitar` lo apaga. `create_capps` y `00_vars` llevan `SESAME_FESTIVOS_MINIMOS` (1).
- **Documentación** (R41, R42): `docs/ARCHITECTURE.md` (semántica 23, sesame-api y la
  herramienta), `infra/README_partes.md` y la lista cerrada de `CLAUDE.md`
  (`festivos_guardados.py` y su guardián).

## Ficheros

64 ficheros, +5672/−1476 (`git diff --stat 338b47b..HEAD`). Producción:
- sv3: `application/services/{festivos_guardados,refresco_festivos}.py`, `persist_parte_pipeline.py`,
  `config/settings.py`, `tabla_calendario_laboral.py` (nuevo; `sesame_calendario_laboral.py`
  borrado), `{orm_models,sqlalchemy_festivos_repository}.py`, `api/app.py`, `contrastar_festivos_sesame.py`.
- sv4: `{calendario_provider,festivos_guardados,reparto_obras}.py`, `{orm_models,parte_repository}.py`,
  `resultado_sigrid.py`, `web/app.py`, `static/{app.js,styles.css}`, tres plantillas.
- infra: `add_sesame_partes.ps1` (nuevo), `create_capps_partes.ps1`, `00_vars_partes.ps1`,
  `README_partes.md`.
- Tests nuevos `test_f032_*` en sv3 (11), sv4 (8) y la raíz (3). Enmienda: los dos `logging_config.py`. Tests cambiados: los de T1,
  T11, T12, T14, T16, T18 y T20, más los de la enmienda del 2026-11-17 (`test_f047` r23 y
  `test_f056_vista` r45_r6).
- No se ha tocado ningún fichero de design §6 (verificado con `git diff --stat`).

## Desviaciones (justificadas, ya anotadas en `progress/current.md`)

- **T12.**
  - Quedan menciones a `SesameCalendarioLaboral` en los docstrings de
    `json_calendario_laboral.py` y `sesame_api_client.py` (§6 prohíbe tocarlos).
  - Los tres tests del cliente de sv3 se trasladan a `test_f032_cliente_sesame.py`.
  - `construir_calendario` con Sesame y sin repositorio lanza `ValueError`.
  - `.env.example` se cambió solo en local (no está versionado).
- **T16/T17.**
  - `test_f003_r25_la_marca_se_ve_en_las_vistas` se adapta: siembra la marca (R24).
  - `test_f022_aprobar_seleccion` ya no manda `forzar_sin_sesame`.
  - `motivo_ok` se conserva, con el docstring nuevo.
  - El texto de `AVISO_SESAME` se escribió ya en T17.
- **Enmienda aprobada por el humano el 2026-11-17**: el recuento de app.js baja a 301,
  `test_f056_vista` r45_r6 se reescribe (200, «Ajustar» se decide) y sale el CSS muerto
  (`.ap-sesame-bloqueo`, `.ap-forzar`).
- **T23.** El contraste lista los calendarios con `SesameApiClient._get`, porque el cliente
  no expone el listado y §6 prohíbe tocarlo. `--impacto` cuenta solo las líneas del año
  `--ano`.
- **T21.** El `title` de la celda festiva lleva el prefijo «Festivo: », antes del motivo de
  incompatibilidad y de «Ver parte», unidos con « · ».
- **T26 `azure-apps/partes.md`**: `sesame-api.md` no existe en `azure-apps`: se nombra como
  pendiente (P4), sin enlace. Las precondiciones pasan a las P0–P5 de F-032.
- **Propagación a `arnes-base`**: no aplica. No se ha tocado nada genérico del arnés.

## Documento del ecosistema

`C:\Users\pgris\PycharmProjects\azure-apps\partes.md`. Se hizo `git pull --rebase` antes
(«Already up to date») y otra vez después (al día). Commit aparte **`af27d0c`** en `main`,
**sin push** (el humano ya lo subió, según la review). Cambia §3.4, §4.6, §4.7 nueva
(`festivos_trabajador`), §5.3, §5.3 bis (endpoints, sin bloqueo, variables, P0–P5), §5.4, §5.5 y §8.
La enmienda de la review 1 no cambia nada de lo que exponemos ni consumimos: sin commit nuevo.

## Fase RED (trazas reales; ficheros completos en el scratchpad de la sesión)

Comando base: `python -m pytest <ficheros> -q -p no:cacheprovider`, desde la carpeta del
servicio (la raíz para `tests/`).

- **T1** `tests/test_f010_orm_models_gemelos.py tests/test_f015_r29_guardian_cinco_tablas.py tests/test_f032_contrato_festivos.py` (raíz):
  ```
  E       KeyError: 'festivos_trabajador'
  E       AssertionError: assert 'festivos_trabajador' in ['dedicacion_bandeja', 'empleado_alias', 'empleado_jornada', 'franquicia_ajuste', 'parte_documents', 'parte_registros', ...]
  ```
- **T3** (sv3, sv4 y el guardián):
  ```
  E   FileNotFoundError: [Errno 2] No such file or directory: '...\partes-persistencia\application\services\festivos_guardados.py'
  E   ModuleNotFoundError: No module named 'application.services.festivos_guardados'
  ```
- **T5** `tests/test_f032_repositorio.py` (sv3):
  ```
  E   ModuleNotFoundError: No module named 'infrastructure.database.sqlalchemy_festivos_repository'
  ```
- **T7** `tests/test_f032_refresco.py` (sv3):
  ```
  E   ModuleNotFoundError: No module named 'application.services.refresco_festivos'
  ```
- **T9** `tests/test_f032_ingesta.py` (sv3):
  ```
  E       TypeError: PersistPartePipeline.__init__() got an unexpected keyword argument 'refresco_festivos'
  12 failed, 1 passed in 2.07s
  ```
- **T11** `tests/test_f032_tabla_calendario.py tests/test_f032_wiring.py tests/test_f003_r10_wiring_sv3.py` (sv3):
  ```
  E   ModuleNotFoundError: No module named 'infrastructure.calendario.tabla_calendario_laboral'
  3 errors in 2.97s
  ```
- **T14** `tests/test_f032_provider_tabla.py tests/test_f003_r4_calendario_provider.py` (sv4):
  ```
  E       TypeError: CalendarioProvider.__init__() got an unexpected keyword argument 'leer_festivos'
  E       AttributeError: 'CalendarioProvider' object has no attribute 'fuente_para'. Did you mean: 'fiable_para'?
  36 failed, 1 passed in 1.27s
  ```
- **T16** `tests/test_f032_sin_bloqueo.py` y los adaptados de f003/f017/f022/f056 (sv4):
  ```
  FAILED tests/test_f032_sin_bloqueo.py::test_f032_r21_el_modal_no_tiene_bloqueo_ni_casilla
  FAILED tests/test_f032_sin_bloqueo.py::test_f032_r22_el_grupo_pinta_el_aviso_sesame
  14 failed, 3 passed, 1 warning in 12.30s
  ```
- **T18** `tests/test_f032_avisos.py tests/test_f003_r2_vistas_festivos.py` (sv4):
  ```
  E       assert 'Sin calendario de Sesame' in 'id="cal-aviso" hidden>⚠ El calendario puede no ser exacto: <strong>Sesame no disponible</strong>. Los festivos marcados salen del respaldo local.'
  3 failed, 22 passed, 1 warning in 16.29s
  ```
- **T20** `tests/test_f032_rejilla_obra.py tests/test_f003_r2_vistas_festivos.py` (sv4):
  ```
  FAILED tests/test_f032_rejilla_obra.py::test_f032_r26_cada_fila_con_su_calendario
  FAILED tests/test_f032_rejilla_obra.py::test_f032_r27_la_cabecera_no_marca_festivos
  FAILED tests/test_f032_rejilla_obra.py::test_f032_r28_nunca_se_pide_none_si_todas_las_filas_tienen_dni
  FAILED tests/test_f032_rejilla_obra.py::test_f032_r26_get_obra_con_holiday_name_de
  FAILED tests/test_f003_r2_vistas_festivos.py::test_f003_r2_la_columna_de_la_matriz_usa_el_calendario_por_defecto
  7 failed, 18 passed, 1 warning in 17.63s
  ```
- **T22** `tests/test_f032_contraste.py` (sv3):
  ```
  E   ModuleNotFoundError: No module named 'contrastar_festivos_sesame'
  ```
- **T24** `tests/test_f032_infra_sesame.py` (raíz): `4 failed, 4 passed, 9 errors in 0.43s`.
- **T32** `tests/test_f032_logs_sin_dni.py`, en sv3 y en sv4 (cliente y `configure_logging` reales):
  ```
  E           AssertionError: httpx | HTTP Request: GET http://sesame.local/api/v1/festivos?dni=12345678Z&ano=2026 "HTTP/1.1 200 OK"
  E       AssertionError: assert 20 >= 30      (httpx en INFO)
  4 failed in 1.27s                            (sv3: 200, 404, 500 y el nivel de httpx)
  E           AssertionError: httpx | HTTP Request: GET http://sesame.local/api/v1/jornada?dni=12345678Z "HTTP/1.1 200 OK"
  4 failed in 1.15s                            (sv4: 200, 404, WARNING con el cuerpo, nivel)
  ```

Todas pasan a verde con su tarea (T2, T4, T6, T8, T10, T12, T15, T17, T19, T21, T23, T25, T33).

## Enmienda tras la review 1 (aprobada por el humano el 2026-11-17)

- **T33 (R3)**: `logging.getLogger("httpx").setLevel(logging.WARNING)` en los dos
  `config/logging_config.py` (como sv5). El WARNING de `jornada_contrato` ya solo lleva
  `type(exc).__name__`: ni el DNI ni `exc!r`, que incluye el cuerpo de Sesame.
- **T34**: el comentario del aviso de `obra_detail` en `web/app.py` (R27) está al día, y
  `current.md` enlaza los comandos de M1–M7 a design §7 y a la sección de abajo.
- Lo que cubre: `RefrescoFestivos.refrescar` (200, 404, 500) y `jornada_contrato` (200, 404 y el
  WARNING de un 500 cuyo cuerpo repite el DNI). Sin DNI en ningún registro ni en el fichero de log.

## Salida de `bash harness/init.sh` (2026-11-17, tras T34)

`ENTORNO LISTO. Puedes trabajar.` (exit 0). Raíz `2517 passed, 48 skipped in 2013.00s`;
sv3 `2572 passed, 2 skipped in 94.54s`; sv4 `3889 passed, 2 warnings in 1156.96s`; sv1, sv2 y
sv5 verdes por caché.
- `PUERTA COBERTURA: 95.5% de 617 líneas cambiadas cubiertas (589/617, umbral 90% (del nivel critico)…)`
- `PUERTA TAMAÑO`: dentro de los topes.
- `PUERTA CARRIL: N/A (F-032 es de nivel critico: no declara límites)`
- `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`

## Verificaciones manuales pendientes (humano)

- **P0–P5** en sesame-api y RRHH (design §2).
- **T28 (M1)**: desplegar sesame-api.
- **T29 (M2, M3)**: `python contrastar_festivos_sesame.py --ano 2026 [--impacto]` desde
  `services/partes-persistencia`. `FALTAN DEL RESPALDO` ⇒ no se enciende.
- **T30 (M4–M7)**: redespliegue apagado; `.\add_sesame_partes.ps1`; portal y propuestas de
  F-046; `-Quitar` de prueba; estado en `azure-apps/partes.md`. Comandos: design §7.
- Push de `azure-apps` (`af27d0c`) y de la rama: los hace el humano.

## Pendiente

- **T27 hecha** en la pasada de campaña. El líder lanzó la campaña (`--workers 3`, 8964 s) sobre
  `0e0d2f8`. 32 supervivientes:
  - 18 muertos con tests nuevos (`test_f032_campana.py` de sv3 y de sv4);
  - 11 muertos por `tests/test_f032_contrato_festivos.py` de la raíz, que la campaña no corre (ORM);
  - 3 equivalentes (`None` frente a objetos sin `__bool__`/`__len__`).
  Cada uno se verificó a mano con el mutante aplicado. El indeterminado (`:440`, `__main__`)
  se detecta: la recolección aborta. Detalle: `progress/mutacion_F-032.md`. Queda solo lo manual.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | raíz 2517 passed / 48 skipped; sv3 2586 passed / 2 skipped; sv4 3890 passed; 0 fallos |
| Cobertura de líneas cambiadas | 95,9 % (592/617), umbral 90 % |
| Mutantes generados / supervivientes | 303 generados, 111 evaluados: 78 muertos, 32 supervivientes (todos analizados: 29 muertos a mano, 3 equivalentes), 0 timeouts, 1 indeterminado (detectado) |
| Tiempo de la suite | raíz 1133 s; sv3 54 s; sv4 1072 s; campaña 8964 s |
| Capa e2e | `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |

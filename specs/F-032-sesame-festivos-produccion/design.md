<!-- specs/F-032-sesame-festivos-produccion/design.md -->
# F-032 · Activar Sesame en producción — Diseño

**Rigor: `critico`** (DA10 = B). Disparadores de `CHECKPOINTS.md`: **1** (dinero: el calendario
de `RecursoConciliador` decide qué horas son ordinarias o extra, que se pagan) y **3** (datos
personales: la tabla guarda DNIs). Encendido manual tras M2–M3.

## 1. Estado de partida (verificado el 2026-11-17 en `7a289a4`, solo lectura)

- **Apagada.** sv3 `api/app.py::construir_calendario` (:59): JSON o `SesameCalendarioLaboral`
  (caché 6 h; `consumir_degradacion()` sube partes a revisión). sv4 `CalendarioProvider`, misma
  cascada; `fiable_para` gobierna avisos y el **bloqueo** de F-003 en `web/app.py`
  (`_calendario_fiable` :2683; preflight :3264, ejecutar :3319 con override, encolar :3421;
  `_dia_ajuste` :2908).
- **Esquema.** `orm_models.py` byte-idéntico (guardián F-010, `TABLAS` = 8); `create_all` al
  arrancar sv3 (`sqlalchemy_parte_repository.py:243`) y sv4 (`parte_repository.py:1111`) más
  `ddl_complementario()`, como `franquicia_ajuste`. **Recálculo (DA7)**: `conciliar_todos` tras
  cada ingesta y `recalcular`; sv3 KEDA a 0; con `REPARTO_REAJUSTE`, a `reparto_pendiente`.
- **Respaldos**: sv3 nacionales + `2026-02-28`; sv4 `holidays` `MD`. Siguen así (DA19 = B, §10).

## 2. Límite de servicio y trabajo fuera del repositorio

**sv3**: refresco en la ingesta (único que pide festivos a Sesame), tabla y herramienta.
**sv4**: lectura, rejilla por persona, textos y **retirada del bloqueo** (DA17 = B). **Ambos**:
`orm_models.py` y `festivos_guardados.py` (gemelos). `infra/`, docs, `CLAUDE.md` y
`azure-apps/partes.md`: implementer. **sesame-api** y Azure (P0–P5, M1–M7): **humano**.

**¿Duplicación?** sv4 solo hace un `SELECT` (como `list_jornadas_empleado`). La cascada y el
formato de `festivos_json` sí lo serían: módulo puro gemelo con guardián, en la lista cerrada
de `CLAUDE.md` (DA20 = A; la edición es T26). El mínimo de festivos, solo en sv3.

**Precondiciones en sesame-api (humano, antes de M1; sin cambios):** **P0** `git rm --cached
.env` (y rotar `SESAME_TOKEN` si se publicó); **P1** commitear rediseño y fix `daysOff`; **P2**
Dockerfile y `.dockerignore`; **P3** (DA8) `contract_not_found` ⇒ 404; **P4** `sesame-api.md`; **P5** RRHH.

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-{persistencia,front}/application/services/festivos_guardados.py` | §5.2 (gemelo) |
| `services/partes-persistencia/application/services/refresco_festivos.py` | §5.4 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_festivos_repository.py` | §5.3 |
| `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` | §5.5 |
| `services/partes-persistencia/contrastar_festivos_sesame.py` | §5.8 (consola, `print`) |
| `services/partes-persistencia/tests/test_f032_{festivos_guardados,repositorio,refresco,ingesta,tabla_calendario,wiring,contraste,recalculo}.py` | R2–R17, R29–R33, R38–R39 |
| `services/partes-front/tests/test_f032_{festivos_guardados,provider_tabla,sin_bloqueo,avisos,rejilla_obra}.py` | R18–R28 |
| `tests/test_f032_{festivos_guardados_gemelos,contrato_festivos,infra_sesame}.py` | R42 (patrón `test_f015_r19_…`), R1 (patrón `test_f056_contrato_franquicia`), R34–R37 (estático) |
| `infra/add_sesame_partes.ps1` | §5.9 |

## 4. Ficheros a modificar y a retirar

- **Los dos `orm_models.py`** (mismo commit): §5.1, docstring «NUEVE tablas»; `TABLAS` de
  `test_f010_orm_models_gemelos.py` y `test_f015_r29_guardian_cinco_tablas.py` gana la novena.
- **sv3**: `persist_parte_pipeline.py` (§5.4), `api/app.py` (§5.5), `config/settings.py`
  (`sesame_festivos_minimos: int = Field(1, ge=0)`, fuera `sesame_cache_ttl_s`),
  `test_f003_r10_wiring_sv3.py` (Sesame ⇒ tabla; JSON y log sin clave se quedan). **Se
  retiran** `sesame_calendario_laboral.py`, `test_f003_r8_sesame_calendario.py` y lo que solo
  los servía en `tests/dobles.py` (R17).
- **sv4**: `calendario_provider.py` (§5.6), `parte_repository.py` (`list_festivos_trabajador`,
  §5.7 y docstring de `motivo_ok`), `web/app.py` (`build_app`, `obra_detail`, §5.10),
  `transfer/resultado_sigrid.py` y `application/services/reparto_obras.py` (§5.10), las tres
  plantillas con aviso y `static/app.js` (§5.10).
- **Tests de sv4 que cambian a propósito** (lista cerrada, test a test, en T14, T16, T18 y
  T20; si cae otro, PARAR y volver a la spec): `test_f003_r4_calendario_provider`, `test_f003_r2_
  vistas_festivos`, `test_f003_r23_bloqueo_registro` (quedan los del badge, R24, y los de R27),
  `test_f022_{aprobar_seleccion,reparto_obras,vistas_seleccion}`, `test_f017_aprobacion_firmada`
  (los dos del forzado se retiran) y `test_f056_decisiones`. No cambian `test_f025_aprobacion`
  (`forzar_sin_sesame` se ignora) ni `test_f056_franquicia` (su `motivo` es genérico).
- **infra y docs**: `create_capps_partes.ps1` (R37), `00_vars_partes.ps1`
  (`$SESAME_FESTIVOS_MINIMOS = 1`), `README_partes.md`, `docs/ARCHITECTURE.md`, `CLAUDE.md`
  (lista cerrada), `azure-apps/partes.md`; `harness/features.json` lo anota el líder.

## 5. Clases y funciones

### 5.1 `FestivoTrabajadorOrm` (`festivos_trabajador`, gemelo)

`id` Integer PK autoincrement; `dni_norm` String(32) NOT NULL `""`; `ano` Integer NOT NULL
`"0"`; `festivos_json` Text NOT NULL `"{}"`; `n_festivos` Integer NOT NULL `"0"`;
`leido_en_utc` String(40) NOT NULL `"1970-01-01T00:00:00Z"`; `Index("ux_festivos_trabajador_
dni_ano", "dni_norm", "ano", unique=True)`. Docstring: solo personas que Sesame conoce; DNI =
dato personal; solo sv3 escribe. Sin `is_active` ni `origen` (no hay fila `*` ni 404 guardado).
`create_all` la crea al arrancar; ni SQL a mano ni permisos nuevos.

### 5.2 `application/services/festivos_guardados.py` (puro, gemelo, DA20)

Solo biblioteca estándar (el guardián lo carga por ruta):
```python
FUENTE_SESAME = "sesame"; FUENTE_SIN_FILA = "sin_fila"
@dataclass(frozen=True)
class FilaFestivos: dni_norm: str; ano: int; festivos: Mapping[str, str | None]; leido_en_utc: str
def del_ano(pares, ano) -> dict[str, str | None];  def a_json(festivos) -> str  # claves ordenadas
def fila_de(dni_norm, ano, festivos_json, leido_en_utc) -> FilaFestivos  # ValueError si mal formado
def elegir(dni_norm, ano, leer: Callable[[str, int], FilaFestivos | None]) -> tuple[FilaFestivos | None, str]
```
`elegir` (DA19 = B): DNI no vacío con fila ⇒ `(fila, "sesame")`; si no, `(None, "sin_fila")`
y el llamante usa **su** respaldo actual. Sin DNI no se llama a `leer`. Recibe el DNI ya
normalizado (cada servicio con su `normalize_dni`).

### 5.3 `SqlAlchemyFestivosRepository` (sv3, infrastructure)

`leer_todas() -> dict[(dni_norm, ano), FilaFestivos]` (~220 filas/año; una mal formada se omite
con WARNING por su `id`); `guardar(fila)` con `insert().on_conflict_do_update(index_elements=
["dni_norm", "ano"])` del dialecto (`postgresql`/`sqlite`), que aguanta dos réplicas (R11). Nunca borra.

### 5.4 `RefrescoFestivos` (sv3, application) y la ingesta

`RefrescoFestivos(*, cliente, repositorio, minimo, ahora_utc, al_guardar=lambda: None)` con
`refrescar(dnis, anos) -> ResultadoRefresco(guardadas, conservadas, sin_calendario,
sin_dato)`, y `anos_de_semana(fecha) -> set[int]` (años del lunes y del domingo ISO).
`cliente` y `repositorio` por duck-typing. Por (DNI, año), `festivos(dni, ano)`: lista con
`len(del_ano(...)) >= minimo` ⇒ upsert y `al_guardar()` (caché de §5.5); `None` (404) ⇒
`sin_calendario`, no se escribe ni se borra (R5); excepción, plazo o incompleto ⇒ fallo: con
fila ⇒ `conservadas`; sin ella ⇒ `sin_dato`. **No** llama a `calendario_por_defecto`. Nunca
lanza; log `[festivos] refresco guardadas=… conservadas=… sin_calendario=… sin_dato=…`.

**Pipeline.** `PersistPartePipeline(..., refresco_festivos: Any = None)`. En `run()`, entre
`_compute_review_required` y `save_parte`, `_refrescar_festivos_safely(parte) -> bool` con
`dnis` = `normalize_dni(r.empleado.dni)` no vacíos y `anos` = `anos_de_semana(parte.fecha_iso
or self._hoy())`. `sin_dato > 0` o un error inesperado ⇒ `True` ⇒ `review_required = True` y
WARNING `[festivos] parte <document_id> a revision: N clave(s) sin festivos de Sesame`. Un
`sin_calendario` no marca nada. El duplicado sale antes y no llega aquí (R10).

### 5.5 `TablaCalendarioLaboral` (sv3, infrastructure) y cableado

`TablaCalendarioLaboral(CalendarioLaboralPort)(*, repositorio, respaldo, ttl_s=60, reloj)`:
fin de semana; `elegir(…)` sobre `leer_todas()` (caché ≤ `ttl_s`); `sin_fila` o lectura
fallida (+ WARNING) ⇒ JSON. `olvidar()` vacía la caché. **Sin** `consumir_degradacion` (R16).
`construir_calendario(settings, repositorio=None)` (sin Sesame ⇒ JSON; con él ⇒ la tabla) y
`construir_refresco_festivos(settings, repositorio, calendario) -> RefrescoFestivos | None`
(`SesameApiClient` sin cambios, `minimo = settings.sesame_festivos_minimos`, `al_guardar =
calendario.olvidar`); `build_app` da el mismo `calendario` al conciliador. Log `[sesame][wiring]
CABLEADO base_url=… key_len=… festivos_minimos=… festivos=tabla`.

### 5.6 `CalendarioProvider` (sv4) y cableado

Gana `leer_festivos: Callable[[], Iterable[dict]] | None` y `ttl_tabla_s=60`; `cliente` queda
para `jornada_contrato` e interruptor (`activo`, DA18 = A). `_resolver`: sin cliente ⇒
`sin_sesame` (como hoy); con cliente ⇒ `elegir` sobre la tabla (`fila_de`, caché ≤ 60 s);
`sin_fila` ⇒ `holidays`; lectura fallida ⇒ `respaldo` + WARNING. Fuera las llamadas a
`festivos`/`calendario_por_defecto`, `_degradar` y `default` (R19). `sin_fila` y `respaldo`,
fuera de `FUENTES_FIABLES`: solo avisan. `build_app` pasa `repository.list_festivos_trabajador`
(dicts); log `festivos=tabla`. Texto común (R25): «⚠ El calendario puede no ser exacto: **Sin
calendario de Sesame** para algún trabajador: sus festivos salen del calendario local.»

### 5.7 Rejilla de obra por persona (sv4, DA13)

`get_obra(..., holiday_name_de: Callable[[str | None], Callable[[date], str | None]] | None)`
sustituye a `holiday_name`; se pide una vez por fila y rellena cada celda. `ObraMatrixCell` gana
`holiday_name`; `ObraDayCol` pierde `is_holiday`/`holiday_name`. `obra_detail` pasa
`calendario_provider.holiday_name_para` y el aviso de jornada usa el mismo resolutor; se borra
`_consultas.update((None, ano) …)`. Plantilla: cabecera sin `mx-hol`; celda con `mx-hol` y
nombre en `title`; aviso según R28 y R25.

### 5.8 `contrastar_festivos_sesame.py` (consola, sv3)

Puras `contrastar_calendario` (`del_ano`), `clasificar_impacto` (404 ⇒ JSON), `render_markdown`
y `escribir_csv`; `main(argv)` fino con `--ano --base-url --api-key --calendario
--festivos-minimos --salida --impacto`. Solo lectura; no lee `festivos_trabajador`.

### 5.9 `infra/add_sesame_partes.ps1` (PowerShell 5.1, CRLF, sin BOM)

Tras `00_vars_partes.ps1` y `00_capps_vars_partes.ps1`; solo `[-Quitar]`. Valida R35 antes del
primer `containerapp` (`az keyvault secret show --query id`). En sv3 y luego sv4: secreto
`sesame-key=keyvaultref:$KV_URI/secrets/SESAME-API-KEY,identityref:$MI_ID`, `--set-env-vars`
de R34 y espera a `latestReadyRevisionName == latestRevisionName`; acaba con los logs de §7.
`-Quitar`: `--remove-env-vars` en las dos (el secreto queda inerte). Mismo `Run-Az`.

### 5.10 Retirada del bloqueo `[SIN-SESAME]` (sv4, DA17 = B)

- `web/app.py`: el preflight pone `aviso_sesame` (texto R25) donde ponía `sesame_bloqueo`;
  `ejecutar`/`encolar` ya no miran `_calendario_fiable` ni `forzar_sin_sesame`; fuera
  `MOTIVO_BLOQUEO_SESAME`, `_bloqueado_sesame`, el log «registro FORZADO» y `sin_sesame` de
  `_trazar`; `_dia_ajuste` ya no mira `fiable_para`. `resultado_sigrid.py`: fuera
  `MOTIVO_SIN_SESAME` y `sin_sesame`. `reparto_obras.py`: sin `sesame_bloqueo`/`bloqueado_sesame`.
- `app.js`: fuera `bloqueoSesameHtml`, la casilla `ap-forzar-sesame`, `forzado` de `planEnvio`,
  las ramas de `sesame_bloqueo` y el título «Bloqueado…»; `grupoHtml` pinta `aviso_sesame`.
- **Lo ya marcado** (en producción no debería haber nada: F-003 nunca se encendió): conserva
  su `sigrid_motivo` y el badge de `trabajador_detail`/`obra_detail`, que lee el motivo (R24).

## 6. Ficheros que NO se tocan

`recurso_conciliador.py`, `reajuste_reparto.py`, `congelacion.py`, `jornada_resolver.py`,
`despacho.py`, `mensajes.py`, `recalculo_publisher.py`, `franquicia.py` (sv4), los dos
`sesame_api_client.py`, `json_calendario_laboral.py`, `calendario_laboral.json`, `holiday_provider.py`,
`validar_datos_sesame.py`, `create_sv4_front.ps1`, `redeploy_*.ps1`, `add_secrets_partes.ps1`,
`enqueue_test.py`, sv1, sv2, sv5 y `sesame-api`.

## 7. Guía de despliegue y verificación manual (humano)

Rigor crítico: cada M va a `progress/impl_F-032.md` con su comando exacto y su resultado real.
- **M1** (DA1, tras P0–P2): `az acr build -r acralbaranesdev`; `SESAMEAPI-TOKEN`,
  `SESAMEAPI-API-KEYS` y `SESAME-API-KEY` en `$KV` por consola; `ca-sesame-api` en `$CAE`,
  `--ingress internal --target-port 8006 --min-replicas 1 --max-replicas 1`, identidad
  `$MI_ID`; `/health` desde el entorno; FQDN a `$SESAME_BASE_URL` (`00_vars_partes.local.ps1`).
- **M2 (puerta DA12)**: en `services/partes-persistencia`, `python contrastar_festivos_sesame.py
  --ano 2026 --base-url <url> --api-key <clave>` (y 2025 si hay partes activos); en local,
  `$env:API_PORT="8016"`. `FALTAN DEL RESPALDO` ⇒ no se enciende; `INCOMPLETO` ⇒ RRHH (P5).
- **M3**: lo mismo con `--impacto` y el `.env` de sv3; revisar `dura` y días mixtos. **M4**:
  `.\infra\redeploy_partes.ps1 -Solo sv3,sv4`; «DESACTIVADO»; `festivos_trabajador` vacía.
- **M5**, fuera del horario de aprobación: `.\infra\add_sesame_partes.ps1`; con el siguiente
  parte, `[festivos] refresco guardadas=…`, filas nuevas y la pasada con
  `extras_reclasificadas`/`repartos_propuestos`, sin partes a revisión por festivos. En sv4
  saldrá el aviso para quien aún no tenga fila: esperado, sin bloqueo.
- **M6**: obra con dos calendarios; sin fila ⇒ aviso y registro que pasa; decidir los
  `reparto_pendiente`. **M7** (opcional): `.\infra\add_sesame_partes.ps1 -Quitar` ⇒ «DESACTIVADO».

## 8. Frontera

¿Cruza la frontera del proyecto? **Sí.** sv3 consume **sesame-api** (`festivos` al ingerir; la
herramienta, `calendarios-festivos`) y sv4 solo `/jornada`: servicio interno nuevo en
`cae-partes-dev` (DA1). La base `partes` (propia) gana `festivos_trabajador`; variable nueva
`SESAME_FESTIVOS_MINIMOS` (sv3) y secreto `SESAME-API-KEY`. Se actualiza `azure-apps/partes.md`
(R41); `sesame-api.md` es de su dueño (P4).

## 9. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| DA1 Dónde vive sesame-api | (A) `ca-sesame-api` en `cae-partes-dev`, interno, 1 réplica, secretos en `kv-partes`; (B) externo; (C) propios internos | (A) | (A) 2026-11-16 |
| DA2 Réplicas | (A) min = max = 1; (B) 0–1 | (A) | (A) 2026-11-16 |
| DA3 Encendido | (A) `add_sesame_partes.ps1` con `-Quitar`; (B) recrear las apps | (A) | (A) 2026-11-16; sin pasada; desde DA17 = B, un solo paso para sv3 y sv4 (sin `-Servicio`) |
| DA4 Si Sesame no responde | (A) en la ingesta: lo último guardado; sin fila, JSON + `review_required`; (B) solo respaldo + log | (A) | (A) 2026-11-17 (un 404 no es «no responde»: R5) |
| DA5 Mínimo de festivos | (A) **1** configurable; (B) 8; (C) 0 | (A) | (A) 2026-11-16; solo en sv3 |
| DA6 Contraste | (A) consola en sv3 con `--impacto`; (B) sin herramienta | (A) | (A) 2026-11-16 |
| DA7 Partes ya conciliados | (A) recálculo de lo libre en la siguiente pasada; congelado intacto salvo F-046; (B) solo fechas posteriores | (A) | (A) 2026-11-16 |
| DA8 `/jornada` con 0 contratos | (A) P3 en sesame-api; (B) interruptor en sv4 | (A) | (A) 2026-11-16 |
| DA9 `sesame-api.md` | (A) lo escribe su dueño, `partes.md` enlaza | (A) | (A) 2026-11-16 |
| DA10 Rigor | (A) estándar; (B) crítico | (A) | **(B) 2026-11-17** (disparadores 1 y 3) |
| DA11 Pasada al encender | — | — | **Retirada** 2026-11-17 por DA15 |
| DA12 A Sesame le faltan festivos del respaldo | (A) puerta: no se enciende y se re-decide; (B) encender igual | (A) | (A) 2026-11-17 |
| DA13 Rejilla de obra | (A) celda por persona, cabecera sin festivos; (B) D6 de F-003 | (A) | (A) 2026-11-17 |
| DA14 Persistir los festivos | (A) tabla `festivos_trabajador`, clave DNI + año; (B) solo caché | (A) | (A) 2026-11-17 |
| DA15 Cuándo se lee Sesame | (A) solo al ingerir, con upsert; los recálculos leen la tabla | (A) | (A) 2026-11-17 |
| DA16 sv4 y los festivos | (A) lee la tabla, no llama a Sesame por festivos | (A) | (A) 2026-11-17 |
| DA17 Bloqueo `[SIN-SESAME]` sin fila | (A) se mantiene y sv4 se enciende después; (B) solo aviso; (C) bloqueo con los dos a la vez | (A) | **(B) 2026-11-17**: ningún bloqueo por calendario; el de F-003 se retira (§5.10) |
| DA18 Interruptor de sv4 y jornada | (A) sv4 conserva `SESAME_API_*` (tabla y jornada); (B) variable nueva y jornada apagada | (A) | (A) 2026-11-17 |
| DA19 Respaldo sin fila | (A) fila `*` y luego respaldo local; (B) cada servicio su respaldo actual; (C) sv4 al JSON | (A) | **(B) 2026-11-17**: sin fila ⇒ respaldo de hoy; sin fila `*`; un 404 no guarda nada |
| DA20 Cascada gemela | (A) `festivos_guardados.py` en la lista cerrada de `CLAUDE.md` con guardián; (B) sin guardián | (A) | (A) 2026-11-17 |

## 10. Riesgos y alternativas descartadas

- **Respaldos distintos (conocido, DA19 = B).** Sin fila (sin parte desde el encendido, 404 o
  fallo), sv3 paga con el JSON nacional y sv4 enseña `holidays` Madrid, bajo el aviso; con fila, igual.
- **Sin bloqueo (DA17 = B).** Una línea calculada con el respaldo puede registrarse en Sigrid;
  defensas: el aviso, `review_required` si falla el refresco (R8) y el recálculo con el
  siguiente parte (R38). El día del encendido el aviso sale a casi todos hasta su primer parte.
- Con DA5 = 1, un calendario solo con fiestas locales pasa: M2 es la defensa (DA12). Una
  pasada fallida tras el upsert (candado F-046) deja el calendario anterior hasta la siguiente.
- **Descartados**: `SesameCalendarioLaboral` sin cablear; guardar el calendario por defecto en
  un 404 (contradice DA19 = B); el bloqueo dormido en `app.js`; refrescar en cada pasada.

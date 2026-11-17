<!-- specs/F-032-sesame-festivos-produccion/design.md -->
# F-032 · Activar Sesame en producción — Diseño

**Rigor: `estandar`** (DA10, mantenida por el humano): tabla aditiva en la base propia,
refresco best-effort, lectura en sv3/sv4, herramienta de lectura y scripts. Aviso: el código
nuevo decide con qué festivos se paga (disparador 1); el encendido es manual tras M2–M3.

## 1. Estado de partida (verificado el 2026-11-17 en `f2de8dd`, solo lectura)

- **Integración apagada.** sv3 `api/app.py::construir_calendario` (:59): JSON o, con
  `SESAME_API_*`, `SesameCalendarioLaboral` (caché en memoria 6 h; `consumir_degradacion()` ⇒
  el conciliador sube a revisión los partes del grupo). sv4: `CalendarioProvider`, misma
  cascada; `fiable_para` gobierna avisos y bloqueo `[SIN-SESAME]` (`_calendario_fiable` :2683,
  `_dia_ajuste` :2908). Las vistas lo usan por interfaz y sus tests con `ProveedorFake`.
- **Esquema.** `orm_models.py` byte-idéntico (guardián F-010, `TABLAS` = 8); tablas por
  `create_all` al arrancar sv3 (`sqlalchemy_parte_repository.py:243`) y sv4
  (`parte_repository.py:1111`) más `ddl_complementario()`; así entró `franquicia_ajuste`.
- **Recálculo (DA7)**: `conciliar_todos` global tras cada ingesta y cada `recalcular`; sv3 es
  KEDA a 0 réplicas; con `REPARTO_REAJUSTE`, días mixtos a `reparto_pendiente`.
- **Respaldos distintos** (sv3 nacionales + `2026-02-28`; sv4 `holidays` `MD`); rejilla con
  `holiday_name_para(None)` (D6 de F-003); sesame-api y F-013 como en f2de8dd.

## 2. Límite de servicio y trabajo fuera del repositorio

**sv3**: refresco en la ingesta (único que pide festivos a Sesame), escritura y lectura de
la tabla, herramienta. **sv4**: solo lectura, rejilla por persona y textos. **Ambos**:
`orm_models.py` (gemelo listado) y `festivos_guardados.py` (gemelo nuevo, DA20). `infra/`, docs
y `azure-apps/partes.md`: implementer. Repo **sesame-api** y Azure (P0–P5, M1–M8): **humano**.

**¿Duplicación?** sv3 escribe y lee; sv4 solo hace un `SELECT` (como `list_jornadas_empleado`):
no es lógica duplicada. **Sí** lo sería la cascada y el formato de `festivos_json`, que deben
coincidir o sv4 enseñaría festivos que sv3 no paga: módulo puro gemelo con guardián, que
entra en la lista cerrada de `CLAUDE.md` solo con el sí del humano (DA20). El mínimo, solo en sv3.

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
| `services/partes-persistencia/tests/test_f032_{festivos_guardados,repositorio,refresco,ingesta,tabla_calendario,wiring,contraste,recalculo}.py` | R2–R17, R26–R30, R35–R36 |
| `services/partes-front/tests/test_f032_{festivos_guardados,provider_tabla,avisos,rejilla_obra}.py` | R18–R25 |
| `tests/test_f032_{festivos_guardados_gemelos,contrato_festivos,infra_sesame}.py` | R39 (patrón `test_f015_r19_…`), R1 (patrón `test_f056_contrato_franquicia`), R31–R34 (estático) |
| `infra/add_sesame_partes.ps1` | §5.9 |

## 4. Ficheros a modificar y a retirar

- **Los dos `orm_models.py`** (mismo commit): §5.1, docstring «NUEVE tablas»; `TABLAS` de
  `test_f010_orm_models_gemelos.py` y `test_f015_r29_guardian_cinco_tablas.py` gana la novena.
- **sv3**: `persist_parte_pipeline.py` (§5.4), `api/app.py` (§5.5), `config/settings.py`
  (`sesame_festivos_minimos: int = Field(1, ge=0)`, fuera `sesame_cache_ttl_s`),
  `test_f003_r10_wiring_sv3.py` (Sesame ⇒ tabla; JSON y log sin clave se quedan). **Se
  retiran** `sesame_calendario_laboral.py`, `test_f003_r8_sesame_calendario.py` y lo que solo
  los servía en `tests/dobles.py` (R17).
- **sv4**: `calendario_provider.py` (§5.6), `parte_repository.py` (`list_festivos_trabajador`
  y §5.7), `web/app.py` (`build_app`, `obra_detail`), las tres plantillas con aviso y
  `static/app.js` :5270 (R22). **Tests que cambian a propósito**:
  `test_f003_r4_calendario_provider.py` (cascada ⇒ tabla; jornada y apagado se quedan),
  `test_f003_r2_la_columna_de_la_matriz_usa_el_calendario_por_defecto` (D6 revocada ⇒
  R23–R24) y los asertos de «Sesame no disponible» de `test_f003_r2`, `test_f003_r23`,
  `test_f022_aprobar_seleccion` y `test_f056_franquicia`. Ningún otro.
- **infra y docs**: `create_capps_partes.ps1` (R34), `00_vars_partes.ps1`
  (`$SESAME_FESTIVOS_MINIMOS = 1`), `README_partes.md`, `docs/ARCHITECTURE.md`,
  `azure-apps/partes.md`; `harness/features.json` lo anota el líder.

## 5. Clases y funciones

### 5.1 `FestivoTrabajadorOrm` (`festivos_trabajador`, gemelo)

`id` Integer PK autoincrement; `dni_norm` String(32) NOT NULL `""`; `ano` Integer NOT NULL
`"0"`; `festivos_json` Text NOT NULL `"{}"`; `n_festivos` Integer NOT NULL `"0"`; `origen`
String(16) NOT NULL `"sesame"`; `leido_en_utc` String(40) NOT NULL `"1970-01-01T00:00:00Z"`;
`Index("ux_festivos_trabajador_dni_ano", "dni_norm", "ano", unique=True)`. Docstring: `*` =
calendario por defecto, DNI = dato personal (como `empleado_jornada`), solo sv3 escribe. Sin
`is_active`: la fila se sustituye. `create_all` la crea en el primer arranque; ni SQL a mano ni
permisos nuevos (mismo rol que creó `franquicia_ajuste`).

### 5.2 `application/services/festivos_guardados.py` (puro, gemelo, DA20)

Solo biblioteca estándar (el guardián lo carga por ruta):
```python
DNI_POR_DEFECTO = "*"; ORIGEN_SESAME = "sesame"; ORIGEN_POR_DEFECTO = "por_defecto"
@dataclass(frozen=True)
class FilaFestivos: dni_norm: str; ano: int; festivos: Mapping[str, str | None]; origen: str; leido_en_utc: str
def del_ano(pares, ano) -> dict[str, str | None];  def a_json(festivos) -> str  # claves ordenadas
def fila_de(dni_norm, ano, festivos_json, origen, leido_en_utc) -> FilaFestivos  # ValueError si mal formado
def elegir(dni_norm, ano, leer: Callable[[str, int], FilaFestivos | None]) -> tuple[FilaFestivos | None, str]
```
`elegir` (DA19): con DNI, su fila ⇒ fuente `sesame` (o `default` si `origen = por_defecto`);
sin ella, la fila `*` ⇒ `sin_fila`; sin `*` ⇒ `(None, "respaldo")`. Sin DNI: la fila `*` ⇒
`default`; sin ella ⇒ `(None, "respaldo")`. Recibe el DNI ya normalizado (cada servicio con su
`normalize_dni`).

### 5.3 `SqlAlchemyFestivosRepository` (sv3, infrastructure)

`leer_todas() -> dict[(dni_norm, ano), FilaFestivos]` (~220 filas/año; una mal formada se
omite con WARNING por su `id`); `guardar(fila)` con `insert().on_conflict_do_update(
index_elements=["dni_norm", "ano"])` del dialecto (`postgresql`/`sqlite`): aguanta dos réplicas
(R11); `claves()` para la herramienta (R29).

### 5.4 `RefrescoFestivos` (sv3, application) y la ingesta

`RefrescoFestivos(*, cliente, repositorio, minimo, ahora_utc, al_guardar=lambda: None)` con
`refrescar(dnis, anos, necesita_defecto) -> ResultadoRefresco(guardadas, conservadas,
sin_dato)`, y `anos_de_semana(fecha) -> set[int]` (años del lunes y del domingo ISO).
`cliente` y `repositorio` por duck-typing (como `recalculo_seguimiento` del pipeline). Por
año: `calendario_por_defecto(ano)` una vez (bueno ⇒ se guarda como `*`); por DNI,
`festivos(dni, ano)` y, si es `None` (404), el por defecto con `origen = por_defecto`. Vale si
hay lista y `len(del_ano(...)) >= minimo`; si no (excepción, `None` del por defecto o
incompleto) es un fallo: con fila guardada ⇒ `conservadas` y no se toca; sin ella ⇒ `sin_dato`
(la `*` solo cuenta con `necesita_defecto`). Cada guardado llama a `al_guardar()` (caché de
§5.5). Nunca lanza; log `[festivos] refresco guardadas=… conservadas=… sin_dato=…`, sin DNIs.

**Pipeline.** `PersistPartePipeline(..., refresco_festivos: Any = None)`. En `run()`, entre
`_compute_review_required` y `save_parte`, `_refrescar_festivos_safely(parte) -> bool` con
`dnis` = `normalize_dni(r.empleado.dni)` no vacíos, `necesita_defecto` = alguna línea sin DNI y
`anos` = `anos_de_semana(parte.fecha_iso or self._hoy())`. `sin_dato > 0` o un error
inesperado ⇒ `True` ⇒ `review_required = True` y WARNING `[festivos] parte <document_id> a
revision: N clave(s) sin festivos de Sesame`. El duplicado sale antes y no llega aquí (R10).

### 5.5 `TablaCalendarioLaboral` (sv3, infrastructure) y cableado

`TablaCalendarioLaboral(CalendarioLaboralPort)(*, repositorio, respaldo, ttl_s=60, reloj)`:
fin de semana; `elegir(…)` sobre `leer_todas()` (caché ≤ `ttl_s`); sin fila, el respaldo;
lectura fallida ⇒ respaldo + WARNING (R16). `olvidar()` vacía la caché. **Sin** `consumir_degradacion`, así que
el conciliador no marca nada (R16). Cableado: `construir_calendario(settings,
repositorio=None)` (sin Sesame ⇒ JSON como hoy; con Sesame y repositorio ⇒ la tabla) y
`construir_refresco_festivos(settings, repositorio, calendario) -> RefrescoFestivos | None`
(monta `SesameApiClient` sin cambios, `minimo = settings.sesame_festivos_minimos`, `al_guardar =
calendario.olvidar`). `build_app` pasa el mismo `calendario` a `RecursoConciliador` y el
refresco a `PersistPartePipeline`. Log `[sesame][wiring] CABLEADO base_url=… key_len=…
festivos_minimos=… festivos=tabla`.

### 5.6 `CalendarioProvider` (sv4) y cableado

Gana `leer_festivos: Callable[[], Iterable[dict]] | None` y `ttl_tabla_s=60`; `cliente` queda
para `jornada_contrato` y como interruptor (`activo`, DA18). `_resolver`: sin cliente ⇒
`sin_sesame` (igual que hoy); con cliente ⇒ `elegir` sobre la tabla leída (`fila_de` por fila,
caché ≤ `ttl_tabla_s`); lectura fallida ⇒ `respaldo` + WARNING. Se borran las llamadas a
`festivos`/`calendario_por_defecto` y `_degradar` (R19). Fuente nueva `sin_fila`, **fuera** de
`FUENTES_FIABLES`. `build_app` pasa `leer_festivos=repository.list_festivos_trabajador` (dicts,
como `list_jornadas_empleado`); log con `festivos=tabla`. Textos (R22): «⚠ El calendario puede
no ser exacto: **Sin calendario de Sesame** para algún trabajador: sus festivos salen del
calendario por defecto o del respaldo local. Se guarda con su siguiente parte.»; título de
`app.js` «Bloqueado: sin calendario de Sesame». El bloqueo no cambia de código:
`_calendario_fiable` ya bloquea lo no fiable (DA17).

### 5.7 Rejilla de obra por persona (sv4, DA13; igual que en f2de8dd)

`get_obra(..., holiday_name_de: Callable[[str | None], Callable[[date], str | None]] | None)`
sustituye a `holiday_name`; se pide una vez por fila y rellena cada celda. `ObraMatrixCell` gana
`holiday_name`; `ObraDayCol` pierde `is_holiday`/`holiday_name`. `obra_detail` pasa
`calendario_provider.holiday_name_para` y el aviso de jornada usa el mismo resolutor; se borra
`_consultas.update((None, ano) …)`. Plantilla: cabecera sin `mx-hol`; celda con `mx-hol` y
nombre en `title`; aviso según R25 y R22.

### 5.8 `contrastar_festivos_sesame.py` (consola, sv3)

Como en f2de8dd: funciones puras `contrastar_calendario` (cuenta con `del_ano`),
`clasificar_impacto` (`clase_linea` y `_congelado` importados), `render_markdown`,
`escribir_csv` y un `main(argv)` fino (`--ano --base-url --api-key --calendario
--festivos-minimos --salida --impacto`). `--impacto` añade `SqlAlchemyFestivosRepository.claves()`
para contar los DNIs activos sin fila del año, que decide encender sv4 (M6). Solo lectura.

### 5.9 `infra/add_sesame_partes.ps1` (PowerShell 5.1, CRLF, sin BOM)

Tras `00_vars_partes.ps1` y `00_capps_vars_partes.ps1`; `-Servicio sv3|sv4` (obligatorio) y
`[-Quitar]`. Valida R32 antes del primer `containerapp` (`az keyvault secret show --query id`). Secreto `sesame-key=keyvaultref:$KV_URI/secrets/
SESAME-API-KEY,identityref:$MI_ID` y `az containerapp update --set-env-vars`: sv3
`SESAME_API_BASE_URL`, `SESAME_API_KEY=secretref:sesame-key`, `SESAME_API_TIMEOUT_S`,
`SESAME_FESTIVOS_MINIMOS`; sv4 las tres primeras y `SESAME_CACHE_TTL_S` (jornada). Espera a
`latestReadyRevisionName == latestRevisionName` y acaba con los comandos de logs de §7.
`-Quitar`: `--remove-env-vars` (el secreto queda inerte). No encola ni lee claves; mismo `Run-Az`.

## 6. Ficheros que NO se tocan

`recurso_conciliador.py`, `reajuste_reparto.py`, `congelacion.py`, `jornada_resolver.py`,
`despacho.py`, `mensajes.py`, `recalculo_publisher.py` (sin motivo nuevo), los dos
`sesame_api_client.py`, `json_calendario_laboral.py`, `calendario_laboral.json`,
`holiday_provider.py`, `validar_datos_sesame.py`, `create_sv4_front.ps1`, `redeploy_*.ps1`,
`add_secrets_partes.ps1`, `enqueue_test.py`, sv1, sv2, sv5 y `sesame-api`.

## 7. Guía de despliegue y verificación manual (humano)

- **M1** (DA1, tras P0–P2): `az acr build -r acralbaranesdev`; `SESAMEAPI-TOKEN`,
  `SESAMEAPI-API-KEYS` y `SESAME-API-KEY` en `$KV` por consola; `ca-sesame-api` en `$CAE`,
  `--ingress internal --target-port 8006 --min-replicas 1 --max-replicas 1`, identidad
  `$MI_ID`; `/health` desde el entorno; FQDN a `$SESAME_BASE_URL` (`00_vars_partes.local.ps1`).
- **M2 (puerta DA12)**: en `services/partes-persistencia`, `python contrastar_festivos_sesame.py
  --ano 2026 --base-url <url> --api-key <clave>` (y 2025 si hay partes activos); en local,
  `$env:API_PORT="8016"`. `FALTAN DEL RESPALDO` ⇒ no se enciende; `INCOMPLETO` ⇒ RRHH (P5).
- **M3**: igual con `--impacto` y el `.env` de sv3; revisar `dura` y días mixtos. **M4**:
  `redeploy_partes.ps1 -Solo sv3,sv4`; «DESACTIVADO»; `festivos_trabajador` existe y vacía.
- **M5**, fuera del horario de aprobación: `add_sesame_partes.ps1 -Servicio sv3`; con el
  siguiente parte, `[festivos] refresco guardadas=…`, filas nuevas y la pasada con
  `extras_reclasificadas`/`repartos_propuestos`, sin partes a revisión por festivos.
- **M6** (DA17), tras ≥ 2 días laborables y con M3 dando pocos «DNIs sin fila»: `-Servicio sv4`.
- **M7**: obra con dos calendarios (cada fila los suyos); sin fila ⇒ aviso y bloqueo; decidir
  `reparto_pendiente`. **M8** (opcional): `-Quitar` en sv4 y sv3 ⇒ «DESACTIVADO».

## 8. Frontera

¿Cruza la frontera del proyecto? **Sí.** sv3 pasa a consumir **sesame-api** (`festivos` y
`calendario_por_defecto`, solo al ingerir) y sv4 solo `/jornada`: servicio interno nuevo en
`cae-partes-dev` (DA1). La base `partes` (propia, no el servidor compartido) gana
`festivos_trabajador`. Variable nueva `SESAME_FESTIVOS_MINIMOS` (sv3) y secreto
`SESAME-API-KEY`. Se actualiza `azure-apps/partes.md` (R38); `sesame-api.md` es de su dueño (P4).

## 9. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| DA1 Dónde vive sesame-api | (A) `ca-sesame-api` en `cae-partes-dev`, ingress interno, 1 réplica, secretos en `kv-partes`; (B) propios con ingress externo; (C) propios internos | (A) | (A) 2026-11-16 |
| DA2 Réplicas | (A) min = max = 1; (B) 0–1 | (A) | (A) 2026-11-16 |
| DA3 Encendido | (A) `add_sesame_partes.ps1` con `-Quitar`; (B) recrear las apps | (A) | (A) 2026-11-16; desde 2026-11-17 con `-Servicio sv3\|sv4` y sin pasada |
| DA4 Si Sesame no responde | (A) en la ingesta: lo último guardado; sin fila, JSON + `review_required` (nivel F-003); (B) solo respaldo + log | (A) | (A) 2026-11-17 (la degradación pasa a la ingesta) |
| DA5 Mínimo de festivos | (A) **1** configurable; (B) 8; (C) 0 | (A) | (A) 2026-11-16; solo en sv3 |
| DA6 Contraste | (A) consola en sv3 con `--impacto`; (B) sin herramienta | (A) | (A) 2026-11-16; llama a sesame-api directamente |
| DA7 Partes ya conciliados | (A) recálculo de lo libre en la siguiente pasada; congelado intacto salvo propuesta F-046; (B) solo fechas posteriores | (A) | (A) 2026-11-16 |
| DA8 `/jornada` con 0 contratos | (A) P3 en sesame-api; (B) interruptor en sv4 | (A) | (A) 2026-11-16 |
| DA9 `sesame-api.md` | (A) lo escribe su dueño, `partes.md` enlaza | (A) | (A) 2026-11-16 |
| DA10 Rigor | (A) estándar; (B) crítico | (A) | (A) 2026-11-16 |
| DA11 Pasada al encender | — | — | **Retirada** 2026-11-17 por DA15 (sin pasada ni `pedir_recalculo_partes.py`) |
| DA12 A Sesame le faltan festivos del respaldo | (A) puerta: no se enciende y se re-decide; (B) encender igual | (A) | (A) 2026-11-17 |
| DA13 Rejilla de obra | (A) celda por persona, cabecera sin festivos; (B) D6 de F-003 | (A) | (A) 2026-11-17 |
| DA14 Persistir los festivos | (A) tabla `festivos_trabajador` en `partes`, clave DNI + año; (B) solo caché | (A) | (A) 2026-11-17 |
| DA15 Cuándo se lee Sesame | (A) solo al ingerir, con upsert; los recálculos leen la tabla | (A) | (A) 2026-11-17 |
| DA16 sv4 y los festivos | (A) lee la tabla, no llama a Sesame por festivos | (A) | (A) 2026-11-17 |
| DA17 Bloqueo `[SIN-SESAME]` sin fila | (A) se mantiene (no fiable ⇒ bloqueo salvo override) y sv4 se enciende **después** de sv3 (M6); (B) solo aviso; (C) bloqueo con los dos a la vez (el día 1, todo bloqueado) | (A) | |
| DA18 Interruptor de sv4 y jornada | (A) sv4 conserva `SESAME_API_*`: encienden la lectura de la tabla y la jornada (DA8); (B) variable nueva `FESTIVOS_SESAME` y jornada apagada | (A) | |
| DA19 Respaldo sin fila | (A) los dos usan la fila `*` y, sin ella, su respaldo local (alinea sv3 y sv4; cambia el «sin fila ⇒ JSON» de DA15); (B) sv3 JSON, sv4 fila `*` (difieren); (C) alinear sv4 al JSON por configuración (cambia hoy el portal) | (A) | |
| DA20 Cascada gemela | (A) `festivos_guardados.py` entra en la lista cerrada de `CLAUDE.md` con guardián; (B) cada servicio la suya, sin guardián | (A) | |

## 10. Riesgos y alternativas descartadas

- Con DA5 = 1, un calendario solo con fiestas locales pasa el control: M2 es la defensa
  (DA12). **Sin fila tras encender**: fila `*` o respaldo y libres viejas sin recalcular hasta
  su siguiente parte (DA17, M6). Una pasada fallida tras el upsert (candado F-046) deja líneas
  con el calendario anterior hasta la siguiente. Reasignar en sv4 a alguien sin partes ⇒ sin fila.
- **Descartados**: conservar `SesameCalendarioLaboral` sin cablear (código muerto que llama a
  Sesame); el mínimo en los clientes gemelos (solo lo usa sv3); refrescar en cada pasada
  (rechazado); caché larga en sv4; marcar revisión en las pasadas (inundaría al encender).

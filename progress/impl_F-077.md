# F-077 · Informe del implementer (`critico`)

sv3 lee los festivos directamente de la API oficial de Sesame HR, sin la pasarela
`sesame-api`. Rama `feature/F-077-sesame-directo-sin-pasarela`. Spec:
`specs/F-077-sesame-directo-sin-pasarela/` (DA1–DA14 = A). Hechas T1–T15 y T19; ciclo 1 de la review 1 al final. T16 (mutación)
la lanza el líder tras el APPROVED. T17–T18 son manuales del humano.

## Qué cambió

- **Cliente de Sesame HR de sv3** (`infrastructure/sesame/sesame_hr_client.py`, R1–R9):
  `Authorization: Bearer`, solo `GET` (AST, R9), paginación estricta; reintentos de 429/5xx con
  `Retry-After` (numérico o fecha, tope 30 s); 401/403, red y JSON inválido ⇒ fallo tipado sin
  cuerpo, query ni token; acepta `dayOff` y `daysOff`; un 404 de festivos es fallo (DA6).
- **Adaptador `FestivosSesameHr`** (`festivos_sesame_hr.py`, R10–R14, R19):
  - Índice DNI → empleado en memoria, normalizado con `normalize_dni` (DA5) y compartido con TTL.
  - Duplicados ⇒ gana el activo; las fichas sin DNI se descartan (DA7).
  - El índice se carga entero o nada (DA8; sin DNIs también es fallo, enmienda de R13). Si
    falla, hay corte de 60 s sin red y la función devuelve fallo para ese (DNI, año).
  - Un DNI ausente de un índice bien cargado ⇒ `None` (DA6). El módulo no escribe a disco.
- **Cableado de sv3** (`config/settings.py`, `interface_adapters/api/app.py`, R15–R18):
  `SESAME_BASE_URL` (solo `https://`), `SESAME_TOKEN` y `SESAME_TIMEOUT_S`. Se retira
  `sesame_api_client.py`. Los logs no llevan datos personales.
- **Herramienta `contrastar_festivos_sesame.py`** (R24–R26): lee los calendarios de Sesame HR.
  - El token sale del entorno o de `pedir_token`, por consola sin eco. No hay `--api-key`.
  - Las faltas ⇒ código ≠ 0 y no se escribe nada.
  - `--impacto` usa el adaptador. Los informes no llevan nombres ni emails.
- **sv4 sin Sesame** (T11, R20–R22):
  - Fuera `infrastructure/sesame/`, `validar_datos_sesame.py` y `SESAME_API_*` /
    `SESAME_CACHE_TTL_S`.
  - Interruptor `FESTIVOS_SESAME_ENABLED` (defecto `false`, DA10), y
    `CalendarioProvider(activo=…)` en vez de `cliente=`/`ttl_seconds=`.
  - La vista de trabajador pierde el badge «contrato:» y el aviso de divergencia (DA9).
- **Infra** (R27–R30): `SESAME-TOKEN` (Key Vault) ⇒ secretref `sesame-token`, solo en sv3. sv4
  lleva solo `FESTIVOS_SESAME_ENABLED`. `add_sesame_partes.ps1` valida `https://` y el secreto
  antes del primer `containerapp`, retira lo viejo solo si está y `-Quitar` lo apaga.
  `create_*`, `add_secrets` y `00_vars` también cambian (`00_vars` queda vacía).
- **Documentación** (R33): `CLAUDE.md` saca los clientes `infrastructure/sesame/` de la lista
  cerrada. También cambian `harness/servicios.json`, `docs/ARCHITECTURE.md`,
  `infra/README_partes.md` y `README.md`.

## Ficheros

Lista completa: `git diff --stat dev..HEAD`.

- sv3: nuevos `infrastructure/sesame/{sesame_hr_client,festivos_sesame_hr}.py`, fuera
  `sesame_api_client.py`; cambian `config/{settings,logging_config}.py`, `api/app.py`,
  `contrastar_festivos_sesame.py` y docstrings de tres módulos (design §3). Tests nuevos
  `test_f077_{cliente_hr,festivos_hr,wiring,ingesta_hr,logs_sin_datos,contraste}.py`,
  `fixtures_sesame.py` reescrito (ficticio), adaptados `test_f032_{wiring,refresco,contraste,
  campana}.py` y `test_f003_r10_wiring_sv3.py`, fuera `test_f032_{cliente_sesame,logs_sin_dni}.py`.
- sv4: cambian `config/{settings,logging_config}.py`, `calendario_provider.py`, `web/app.py` y
  `trabajador_detail.html`; fuera `infrastructure/sesame/` y `validar_datos_sesame.py`. Test nuevo
  `test_f077_sin_sesame_sv4.py`; adaptados (lista cerrada de design §4 y enmienda)
  `test_f003_r{4,7,16,23}_*.py`, `test_f032_{avisos,logs_sin_dni,provider_tabla,wiring_sv4}.py` y
  `test_f056_decisiones.py`; fuera `test_f003_r1_sesame_client.py`,
  `test_f003_r13_jornada_contrato.py`, `test_f013_informe_sesame.py` y `fixtures_sesame.py`.
- Raíz: nuevos `tests/test_f077_{sin_pasarela,infra_sesame}.py`; fuera `test_f032_infra_sesame.py`.
- Infra: `add_sesame_partes.ps1`, `create_capps_partes.ps1`, `create_sv4_front.ps1`,
  `add_secrets_partes.ps1`, `00_vars_partes.ps1` y `README_partes.md`. Docs: `CLAUDE.md`,
  `harness/servicios.json`, `docs/ARCHITECTURE.md` y `README.md`.

## Desviaciones

- **Enmienda de la lista cerrada (aprobada por el humano el 2026-11-18, «ok»).** T11 dejaba
  7 tests rojos fuera de la lista: 4 de `test_f056_decisiones.py`, 2 de `test_f032_sin_bloqueo.py`
  y 1 de `test_f056_vista.py`. Los 7 caían porque el doble `CalendarioNoFiable` llamaba a
  `super().__init__(cliente=None, …)`.
  Solo cambió esa línea (≈401) a `super().__init__(respaldo_holiday_name=lambda d: None)`; los
  7 pasan sin tocar los otros dos ficheros. Enmienda en `tasks.md` (T11).
- **CSS muerto (design §5.4, «si quedan muertas»).** `static/styles.css` no tiene reglas
  `.jornada-contrato` ni de divergencia, así que no había nada que retirar. Las clases
  `cell-sub` y `tag-difiere`, que se usan en otras vistas, se conservan. `static/app.js` no se
  tocó, así que no hacía falta `node --check`.

## Documento del ecosistema

Cruza la frontera (design §8) y `CLAUDE.md` declara `azure-apps`. `azure-apps/partes.md`:
commit **a568995** en `azure-apps`, aparte de la feature, con `pull --rebase` antes y sin
conflicto. **Sin push**: lo hace el humano (`git -C C:\Users\pgris\PycharmProjects\azure-apps pull`
y después `push`).

## Fase RED (trazas reales)

Se reprodujeron el 2026-11-18 en un worktree temporal, ejecutando cada test en el commit en que
existía el test y aún no el código. El worktree ya está retirado.

```
$ git checkout 733d4c8   # T2; en services/partes-persistencia
$ python -m pytest -q -p no:cacheprovider tests/test_f077_cliente_hr.py
E   ModuleNotFoundError: No module named 'infrastructure.sesame.sesame_hr_client'
ERROR tests/test_f077_cliente_hr.py
1 error in 1.98s
```
```
$ git checkout b108c11   # T4; en services/partes-persistencia
$ python -m pytest -q -p no:cacheprovider tests/test_f077_festivos_hr.py
E   ImportError: cannot import name 'festivos_sesame_hr' from 'infrastructure.sesame'
ERROR tests/test_f077_festivos_hr.py
1 error in 1.06s
```
```
$ git checkout 9ec1af0   # T6; en services/partes-persistencia
$ python -m pytest -q -p no:cacheprovider tests/test_f077_wiring.py tests/test_f077_ingesta_hr.py tests/test_f077_logs_sin_datos.py
E   AttributeError: 'Settings' object has no attribute 'sesame_base_url'. Did you mean: 'sesame_api_base_url'?
E   AssertionError: assert False is True   (… .sesame_enabled)
E   Failed: DID NOT RAISE ValidationError   (x3: URL sin https / sin token)
10 failed, 22 passed in 8.19s
```
```
$ git checkout 7f0c295   # T8; en services/partes-persistencia
$ python -m pytest -q -p no:cacheprovider tests/test_f077_contraste.py
E   ModuleNotFoundError: No module named 'infrastructure.sesame.sesame_api_client'
ERROR tests/test_f077_contraste.py
1 error in 15.97s
```
```
$ git checkout bc7dbdd   # T10; en services/partes-front
$ python -m pytest -q -p no:cacheprovider tests/test_f077_sin_sesame_sv4.py
E   AssertionError: assert True is False   (Settings(... sesame_api_key='clave-vieja-de-prueba' ...).sesame_enabled)
E   AssertionError: assert {'cliente', '...'ttl_tabla_s'} == {'activo', 'l...'ttl_tabla_s'}
E     Extra items in the left set: 'cliente' 'ttl_seconds'
13 failed, 1 warning in 6.98s
```
```
$ git checkout fcafdad   # T12; raíz
$ python -m pytest -q -p no:cacheprovider tests/test_f077_infra_sesame.py
E   AssertionError: sin $RETIRADAS
E   assert None   (re.search '"sesame-token=keyvaultref:\$KV_URI/secrets/SESAME-TOKEN,identityref:\$MI_ID"')
E   AssertionError: sin $VARS_SV3 / sin $VARS_SV4
14 failed, 12 passed in 0.92s
```
```
$ git checkout 5f9cdb8   # T1; raíz
$ python -m pytest -q -p no:cacheprovider tests/test_f077_sin_pasarela.py
E   AssertionError: assert ['services\\p...estivos', ...] == []
E     Left contains 9 more items, first extra item: 'services\\partes-persistencia\\config\\settings.py: x-api-key'
E     Left contains 9 more items, first extra item: 'services\\partes-front\\config\\settings.py: x-api-key'
10 failed, 1 passed in 1.36s
```


## Verificación de T11

Commit **914f8d7**. Suite de sv4: **3809 passed in 937.35s** (antes de la enmienda, 7 failed).
Guardianes R20/R23/R31: 11 passed. Jinja2 de `trabajador_detail.html` parsea; `app.js` no se tocó.

## Salida de `bash harness/init.sh` (T19)

Primera pasada (2026-11-18/19) en ROJO solo por `PUERTA TAMAÑO` (`design.md` 252 > 250, por la
enmienda de design §4); resuelto por el líder y T19 en verde en 9effd33 (cobertura 99,2 %,
263/265). La salida vigente es la del ciclo 1, al final.

## Verificaciones manuales pendientes (humano, design §7)

- **M0**: rotar el token de Sesame HR (el `.env` de sesame-api estuvo en git) y, si Sesame lo
  permite, hacerlo de solo lectura. Después, `.\infra\add_secrets_partes.ps1` (`SESAME-TOKEN`).
  En local, poner `SESAME_BASE_URL` y `SESAME_TOKEN` en el `.env` de sv3 y quitar `SESAME_API_*`
  de sv3 y sv4.
- **M1**: en `services/partes-persistencia`, `python contrastar_festivos_sesame.py --ano 2026`
  (y 2025 si hay partes activos). `FALTAN DEL RESPALDO` ⇒ no se enciende; `INCOMPLETO` ⇒ RRHH
  (P5).
- **M2**: la misma orden con `--impacto`; revisar `dura` y los días mixtos.
- **M3**: `.\infra\redeploy_partes.ps1 -Solo sv3,sv4`; los dos logs dicen `DESACTIVADO`.
- **M4**, fuera del horario de aprobación: `$SESAME_BASE_URL` en el `.local` y
  `.\infra\add_sesame_partes.ps1`. `CABLEADO` en los dos servicios. Con el siguiente parte, sv3
  escribe `[sesame-hr] indice …` y `[festivos] refresco …`. Para comprobar que no sale ningún DNI:
  `az containerapp logs show -n ca-sv3-persistencia -g $RG --tail 300 | Select-String -Pattern
  '\b[0-9XYZ][0-9]{7}[A-Z]\b'`.
- **M5**: en el portal, un trabajador con fila no tiene aviso; uno sin fila tiene aviso y su
  registro pasa; la vista de trabajador no tiene badge «contrato:».
- **M6**: `.\infra\add_sesame_partes.ps1 -Quitar` ⇒ `DESACTIVADO`; volver a encender. Al
  encender, anotar el estado en `azure-apps/partes.md`.

Cada M deja aquí su comando y su resultado real (T17–T18).

## Pendiente

- T16: la campaña de mutación, en la pasada de campaña, tras el APPROVED del reviewer.
- T17–T18: M0–M6 del humano. Sin desplegar.
- Push del humano: la rama `feature/F-077-sesame-directo-sin-pasarela` y `azure-apps`
  (a568995).
- Fuera del alcance: `sesame-api` no se toca (DA2). P5 (RRHH completa Alicante) sigue abierta.

## Ciclo 1 (review 1)

Encargo: cambios 1 y 2 de `progress/review_F-077.md` y la enmienda de R13 del humano («a»).

- **Cambio 1** (a370158): el `MockTransport` de `test_f077_r1_el_plazo_llega_a_httpx` hace
  `assert request.method == "GET"`, como pide tasks.md.
- **Cambio 2** (ce697ec): `_ProveedorSinJornada` ya no define `jornada_contrato`; en su lugar un
  `__getattr__` que revienta ante cualquier atributo inexistente, así que una vista que pidiera
  la jornada (o cualquier cosa retirada) sigue rompiendo el test. 13/13 en verde.
- **Enmienda de R13** (2e33a1f): en `_indice_vigente`, tras el log de recuentos, un índice vacío
  (empleados, pero ninguno con DNI) abre el corte y lanza `SesameNoDisponible("sesame indice sin
  DNIs")` sin guardarse. El docstring del módulo lo recoge. Ningún otro test de F-077 dependía del
  índice sin DNIs (sv3 entera en verde tras el cambio: 2722 passed, 2 skipped).

RED, con el test ya reescrito y el código sin tocar (en `services/partes-persistencia`):
```
$ python -m pytest tests/test_f077_festivos_hr.py -k "solo_filas_sin_dni" -q
>           with pytest.raises(SesameNoDisponible) as exc:
E           Failed: DID NOT RAISE SesameNoDisponible
INFO ... [sesame-hr] indice empleados=2 duplicados=0 sin_dni=2 paginas=1
1 failed, 31 deselected in 0.32s
```
GREEN: `tests/test_f077_cliente_hr.py tests/test_f077_festivos_hr.py` ⇒ 98 passed in 0.47s.

`bash harness/init.sh` (ciclo 1, 2026-11-19): **ENTORNO LISTO**, exit 0. Raíz 2537 passed, 48 skipped;
sv3 2722 passed, 2 skipped; sv4 3809 passed; sv1/sv2/sv5 en caché. `PUERTA COBERTURA` 99.3 % (266/268);
`PUERTA TAMAÑO` OK (design 250/250, impl ≤220); `PUERTA CARRIL` N/A; `CAPA E2E` N/A.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests | Ciclo 1: raíz 2537 passed, 48 skipped; sv3 2722 passed, 2 skipped; sv4 3809 passed; sv1, sv2 y sv5 verdes en caché |
| Cobertura de líneas cambiadas | **99.3 %** (266/268) en el ciclo 1, umbral del nivel `critico`: 90 % |
| Mutación | Pendiente de T16: la pasada de campaña va tras el APPROVED (`python -m harness.mutacion --feature F-077`) |
| Tiempo de la suite | Ciclo 1, dentro de `init.sh`: raíz 1242.53 s, sv3 60.73 s, sv4 651.54 s |
| Capa e2e | N/A (`CAPA E2E: N/A`, ningún servicio declara el bloque e2e) |

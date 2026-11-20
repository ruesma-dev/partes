# F-077 · Informe del implementer (`critico`)

sv3 lee los festivos directamente de la API oficial de Sesame HR, sin la pasarela
`sesame-api`. Rama `feature/F-077-sesame-directo-sin-pasarela`. Spec:
`specs/F-077-sesame-directo-sin-pasarela/` (DA1–DA14 = A). Hechas T1–T15 y T19; ciclo 1 de la review 1 y pasada de campaña (T16) al
final. T17–T18 son manuales del humano.

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
- **Herramienta `contrastar_festivos_sesame.py`** (R24–R26): calendarios de Sesame HR; token
  del entorno o por consola sin eco (sin `--api-key`); faltas ⇒ código ≠ 0 sin escribir;
  `--impacto` usa el adaptador; informes sin nombres ni emails.
- **sv4 sin Sesame** (T11, R20–R22): fuera `infrastructure/sesame/`, `validar_datos_sesame.py`,
  `SESAME_API_*`/`SESAME_CACHE_TTL_S`, el badge «contrato:» y el aviso de divergencia (DA9);
  interruptor `FESTIVOS_SESAME_ENABLED` (`false`, DA10) y `CalendarioProvider(activo=…)`.
- **Infra** (R27–R30): `SESAME-TOKEN` (KV) ⇒ secretref `sesame-token`, solo sv3;
  `add_sesame_partes.ps1` valida `https://` y el secreto antes del primer `containerapp`, retira
  lo viejo si está y `-Quitar` apaga. Cambian `create_*`, `add_secrets` y `00_vars` (vacía).
- **Documentación** (R33): `CLAUDE.md` saca `infrastructure/sesame/` de la lista cerrada; cambian
  `harness/servicios.json`, `docs/ARCHITECTURE.md`, `infra/README_partes.md` y `README.md`.

## Ficheros

Lista completa: `git diff --stat dev..HEAD` (y design §3–§4).

- sv3: nuevos `infrastructure/sesame/{sesame_hr_client,festivos_sesame_hr}.py` (fuera
  `sesame_api_client.py`), cambian `config/`, `api/app.py`, `contrastar_festivos_sesame.py` y
  tres docstrings; tests nuevos `test_f077_*.py`, `fixtures_sesame.py` ficticio, F-032/F-003 adaptados.
- sv4: fuera `infrastructure/sesame/` y `validar_datos_sesame.py`; cambian `config/`,
  `calendario_provider.py`, `web/app.py`, `trabajador_detail.html`; test `test_f077_sin_sesame_sv4.py`
  y los adaptados de la lista cerrada de design §4 (más la enmienda).
- Raíz `tests/test_f077_{sin_pasarela,infra_sesame}.py`; infra (5 scripts y README) y docs
  (`CLAUDE.md`, `servicios.json`, `ARCHITECTURE.md`, `README.md`).

## Desviaciones

- **Enmienda de la lista cerrada (aprobada por el humano el 2026-11-18, «ok»).** T11 dejaba
  7 tests rojos fuera de la lista: 4 de `test_f056_decisiones.py`, 2 de `test_f032_sin_bloqueo.py`
  y 1 de `test_f056_vista.py`. Los 7 caían porque el doble `CalendarioNoFiable` llamaba a
  `super().__init__(cliente=None, …)`.
  Solo cambió esa línea (≈401) a `super().__init__(respaldo_holiday_name=lambda d: None)`; los
  7 pasan sin tocar los otros dos ficheros. Enmienda en `tasks.md` (T11).
- **CSS muerto (design §5.4).** `styles.css` no tiene reglas `.jornada-contrato` ni de
  divergencia: nada que retirar (`cell-sub`, `tag-difiere` siguen en uso); `app.js` intacto.

## Documento del ecosistema

`azure-apps/partes.md` (design §8): commit **a568995** aparte, `pull --rebase` antes, sin
conflicto. **Sin push**: el humano, `git -C C:\Users\pgris\PycharmProjects\azure-apps pull` y luego `push`.

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


## Verificación de T11 y T19

T11 (914f8d7): sv4 **3809 passed in 937.35s**; guardianes R20/R23/R31 11 passed. T19: verde en
9effd33 tras resolver el líder `PUERTA TAMAÑO` (design 252 > 250). Salida vigente: la del final.

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

- T16: aceptación del humano de los 3 mutantes equivalentes (pasada de campaña, al final).
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
| Tests | Pasada de campaña: sv3 2732 passed, 2 skipped (+10 tests); raíz 2537 passed. Ciclo 1: raíz 2537 passed, 48 skipped; sv3 2722 passed, 2 skipped; sv4 3809 passed; sv1, sv2 y sv5 verdes en caché |
| Cobertura de líneas cambiadas | **99.3 %** (266/268) en el ciclo 1, umbral del nivel `critico`: 90 % |
| Mutación | 141 generados, 85 evaluados (campaña completa, uno por línea), 73 muertos, **12 supervivientes**, 0 timeouts, 7791 s. Tras T16: 9 muertos con test, **3 equivalentes aceptados por el humano el 2026-11-19** (`progress/mutacion_F-077.md`) |
| Tiempo de la suite | Ciclo 1, dentro de `init.sh`: raíz 1242.53 s, sv3 60.73 s, sv4 651.54 s |
| Capa e2e | N/A (`CAPA E2E: N/A`, ningún servicio declara el bloque e2e) |

## Pasada de campaña (T16)

Campaña del líder sobre 11d32fc (`--workers 3`): 85 evaluados, 73 muertos, 12 supervivientes.
Informe y datos commiteados en 611adac; análisis completo en `progress/mutacion_F-077.md`.
Tests en dbecb3e (solo `services/partes-persistencia/tests/`, sin tocar producción):

- `test_f077_wiring.py`: `SESAME_TIMEOUT_S=0.5` vale (design 5.3, `gt=0`) ⇒ n.º 1.
- `test_f077_festivos_hr.py`: corte con reloj de origen negativo (R14, `monotonic`) ⇒ n.º 3.
- `test_f077_cliente_hr.py`: dataclasses inmutables y hasheables (5.1) ⇒ n.º 5–7; tope por
  defecto 20 000 (5.1, R2) ⇒ n.º 8; `daysOff: []` manda sobre `dayOff` (R8) ⇒ n.º 10; un 200
  `[]`/`""` da «sin listado», no «HTTP 404» (R5, DA6) ⇒ n.º 11; `Retry-After` `-5`/`nan` en el
  2.º intento ⇒ `[1.0, 2.0]` (R3) ⇒ n.º 12.

Muerte reproducida a mano (`scratchpad/repro.py`: aplica en el árbol, `pytest -q` del test,
revierte en `finally`): los 9 dan `failed` con el mutante y `passed` sin él; árbol limpio.
**Equivalentes** (aceptados por el humano el 2026-11-19: «acepto»): n.º 2 y 4 (`EmpleadoSesame` siempre
verdadero: `not x` ⇔ `x is None`) y n.º 9 (el `ultimas_paginas` inicial nunca se lee: el log
de R12 va tras un listado que lo ha fijado). Con su mutante, las suites F-077 siguen verdes.
La lectura de R8 del n.º 10 es la literal: si el humano la quiere al revés, es cambio de spec.
T16 queda **sin marcar** hasta esa aceptación.

`bash harness/init.sh` (2026-11-19): **ENTORNO LISTO**, exit 0. Raíz 2537 passed, 48 skipped (905 s); sv3 **2732 passed**, 2 skipped (93 s); sv1/sv2/sv4/sv5 en caché. COBERTURA 99.6 % (267/268); TAMAÑO OK; CARRIL y E2E N/A.

### Resultado M3 (humano lanza, líder verifica por Log Analytics, 2026-11-20)

`.\infra\redeploy_partes.ps1 -Solo sv3,sv4` (lleva también F-032 y F-078). Revisiones
`ca-sv3-persistencia--r20261120213950` y `ca-sv4-front--r20261120213950`. sv3: `[sesame][wiring]
DESACTIVADO (faltan SESAME_BASE_URL/SESAME_TOKEN)`, esquema inicializado (216 sentencias), alias de
membrete de las empresas 1 y 28. sv4: `[sesame][wiring] DESACTIVADO (FESTIVOS_SESAME_ENABLED=false)`,
esquema inicializado, `Application startup complete`. Sin `Traceback` en ninguna de las dos. **M3 OK.**

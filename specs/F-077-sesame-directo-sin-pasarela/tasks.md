<!-- specs/F-077-sesame-directo-sin-pasarela/tasks.md -->
# F-077 · Sesame HR directo, sin la pasarela — Tareas

Rama: **`feature/F-077-sesame-directo-sin-pasarela`**. Un commit **local** por tarea, `F-077 Tn:
…`, por rutas explícitas (nunca `git add -A`). Sin push ni PR. Rigor **`critico`** (DA4): fase
RED con traza en `progress/impl_F-077.md`, cobertura de líneas cambiadas ≥ umbral del nivel,
campaña de mutación **exigida** con la regla del nivel (`harness/rigor.json`) y **cero
supervivientes** en la muestra sin test nuevo o justificación aceptada por el humano; las M de
design §7, con comando y resultado real.

Reglas que no se negocian:
- DA5–DA14 se aplican tal como las decida el humano (design §9). Si algo resulta contradictorio, PARAR.
- Prohibido abrir o leer cualquier `.env` (el de `sesame-api` y los de partes llevan el token real).
  Prohibido llamar a Sesame HR o a sesame-api en red; `sesame-api` solo se lee como referencia.
- Tests sin red ni BBDD real: `httpx.MockTransport` (que **rechaza todo método distinto de GET**),
  esperas inyectadas (`dormir`), relojes falsos y la SQLite de `tests/dobles`.
- En fixtures y tests, solo datos **ficticios**: ni DNIs, ni nombres, ni tokens, ni ids reales.
- Ningún log, mensaje de excepción ni informe Markdown nuevo lleva DNI, nombre, email, token ni id
  de empleado (R5, R18).
- No se tocan los ficheros de design §6 (`congelacion.py`, `esta_congelado`, `festivos_guardados.py`…).
- Tests existentes que cambian: **solo** la lista cerrada de design §4; si cae otro, PARAR.

- [x] T1: Guardianes rojos de la raíz `tests/test_f077_sin_pasarela.py`: R31 (ningún `.py` de producción de sv3/sv4 nombra `x-api-key`, `/api/v1/festivos`, `/api/v1/jornada`, `/api/v1/calendarios-festivos` ni `SESAME_API_`), R20 (sv4 sin `infrastructure/sesame/`, sin importarlo, sin `SESAME_TOKEN`), R23 (no existe `validar_datos_sesame.py`), R9 estático (por AST, `sesame_hr_client.py` y `festivos_sesame_hr.py` solo llaman a `.get` de httpx y no tienen `post/put/patch/delete/request/send/stream`) y R33 (CLAUDE.md sin los clientes `infrastructure/sesame/` en la lista cerrada; `servicios.json` sin el cliente de sv4)  |  Verificación: traza RED
- [x] T2: Tests rojos del cliente `services/partes-persistencia/tests/test_f077_cliente_hr.py` (R1–R9: cabeceras, solo GET, paginación y sus fallos, reintentos 429/5xx con `Retry-After` numérico, fecha HTTP y tope 30 s, red, 401/403, JSON inválido, mensajes sin cuerpo/query/token, campos descartados de empleados, `dayOff`/`daysOff`, 404 de festivos ⇒ fallo, calendarios) y reescritura de `tests/fixtures_sesame.py` con respuestas ficticias de Sesame HR  |  Verificación: traza RED
- [x] T3: `infrastructure/sesame/sesame_hr_client.py` de sv3 (design §5.1)  |  Verificación: T2 en verde, `python -m pytest tests/test_f077_cliente_hr.py -q` desde `services/partes-persistencia`
- [x] T4: Tests rojos del adaptador `tests/test_f077_festivos_hr.py` de sv3 (R10–R14 y R19: normalización DA5, no encontrado ⇒ `None`, índice compartido y TTL con reloj falso, duplicados y sin DNI, índice todo-o-nada, 0 empleados, corte de 60 s sin red, 404/cuerpo sin corte, el módulo no importa nada que escriba a disco)  |  Verificación: traza RED
- [x] T5: `infrastructure/sesame/festivos_sesame_hr.py` de sv3 (design §5.2)  |  Verificación: T4 en verde
- [x] T6: Tests rojos de cableado e ingesta de sv3: `tests/test_f077_wiring.py` (R16–R17), `tests/test_f077_ingesta_hr.py` (R15, pipeline real + adaptador real + SQLite) y `tests/test_f077_logs_sin_datos.py` (R18, `configure_logging` real); adaptar `test_f032_wiring.py`, `test_f003_r10_wiring_sv3.py` y `test_f032_refresco.py`  |  Verificación: traza RED
- [x] T7: sv3 `config/settings.py` e `interface_adapters/api/app.py` (design §5.3); retirar `infrastructure/sesame/sesame_api_client.py`, `tests/test_f032_cliente_sesame.py` y `tests/test_f032_logs_sin_dni.py`; docstrings de `refresco_festivos.py`, `persist_parte_pipeline.py`, `tabla_calendario_laboral.py` y `logging_config.py`  |  Verificación: T6 en verde y suite de sv3 en verde
- [ ] T8: Tests rojos de la herramienta `tests/test_f077_contraste.py` de sv3 (R24–R26: listado de calendarios Sesame HR, token por entorno o `pedir_token`, sin `--api-key`, `https://`, faltas ⇒ ≠ 0 sin escribir, `--impacto` con el adaptador, informes sin nombres ni emails) y adaptar `test_f032_contraste.py` y `test_f032_campana.py`  |  Verificación: traza RED
- [ ] T9: `contrastar_festivos_sesame.py` (design §5.5)  |  Verificación: T8 en verde
- [ ] T10: Tests rojos de sv4 `services/partes-front/tests/test_f077_sin_sesame_sv4.py` (R20–R22: `FESTIVOS_SESAME_ENABLED` verdadero/falso, log de cableado, `CalendarioProvider(activo=…)`, vista de trabajador sin badge «contrato:» ni aviso de divergencia y con los mismos KPI) y adaptar los de sv4 de la lista cerrada de design §4  |  Verificación: traza RED
- [ ] T11: sv4 `config/settings.py`, `calendario_provider.py`, `web/app.py`, `trabajador_detail.html` y el CSS muerto (design §5.4); retirar `infrastructure/sesame/`, `validar_datos_sesame.py`, `test_f003_r1_sesame_client.py`, `test_f003_r13_jornada_contrato.py`, `test_f013_informe_sesame.py` y `tests/fixtures_sesame.py`  |  Verificación: T10 y los guardianes R20/R23/R31 de T1 en verde, suite de sv4 en verde, `node --check static/app.js` si se toca y parseo Jinja2 de la plantilla
- [ ] T12: Tests rojos de infra `tests/test_f077_infra_sesame.py` (R27–R30, lectura estática como la de F-032: secreto `sesame-token`, variables de sv3, sv4 solo `FESTIVOS_SESAME_ENABLED`, retiradas solo si están, validación `https://` y `SESAME-TOKEN` antes del primer `containerapp`, `-Quitar`, `create_*`, `add_secrets`, `00_vars` vacía, sin URL ni token en los `.ps1`, CRLF sin BOM) y retirar `tests/test_f032_infra_sesame.py`  |  Verificación: traza RED
- [ ] T13: `infra/add_sesame_partes.ps1`, `create_capps_partes.ps1`, `create_sv4_front.ps1`, `add_secrets_partes.ps1`, `00_vars_partes.ps1` (design §5.6), conservando el fin de línea de cada uno  |  Verificación: T12 en verde
- [ ] T14: Documentación: `CLAUDE.md` (lista cerrada), `harness/servicios.json`, `docs/ARCHITECTURE.md`, `infra/README_partes.md` y `README.md` (R33)  |  Verificación: T1 entero en verde y `python -m harness.servicios --validar`
- [ ] T15: `azure-apps/partes.md` (design §8): `git -C C:\Users\pgris\PycharmProjects\azure-apps pull --rebase` antes; solo ese documento; commit aparte en `azure-apps`, sin push; ante conflicto, PARAR y `blocked`  |  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1 --stat` con solo `partes.md`
- [ ] T16: Campaña de mutación del nivel sobre las líneas cambiadas y análisis de cada superviviente en `progress/mutacion_F-077.md`  |  Verificación: informe con cero supervivientes sin test o justificación aceptada
- [ ] T17: M0 (token rotado y, si se puede, de solo lectura; `SESAME-TOKEN` en `$KV`) y M1–M2 (contraste e impacto)  |  Verificación: MANUAL (humano), design §7, comando y resultado en `progress/impl_F-077.md`
- [ ] T18: M3–M6 (redespliegue apagado, encendido, portal y `-Quitar`); al encender, estado en `azure-apps/partes.md`  |  Verificación: MANUAL (humano), design §7, comando y resultado en `progress/impl_F-077.md`
- [ ] T19: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

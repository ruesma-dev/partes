<!-- specs/F-003-sesame-festivos-jornada/tasks.md -->
# F-003 · Integración sesame-api: festivos y jornada reales — Tareas

Rama: `feature/F-003-sesame-festivos-jornada`. Un commit por tarea
(`F-003 Tn: ...`). Tests junto a cada implementación; sin red ni BBDD
real (dobles y `httpx.MockTransport`).

- [ ] T1: `jornada_efectiva` en sv4 (`application/services/jornada_resolver.py`)
      y refactor de los 3 usos (`trabajador_detail`, `obra_detail`,
      `_sugerida`) para delegar en él, sin cambio de comportamiento.
      | Verificación: `test_f003_r12_*` (regla + los 3 usos dan lo mismo
      que antes) — `cd services/partes-front && python -m pytest -k f003_r12`
- [ ] T2: inaugurar `services/partes-persistencia/tests/` (conftest.py,
      dobles.py) + `jornada_efectiva` en sv3 y refactor de
      `_reclasificar_extras_jornada` L486-493 para delegar en él.
      | Verificación: `test_f003_r11_*` y regresión de splits dorados
      `test_f003_r15_*` — `cd services/partes-persistencia && python -m pytest -k "f003_r11 or f003_r15"`
- [ ] T3: `SesameApiClient` de sv4 (`infrastructure/sesame/`) con
      transporte inyectable + fixtures JSON del contrato real
      (festivos, calendarios, jornada, 404, 502, no-JSON, log sin clave).
      | Verificación: `test_f003_r1_*`, `test_f003_r20_*` (pytest sv4)
- [ ] T4: `CalendarioProvider` de sv4: caché TTL (DNI × año),
      *stale-while-error*, cascada DNI → por defecto → respaldo, y
      `jornada_contrato`. | Verificación: `test_f003_r4_*`,
      `test_f003_r5_*`, `test_f003_r6_*` (dobles del cliente, time
      monkeypatcheado)
- [ ] T5: settings sv4 (`SESAME_*` + `sesame_enabled`), wiring en
      `build_app` (inyectable, log CABLEADO/DESACTIVADO) y `.env.example`.
      | Verificación: `test_f003_r7_*` (sin configurar ⇒ respaldo y cero
      red; configurado ⇒ proveedor cableado)
- [ ] T6: vistas sv4 — festivos por trabajador en `trabajador_detail`
      (calendario + `dias_incompletos`), `obra_detail` con columna por
      calendario por defecto e `incompletos` por DNI de fila (añadir
      `dni` a `ObraMatrixRow`). | Verificación: `test_f003_r2_*`,
      `test_f003_r3_*` con TestClient + doble del proveedor
- [ ] T7: badge de jornada del contrato + aviso de divergencia en
      `trabajador_detail` (plantilla + contexto). | Verificación:
      `test_f003_r13_*`, `test_f003_r14_*` (contexto/HTML renderizado)
- [ ] T8: endpoint `GET /api/calendario` (rango <= 62 días, 422 si no).
      | Verificación: `test_f003_r16_*` (TestClient: per-DNI, default,
      422, degradación)
- [ ] T9: «+ Nuevo» — rejilla JS con marcas festivo/domingo desde
      `/api/calendario` y confirmación no bloqueante al enviar; CSS.
      | Verificación: `node --check services/partes-front/static/app.js`
      + parseo Jinja2 de `nuevo_parte.html`; comportamiento en navegador:
      MANUAL (humano) — crear un parte con un domingo y confirmar el aviso
- [ ] T10: aviso festivo/domingo en el preflight de aprobación (líneas
      con horas > 0). | Verificación: `test_f003_r18_*`
- [ ] T11: `SesameApiClient` de sv3 (gemelo de T3) +
      `SesameCalendarioLaboral` (cascada + respaldo, nunca propaga
      excepciones). | Verificación: `test_f003_r8_*`, `test_f003_r9_*`
- [ ] T12: wiring sv3 (settings `SESAME_*`, `interface_adapters/api/app.py`
      L87-95) y `_es_no_laborable` pasando el DNI del grupo al puerto;
      `.env.example`. | Verificación: `test_f003_r8_*` (festivo del
      calendario del trabajador ⇒ ordinarias a extra; sin configurar ⇒
      `test_f003_r10_*` JSON como hoy)
- [ ] T13: infra — `SESAME_API_BASE_URL` (redactada) y `SESAME_API_KEY`
      como `keyvaultref` (`sesame-api-key`) en manifiestos/scripts de
      sv3 y sv4; valores reales solo en `*.local.ps1`. SIN desplegar.
      | Verificación: MANUAL (humano) — revisar diff de `infra/` y
      confirmar que no viaja ningún secreto
- [ ] T14: actualizar `azure-apps/partes.md` (consumo de sesame-api:
      endpoints, `x-api-key`, degradación) y señalar el hueco P3
      (documento de sesame-api pendiente, dueño: sesame-api).
      | Verificación: MANUAL (humano) — R21, revisar el documento
- [ ] T15: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: `bash harness/init.sh`

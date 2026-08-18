<!-- specs/F-012-estudio-jornada-semanal/tasks.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Tareas

> F-012 es un estudio: sus tareas son de validación y decisión, no de
> código. Las tareas de implementación quedan enumeradas al final como
> **propuesta de tasks para F-014/F-015** (no se ejecutan en F-012; las
> hereda la spec de esas features una vez tomadas las decisiones D1–D8).
> Rigor recomendado para cerrar F-012: `documental` (D8).

## Tareas de F-012

- [x] T1: Redactar el estudio con datos reales (Sigrid vía sigrid-api solo
      lectura + BBDD `partes` dev), el análisis de casos, el inventario de
      fuentes y el modelo propuesto en `design.md`; requisitos del estudio
      (bloque A) y de la implementación (bloque B) en `requirements.md`.
      | Verificación: los tres ficheros existen y cubren R1–R7 (lectura del
      humano); `grep -nE "[0-9]{8}[A-Z]" specs/F-012-estudio-jornada-semanal/*.md`
      no devuelve nada (R7: sin DNIs).
- [ ] T2: Validación del humano de los hallazgos H1–H8 de `design.md` §3
      (en especial H2: un solo candef 9 y sin DNI; H5: la cuadrilla de 7
      con 48 → 42 → 35 h; H6: intensiva registrada como 7 + 0).
      | Verificación: MANUAL (humano) — anota «H validados» o las
      correcciones en `progress/current.md`; si quiere ver más datos, el SQL
      del anexo A se ejecuta con cualquier cliente de sigrid-api
      (`POST /api/sql/read`, `database=ruesma`, `max_rows<=1000`).
- [ ] T3: Decisiones D1–D8 de `design.md` §9 tomadas por el humano (fuente,
      regla del viernes, cuadrilla 42 vs 40+2, candef en Sigrid, UI de
      mantenimiento, orden con F-010, exclusión de líneas registradas,
      rigor/reparto).
      | Verificación: MANUAL (humano) — decisiones escritas en
      `progress/current.md` (el líder las copia a la spec de F-014).
- [ ] T4: Dar de alta en `harness/features.json` la feature de implementación
      **F-014 «Jornada del día por patrón semanal particularizable (extras
      sv3 + avisos sv4)»** con `sdd: true`, rigor `estandar`, dependencia
      declarada de F-010 según D6, y —si D5 = (b)— **F-015 «UI de
      mantenimiento de `empleado_jornada` en el portal»**; anotar en la
      descripción de F-011 que su fuente candidata es la misma tabla más
      `emphis.porjorlab` (H6/H7). Lo hace el LÍDER (el spec-author no edita
      `features.json`).
      | Verificación: `bash harness/init.sh` en verde tras el alta (valida
      el JSON) y `git log -1` con el commit del backlog.
- [ ] T5: Avisos al humano fuera del alcance de código: (a) `MO/0037` (el
      único candef 9) no tiene DNI en `emp` de Sigrid → sv3 no puede
      resolverlo por DNI; (b) los siete recursos de la cuadrilla H5 tienen
      candef 8 aunque hacen 9 h L–J (D4).
      | Verificación: MANUAL (humano) — acuse en `progress/current.md`.
- [ ] T6: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: exit code 0 (F-012 no toca código: los tests
      existentes siguen pasando).

## Propuesta de tasks para F-014 (NO se ejecutan en F-012)

Orden por dependencia; cada una un commit `F-014 Tn: …`; tests antes o
junto a la implementación; nada toca red ni BBDD real.

- T1: `jornada_resolver.py` de sv3: `PatronSemanal`, `patron_derivado`,
  `jornada_dia` (§6.3) + `tests/test_f014_r10_patron_derivado.py`,
  `test_f014_r12_candef_invalido.py` (fase RED primero).
  | Verificación: `pytest services/partes-persistencia/tests -k f014_r10 or f014_r12`.
- T2: Gemelo en sv4 + guardián `test_f014_r14_gemelos.py` (tabla de casos
  contra ambas copias) y regresión R11 (`test_f014_r11_regresion_candef8`:
  los dorados de F-003 intactos).
  | Verificación: `pytest services/partes-front/tests -k f014_r14 or f014_r11`
  y `pytest services/partes-persistencia/tests -k f003_r15`.
- T3: `EmpleadoJornadaOrm` en las DOS copias de `orm_models.py` +
  `test_f014_r17_orm_gemelos.py`.
  | Verificación: `pytest -k f014_r17`; `create_all` sobre SQLite en memoria
  crea `empleado_jornada`.
- T4: sv3 — puerto `JornadaEmpleadoPort`, repositorio SQLAlchemy, caché TTL
  en el conciliador, `jornada_dia` en `_reclasificar_extras_jornada`, log
  R25; tests R15, R16, R18, R19, R20, R25 (SQLite en memoria + dobles).
  | Verificación: `pytest services/partes-persistencia/tests -k f014`.
- T5: sv3 — settings `JORNADA_SEMANAL_POR_DEFECTO`, wiring en
  `interface_adapters/api/app.py`, `.env.example`.
  | Verificación: `pytest -k f003_r10_wiring` sigue verde + test de wiring
  nuevo (`test_f014_r15_wiring_sv3`).
- T6: sv4 — `JornadaEmpleadoProvider`, `get_jornadas_empleado` en el
  repositorio, `jornada_dia` en `trabajador_detail` / `obra_detail`, KPI
  con patrón (R22), `jornada_dia` opcional en `/api/sigrid/empleados`
  (R23); tests R21–R23 con TestClient + SQLite (`Settings(_env_file=None)`).
  | Verificación: `pytest services/partes-front/tests -k f014`;
  `node --check services/partes-front/static/app.js` si se toca; parseo
  Jinja2 de `trabajador_detail.html`.
- T7: (D7) excluir de `revert_extras_auto`/splits las líneas con
  `sigrid_estado` en {encolado, registrado} — o feature aparte si el
  humano lo prefiere. Test: línea registrada no se re-splitea.
  | Verificación: `pytest -k f014_d7`.
- T8: Documentación: `docs/ARCHITECTURE.md` (semántica 3 y 7),
  `docs/referencia/partes-proyecto.md` (§4.3, §5), `azure-apps/partes.md`
  (tabla nueva).
  | Verificación: revisión del reviewer contra C3/C5.
- T9: MANUAL (humano): tras desplegar sv4 (crea la tabla), sembrar
  `empleado_jornada` según D3/D4 (p. ej. las 7 filas de la cuadrilla con
  `jornada_semanal=42`, patrón 9,9,9,9,6, `desde='2026-05-01'`,
  `nota='cuadrilla H5 F-012'`) y comprobar en el portal el KPI y los avisos
  de un viernes.
  | Verificación: MANUAL (humano) — captura/acuse en `progress/`.
- T10: Ejecutar `bash harness/init.sh` en verde (+ `python -m
  harness.mutacion --feature F-014`).
  | Verificación: exit code 0; supervivientes analizados.

## Propuesta de tasks para F-015 (solo si D5 = (b))

- T1: rutas `GET/POST /admin/jornadas` en sv4 con validaciones R24
  (horas 0–24, `desde` < `hasta`, sin solapes por DNI), trazabilidad
  quién/cuándo, papelera lógica; plantilla `admin_jornadas.html`; tests
  `test_f015_r24_*` con TestClient.
- T2: enlace desde la vista trabajador («jornada particularizada: editar»).
- T3: `bash harness/init.sh` en verde.

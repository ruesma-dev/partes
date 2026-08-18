<!-- specs/F-012-estudio-jornada-semanal/tasks.md -->
# F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable — Tareas

> F-012 es un estudio: sus tareas son de validación y cierre, no de
> código. Las tareas de implementación quedan enumeradas al final como
> **propuesta de tasks para F-015 y F-016** (no se ejecutan en F-012; las
> hereda la spec de esas features). Rigor recomendado para cerrar F-012:
> `documental` (D8). Versión 2 (2026-08-18) tras las decisiones del humano.

## Tareas de F-012

- [x] T1: Redactar el estudio con datos reales (Sigrid vía sigrid-api solo
      lectura + BBDD `partes` dev), el análisis de la regla, el inventario
      de fuentes y el modelo en `design.md`; requisitos del estudio
      (bloque A) y de la implementación (bloque B) en `requirements.md`.
      Rehecho con las decisiones firmes del humano del 2026-08-18
      (derivación por candef, último laborable, excepciones en tabla).
      | Verificación: los tres ficheros existen y cubren R1–R7 (lectura del
      humano); `grep -nE "[0-9]{8}[A-Z]" specs/F-012-estudio-jornada-semanal/*.md`
      no devuelve nada (R7: sin DNIs).
- [ ] T2: Validación del humano de los hallazgos H1–H8 de `design.md` §3
      (los datos no cambian con la v2) y de la tabla de casos del §4 (en
      especial B–E: festivo en viernes/miércoles/jueves+viernes/solo lunes,
      y M: candef fuera del mapa).
      | Verificación: MANUAL (humano) — anota «H y casos validados» o las
      correcciones en `progress/current.md`; el SQL del anexo A se
      reproduce con cualquier cliente de sigrid-api (`POST /api/sql/read`,
      `database=ruesma`, `max_rows<=1000`).
- [ ] T3: Cerrar las decisiones que quedan abiertas (`design.md` §9.2):
      D-A1 (mapa en env espejo de sv3+sv4 vs tabla de configuración),
      D-A2 (candef válido fuera del mapa: S=40 + WARNING recomendado),
      D-A3 (sin calendario cableado → último laborable = viernes).
      | Verificación: MANUAL (humano) — decisiones escritas en
      `progress/current.md`; el líder las copia a la spec de F-015.
- [ ] T4: Backlog (lo hace el LÍDER; el spec-author no edita
      `features.json`): dar de alta **F-015 «Jornada del día por jornada
      semanal derivada del candef y último laborable (extras sv3 + avisos
      sv4) + tabla de excepciones `empleado_jornada`»** (`sdd: true`, rigor
      `estandar`, prerrequisitos F-014 y —recomendado— F-010) y **F-016
      «Pantalla de administración de `empleado_jornada` en el portal»**
      (`sdd: true`, rigor `estandar`, después de F-015); anotar en F-011
      que su fuente candidata es `empleado_jornada` + `emphis.porjorlab`
      (H6/H7). F-014 ya está dada de alta (candef en Sigrid, documental).
      | Verificación: `bash harness/init.sh` en verde tras el alta y
      `git log -1` con el commit del backlog.
- [ ] T5: MANUAL (humano) — F-014: pedir a RRHH/Administración el cambio en
      Sigrid (candef 9 en la hora por defecto HLOF de `MO/0006`, `MO/0007`,
      `MO/0008`, `MO/0031`, `MO/0366`, `MO/0405`, `MO/0456`; DNI en `emp`
      para `MO/0037`) y verificarlo por sigrid-api en solo lectura con el
      SQL de H1/H2 del anexo A. Debe estar cerrado ANTES de mergear F-015
      (riesgo §10.6).
      | Verificación: MANUAL (humano) — resultado del SQL (7 recursos con
      candef 9; `MO/0037` con DNI) anotado en `progress/` de F-014.
- [ ] T6: Ejecutar `bash harness/init.sh` en verde.
      | Verificación: exit code 0 (F-012 no toca código: los tests
      existentes siguen pasando).

## Propuesta de tasks para F-015 (NO se ejecutan en F-012)

Prerrequisitos: F-014 cerrada (candef corregidos en Sigrid); F-010
recomendada antes (D6). Orden por dependencia; cada una un commit
`F-015 Tn: …`; tests antes o junto a la implementación; nada toca red ni
BBDD real.

- T1: `jornada_resolver.py` de sv3: `parsear_mapa_semanal`,
  `jornada_semanal_de`, `es_ultimo_laborable`, `Excepcion`, `jornada_dia`
  (§6.2) + `tests/test_f015_r10_mapa_candef.py`,
  `test_f015_r12_candef_invalido.py`, `test_f015_r13_ultimo_laborable.py`,
  `test_f015_r14_finde_y_semana_festiva.py`,
  `test_f015_r15_calendario_no_registros.py` (fase RED primero; calendario
  fake por *callable*).
  | Verificación: `pytest services/partes-persistencia/tests -k f015_r1`.
- T2: Gemelo en sv4 + guardián `test_f015_r19_gemelos.py` (tabla de casos
  contra ambas copias) y regresión R11 (`test_f015_r11_regresion_candef8`:
  los dorados de F-003 intactos + semana con festivo y candef 8 → 8).
  | Verificación: `pytest services/partes-front/tests -k f015_r19 or f015_r11`
  y `pytest services/partes-persistencia/tests -k f003_r15`.
- T3: `EmpleadoJornadaOrm` en las DOS copias de `orm_models.py` +
  `test_f015_r18_orm_gemelos.py`.
  | Verificación: `pytest -k f015_r18`; `create_all` sobre SQLite en memoria
  crea `empleado_jornada`.
- T4: sv3 — puerto `JornadaEmpleadoPort`, repositorio SQLAlchemy de
  excepciones, caché TTL en el conciliador, `jornada_dia` en
  `_reclasificar_extras_jornada` con `es_laborable` ligado al DNI del
  grupo, degradación (R23), log (R28); tests R16, R17, R20–R23, R28
  (SQLite en memoria + dobles + calendario fake).
  | Verificación: `pytest services/partes-persistencia/tests -k f015`.
- T5: sv3 — settings `JORNADA_SEMANAL_POR_CANDEF` (fail-fast),
  `JORNADA_SEMANAL_POR_DEFECTO`, `JORNADA_CACHE_TTL_S`; wiring en
  `interface_adapters/api/app.py`; `.env.example`.
  | Verificación: `pytest -k f003_r10_wiring` sigue verde + test de wiring
  nuevo (`test_f015_wiring_sv3`).
- T6: sv3 — D7: excluir de `revert_extras_auto`/`fetch_registros_para_recurso`
  las líneas con `sigrid_estado` en {encolado, registrado} y las de
  documentos `approved`; test: línea registrada no se re-splitea al
  cambiar la jornada.
  | Verificación: `pytest -k f015_d7`.
- T7: sv4 — `JornadaEmpleadoProvider`, `get_jornadas_empleado` en el
  repositorio, `jornada_dia` en `trabajador_detail` / `obra_detail`, KPI
  (R25), `jornada_dia` opcional en `/api/sigrid/empleados` (R26); settings
  y wiring; tests R24–R26 con TestClient + SQLite + doble de calendario
  (`Settings(_env_file=None)`).
  | Verificación: `pytest services/partes-front/tests -k f015`;
  `node --check services/partes-front/static/app.js` si se toca; parseo
  Jinja2 de `trabajador_detail.html`.
- T8: Documentación: `docs/ARCHITECTURE.md` (semántica 3 y 7),
  `docs/referencia/partes-proyecto.md` (§4.3, §5), `azure-apps/partes.md`
  (tabla nueva y variables), manifiestos de `infra/` con la variable
  espejo si D-A1 = env.
  | Verificación: revisión del reviewer contra C3/C5.
- T9: MANUAL (humano): tras desplegar sv3 y sv4 (sv4 crea la tabla vacía),
  comprobar en el portal el KPI y los avisos de un viernes de la cuadrilla
  (candef 9 ya en Sigrid): viernes de 6 h sin aviso, KPI «9 h · 42 h/sem ·
  último laborable 6 h».
  | Verificación: MANUAL (humano) — captura/acuse en `progress/`.
- T10: Ejecutar `bash harness/init.sh` en verde (+ `python -m
  harness.mutacion --feature F-015`).
  | Verificación: exit code 0; supervivientes analizados.

## Propuesta de tasks para F-016 (UI de excepciones; después de F-015)

- T1: rutas `GET/POST /admin/jornadas` en sv4 con validaciones R27
  (al menos S o patrón; horas 0–24; `desde` < `hasta`; sin solapes por
  DNI), trazabilidad quién/cuándo, papelera lógica; plantilla
  `admin_jornadas.html`; tests `test_f016_r27_*` con TestClient.
- T2: enlace desde la vista trabajador («jornada: añadir excepción») y
  badge en el KPI cuando la S aplicada viene de una excepción.
- T3: `bash harness/init.sh` en verde (+ mutación).

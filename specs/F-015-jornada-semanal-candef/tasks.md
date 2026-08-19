<!-- specs/F-015-jornada-semanal-candef/tasks.md -->
# F-015 · Jornada del día por jornada semanal derivada del candef y último laborable — Tareas

Rama: **`feature/F-015-jornada-semanal-candef`** (ya creada desde `dev`; no se
crea otra). Un commit **local** por tarea, mensaje `F-015 Tn: …`. Sin `git
push` y sin PR: eso lo hace el humano.

Rigor **`estandar`** ⇒ fase **RED** con traza real en `progress/impl_F-015.md`
para R10, R13, R16, R20, R24, R31 y R32; **cobertura** de las líneas cambiadas
≥ umbral; **campaña de mutación** con los supervivientes analizados.

Reglas que no se negocian durante la ejecución:

- **Ningún test toca red ni BBDD**: SQLite en memoria, dobles y calendario
  fake. En sv4, `Settings(_env_file=None)`.
- **Los tests dorados de F-003 no se modifican.** Si uno se pone rojo, la
  regresión cero (R11) se rompió: **parar** y avisar, no adaptar el test.
- **Quien toca una copia de `orm_models.py` toca la otra en el mismo commit.**
- Si la spec resulta ambigua o una herramienta falla de forma inesperada:
  `blocked`, motivo en `progress/current.md`, parar. Nada de workarounds.

> **PUERTA DE ENTREGA (R35).** Terminar las tareas **no** autoriza el merge:
> la rama no se mergea a `dev` ni se despliega hasta que **F-014** esté
> verificada en Sigrid (7 recursos con `candef = 9` y el octavo con DNI en
> `emp`). Ver `design.md` §11.2 — la ventana peligrosa es F-014 **sin** F-015.

---

- [x] **T1**: Resolutor de sv3 —
      `services/partes-persistencia/application/services/jornada_resolver.py`:
      `parsear_mapa_semanal`, `jornada_semanal_de`, `es_ultimo_laborable`,
      `Excepcion`, `DetalleJornada`, `detalle_jornada_dia` y `jornada_dia`
      (`design.md` §5.1). **`jornada_efectiva` y `candef_valido` no se tocan.**
      Tests **primero** (fase RED por `ImportError`):
      `test_f015_r10_mapa_candef.py`, `test_f015_r12_candef_invalido.py`,
      `test_f015_r13_ultimo_laborable.py`,
      `test_f015_r14_finde_y_semana_festiva.py`,
      `test_f015_r15_calendario_no_registros.py` (calendario fake por
      *callable*; semana de referencia 2026-03-16…2026-03-22).
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k f015`
      en verde tras la implementación; traza de la fase RED pegada en
      `progress/impl_F-015.md`.

- [x] **T2**: Gemelo de sv4 —
      `services/partes-front/application/services/jornada_resolver.py` con la
      misma API pública y el mismo comportamiento (docstring propio, como
      hoy). Guardián `tests/test_f015_r19_jornada_resolver_gemelo.py` en la
      **raíz**: firmas idénticas (`inspect.signature`) + tabla de ≥ 20 casos
      (los de R13, R14 y R16) contra ambas copias. Test de regresión
      `test_f015_r11_regresion_candef8.py` en sv3 (candef 8 / S 40 con y sin
      festivos, y con `calendario=None`).
      | Verificación: `python -m pytest tests -q -k f015_r19`;
      `python -m pytest services/partes-persistencia/tests services/partes-front/tests -q -k "f003 or f015_r11"`
      en verde **sin haber tocado ningún test de F-003**.

- [x] **T3**: `EmpleadoJornadaOrm` (`design.md` §6) en las **DOS** copias de
      `infrastructure/database/orm_models.py`, byte-idénticas, con
      `server_default` en `origen` e `is_active` y `index=True` en `dni_norm`;
      docstring «CINCO tablas». Actualizar el guardián
      `tests/test_f010_orm_models_gemelos.py` (`TABLAS` a cinco + columnas
      literales de la tabla nueva, **sin relajar nada**) y añadir
      `tests/test_f015_r29_guardian_cinco_tablas.py`. Tests R18 y R30 en los
      dos servicios (`create_all` sobre SQLite en memoria crea la tabla;
      `ddl_complementario()` emite sus `ALTER … ADD COLUMN IF NOT EXISTS` y su
      `CREATE INDEX IF NOT EXISTS`).
      | Verificación: `python -m pytest tests -q -k "f010 or f015_r29"`;
      `python -m pytest services/partes-persistencia/tests services/partes-front/tests -q -k "f015_r18 or f015_r30"`;
      `cmp` de las dos copias sin diferencias.

- [x] **T4**: sv3 · excepciones — puerto
      `domain/ports/jornada_empleado_port.py` (`JornadaEmpleadoRow`,
      `JornadaEmpleadoPort.fetch_jornadas()`) y adaptador
      `infrastructure/database/sqlalchemy_jornada_repository.py` (lee
      `EmpleadoJornadaOrm` con `is_active`). En `RecursoConciliador`:
      parámetros `jornadas=None` y `jornada_cache_ttl_s=600`, caché TTL de la
      tabla entera, `_excepcion_para(dni, fecha)` y degradación silenciosa con
      un WARNING por pasada. Tests R16, R17 y R22.
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k "f015_r16 or f015_r17 or f015_r22"`;
      con `jornadas=None` los tests de F-003 siguen verdes.

- [x] **T5**: sv3 · cómputo — en `_reclasificar_extras_jornada`, sustituir
      `candef_efectivo` por `detalle_jornada_dia(...)` con `es_laborable`
      ligado al DNI del grupo; **la rama de día no laborable no se toca**;
      `objetivo_extra = total − detalle.horas`. WARNING de candef fuera del
      mapa deduplicado por recurso y pasada (R10), señal de degradación en las
      consultas del último laborable (R23) y log de trazabilidad (R28). Tests
      R20, R21, R23 y R28.
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k "f015_r20 or f015_r21 or f015_r23 or f015_r28"`;
      `python -m pytest services/partes-persistencia/tests -q -k f003_r15` (dorados) en verde.

- [x] **T6**: sv3 · congelados (D7, `design.md` DA3) —
      `sqlalchemy_parte_repository.py`: `revert_extras_auto()` salta las líneas
      congeladas (`sigrid_estado` en {`encolado`, `registrado`} o documento
      `approved`) y `fetch_registros_para_recurso()` devuelve además
      `sigrid_estado` y `doc_approved`. En el conciliador, `_congelado(reg)`
      escrito una sola vez: las congeladas **suman** en el total del día y se
      excluyen de los candidatos a recorte y de pivote; si el día no cuadra sin
      tocarlas, WARNING y ningún split. Tests R31 y R32 (fase RED primero).
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k "f015_r31 or f015_r32"`;
      un día sin congelados produce **exactamente** los mismos splits que antes
      del cambio (caso de regresión dentro del propio test).

- [x] **T7**: sv3 · configuración y cableado — `config/settings.py`:
      `jornada_semanal_por_candef` (`8:40,9:42`) y `jornada_cache_ttl_s`
      (`600`); `interface_adapters/api/app.py`: `parsear_mapa_semanal(...)`
      (fail-fast al arrancar) y `SqlAlchemyJornadaRepository` inyectado al
      conciliador; `.env.example`. Test `test_f015_r10_fail_fast_wiring` (mapa
      mal formado ⇒ la app no se construye) y test de wiring del conciliador.
      | Verificación: `python -m pytest services/partes-persistencia/tests -q -k "f015 or f003_r10_wiring"`.

- [x] **T8**: sv4 · lectura de excepciones —
      `application/services/jornada_provider.py` (`JornadaEmpleadoProvider`
      con caché TTL y degradación silenciosa),
      `infrastructure/database/parte_repository.py::list_jornadas_empleado()`,
      `config/settings.py` con las **mismas dos** variables y los **mismos**
      defaults, `build_app(..., jornada_provider=None)` + fail-fast del mapa,
      `.env.example`. Tests R10, R12, R13, R16, R17 en sv4 y
      `tests/test_f015_r33_variable_espejo.py` en la raíz.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f015`;
      `python -m pytest tests -q -k f015_r33`.

- [x] **T9**: sv4 · avisos y KPI — `trabajador_detail` (`dias_incompletos` por
      `jornada_dia` del día + contexto `jornada_kpi`), `obra_detail`
      (`incompletos` por fila y día con el DNI de la fila) y
      `templates/trabajador_detail.html` (KPI: candef efectivo, `S` aplicada
      con su origen, jornada del último laborable). Tests R24 y R25.
      | Verificación: `python -m pytest services/partes-front/tests -q -k "f015_r24 or f015_r25"`;
      parseo Jinja2 de `trabajador_detail.html`;
      `python -m pytest services/partes-front/tests -q -k f003` en verde.

- [x] **T10**: sv4 · «+ Nuevo» — `GET /api/sigrid/empleados` mantiene
      `jornada_sugerida` intacta y añade `jornada_dia` **solo** cuando llega
      `fecha` válida (R26). Si se toca `static/app.js`, `node --check`.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f015_r26`;
      `node --check services/partes-front/static/app.js` si procede.

- [x] **T11**: Documentación (R34) — `docs/ARCHITECTURE.md` semántica 3
      (exceso sobre la jornada **del día**: candef, salvo el último laborable
      de la semana, que recibe el resto de la jornada semanal derivada del
      candef) y semántica 7 (**cinco** tablas);
      `docs/referencia/partes-proyecto.md` §4.3 y §5;
      `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (tabla nueva y
      variables nuevas, **commit local, sin push**); `infra/create_capps_partes.ps1`
      con `JORNADA_SEMANAL_POR_CANDEF=8:40,9:42` en sv3 **y** sv4.
      | Verificación: `grep -n "Cuatro tablas" docs/ARCHITECTURE.md` sin
      resultados; revisión del reviewer contra C3/C5.

- [ ] **T12**: **MANUAL (humano)** — tras desplegar sv3 y sv4 (sv4 crea la
      tabla vacía al arrancar):
      1. En el log de arranque de **ambos**, «esquema inicializado (N
         sentencias complementarias)» con N mayor que el de F-010; en la base
         `partes`, `\d empleado_jornada` muestra las 19 columnas y el índice
         `ix_empleado_jornada_dni_norm`.
      2. En el portal, un trabajador de la cuadrilla (ya con candef 9 en
         Sigrid): viernes de 6 h **sin** aviso de jornada incompleta y KPI
         «9 h · 42 h/sem · último laborable 6 h».
      3. Un parte ya aprobado/registrado **no** cambia su desglose tras la
         primera pasada de sv3 con la versión nueva (R31/R32).
      | Verificación: MANUAL (humano) — acuse o captura anotada en
      `progress/impl_F-015.md`.

- [x] **T13**: Ejecutar `bash harness/init.sh` en verde y la campaña
      `python -m harness.mutacion --feature F-015`, con los supervivientes
      analizados por escrito.
      | Verificación: exit code 0 en `bash harness/init.sh` (comando limpio,
      sin pipes ni `tail`); informe de mutación en `progress/impl_F-015.md`.

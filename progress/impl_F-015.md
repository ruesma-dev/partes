<!-- progress/impl_F-015.md -->
# F-015 · Jornada del día por jornada semanal derivada del candef y último laborable — informe del implementer

Rama `feature/F-015-jornada-semanal-candef` (desde `dev` `cf77e6a`) · rigor
**estandar** · spec aprobada por el humano (§13 bis y §13 ter del `design.md`)
· **13 commits**, uno por tarea más uno de higiene, y un commit local en
`azure-apps`. **T12 es MANUAL del humano y queda pendiente** (sección 7).

## 1. Qué cambió, en una frase

La jornada teórica de un día deja de ser plana: es el `candef` de Sigrid de
lunes a jueves y **el resto de la jornada semanal el último día laborable de
esa semana** (`max(0, S − 4·candef)`), con `S` derivada de un mapa
configurable espejo en sv3 y sv4 y con excepciones por trabajador en la tabla
nueva `empleado_jornada`; sv3 reparte extras contra esa jornada (sin tocar
nunca lo ya registrado en Sigrid) y sv4 avisa, informa y sugiere con la
misma regla. Con `candef = 8` **no se mueve ni una hora**.

## 2. Ficheros tocados

### Producción

| Fichero | Qué |
|---|---|
| `services/partes-persistencia/application/services/jornada_resolver.py` | **+** `parsear_mapa_semanal`, `jornada_semanal_de`, `es_ultimo_laborable`, `Excepcion`, `DetalleJornada`, `detalle_jornada_dia`, `jornada_dia`. `jornada_efectiva` y `candef_valido` **intactas** |
| `services/partes-front/application/services/jornada_resolver.py` | **gemelo**: misma API pública y mismo comportamiento (docstring propio) |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | `EmpleadoJornadaOrm` (19 columnas) + docstring «CINCO tablas» |
| `services/partes-front/infrastructure/database/orm_models.py` | **byte-idéntico** al anterior (`cmp` sin diferencias) |
| `services/partes-persistencia/domain/ports/jornada_empleado_port.py` | **nuevo** · `JornadaEmpleadoRow` + `JornadaEmpleadoPort.fetch_jornadas()` |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | **nuevo** · adaptador que lee `empleado_jornada` activa |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | `mapa_semanal` / `jornadas` / `jornada_cache_ttl_s`; `_dni_grupo`, `_es_laborable_para`, `_jornadas_index`, `_excepcion_para`, `_detalle_jornada`; jornada del día en `_reclasificar_extras_jornada`; congelados (R32); aviso de mapa (R10) y traza (R28); regla `esta_congelado` |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | `revert_extras_auto()` salta congelados (R31); `fetch_registros_para_recurso()` devuelve `sigrid_estado` y `doc_approved` |
| `services/partes-persistencia/config/settings.py` | `jornada_semanal_por_candef` (`8:40,9:42`) y `jornada_cache_ttl_s` (600) |
| `services/partes-persistencia/interface_adapters/api/app.py` | `construir_mapa_semanal()` (fail-fast, lo PRIMERO de `build_app`) + `SqlAlchemyJornadaRepository` al conciliador |
| `services/partes-front/application/services/jornada_provider.py` | **nuevo** · `JornadaEmpleadoProvider` (caché TTL, vigencia, degradación silenciosa) |
| `services/partes-front/infrastructure/database/parte_repository.py` | `list_jornadas_empleado()` |
| `services/partes-front/config/settings.py` | las **mismas dos** variables con los **mismos** defaults |
| `services/partes-front/interface_adapters/web/app.py` | `build_app(..., jornada_provider=None)` + fail-fast del mapa; `trabajador_detail` (avisos + `jornada_kpi`); `obra_detail` (avisos por fila y día); `sigrid_empleados` (`fecha` → `jornada_dia`) |
| `services/partes-front/templates/trabajador_detail.html` | KPI de jornada: `S` aplicada con su origen, último laborable y patrón |

### Tests (todos nuevos salvo el guardián de F-010)

| Fichero | Requisito |
|---|---|
| `tests/test_f015_r19_jornada_resolver_gemelo.py` | R19 · guardián de los dos resolutores (API + 27 casos + barrido de 3 semanas) |
| `tests/test_f015_r29_guardian_cinco_tablas.py` | R29 · el guardián de F-010 muerde con la tabla nueva |
| `tests/test_f015_r33_variable_espejo.py` | R33 · mismo default en los dos `config/settings.py` |
| `tests/test_f010_orm_models_gemelos.py` | **modificado** · `TABLAS` a cinco + columnas literales de `empleado_jornada` (sin relajar nada) |
| sv3: `…r10_mapa_candef`, `…r10_fail_fast_wiring`, `…r11_regresion_candef8`, `…r12_candef_invalido`, `…r13_ultimo_laborable`, `…r14_finde_y_semana_festiva`, `…r15_calendario_no_registros`, `…r16_excepciones`, `…r17_tabla_caida_o_vacia`, `…r18_orm_empleado_jornada`, `…r20_computo_ultimo_laborable`, `…r21_hora_candef_intacto`, `…r22_sin_dni`, `…r23_degradado_review`, `…r28_log_trazable`, `…r30_ddl_empleado_jornada`, `…r31_revert_respeta_congelados`, `…r32_congelados_cuentan_no_se_tocan` | R10–R32 |
| sv4: `…r10_mapa_candef_sv4`, `…r12_candef_invalido_sv4`, `…r13_ultimo_laborable_sv4`, `…r16_excepciones_sv4`, `…r17_tabla_caida_o_vacia_sv4`, `…r18_orm_empleado_jornada_sv4`, `…r24_avisos`, `…r25_kpi`, `…r26_sugerida_fecha`, `…r30_ddl_empleado_jornada_sv4` | R10–R30 |
| `services/partes-persistencia/tests/dobles.py`, `services/partes-front/tests/dobles.py` | `es_laborable_fake`, `JornadasFake`, `FabricaSesionSqlite` (sv3), `sembrar_lineas`, `estado_lineas`, `sembrar_jornadas` |

### Documentación e infra

`docs/ARCHITECTURE.md` (semánticas 3 y 7), `docs/referencia/partes-proyecto.md`
(§4.3 y §5, con §5.4 nueva), `infra/create_capps_partes.ps1` y
`infra/create_sv4_front.ps1` (la variable en sv3 **y** sv4), `CLAUDE.md`
(lista cerrada de duplicación), `.gitignore` (sección 6, decisión DI5) y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local `a05e1f1`,
**sin push**).

**Sin cambios en sv1, sv2 ni sv5.** Sin cambios en `static/app.js`
(`node --check` en verde igualmente). Ni una columna nueva en
`parte_registros` ni en `parte_documents`.

## 3. Tarea por tarea, con la verificación real

### T1 · Resolutor de sv3 (commit `987d1f3`)

Los siete elementos nuevos de `design.md` §5.1, como **funciones puras**: no
abren BBDD, no llaman a Sesame, no loguean. El calendario llega ya ligado al
DNI como *callable*.

**Fase RED (traza real).** `python -m pytest services/partes-persistencia/tests -q -k f015`:

```
tests\test_f015_r13_ultimo_laborable.py:19: in <module>
    from application.services.jornada_resolver import (
E   ImportError: cannot import name 'detalle_jornada_dia' from 'application.services.jornada_resolver'
...
ERROR tests/test_f015_r10_mapa_candef.py
ERROR tests/test_f015_r12_candef_invalido.py
ERROR tests/test_f015_r13_ultimo_laborable.py
ERROR tests/test_f015_r14_finde_y_semana_festiva.py
ERROR tests/test_f015_r15_calendario_no_registros.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!
112 deselected, 5 errors in 2.30s
```

**Verde.** `82 passed, 112 deselected in 2.13s` (`-k f015`); suite de sv3
entera `194 passed`.

### T2 · Gemelo de sv4, guardián R19 y regresión (commit `0ddd78b`)

El bloque de F-015 se copió **verbatim** a sv4 (docstring propio, como ya
hacía F-003) y `tests/test_f015_r19_jornada_resolver_gemelo.py` compara **API
pública y comportamiento**: presencia y firmas de las 7 funciones, campos de
las 2 dataclases, nada público de más en una copia, tabla de **27 casos**
(R13 + R14 + R16), barrido de 3 semanas × 7 días × 3 candef, parseo del mapa
y sus errores, `jornada_efectiva`/`candef_valido` todavía gemelas, y —lo
importante— que el guardián **muerde**: se altera `semanal - 4.0 * c` en una
copia dentro de `tmp_path` y se exige que el resultado cambie.

`test_f015_r11_regresion_candef8.py` (sv3) fija la regresión: la semana
completa día a día con 8/6/10 h, con festivos, y con `calendario=None`.

**Verificación.** `python -m pytest tests -q -k f015_r19` → `58 passed`.
`python -m pytest services/partes-persistencia/tests -q -k "f003 or f015_r11"`
→ `125 passed, 99 deselected`, **sin haber tocado ni un test de F-003**.

### T3 · `empleado_jornada` en las dos copias del ORM (commit `482252b`)

19 columnas (ver 4·DI2), `index=True` en `dni_norm`, `server_default` en
**todas** las NOT NULL, docstring de «CINCO tablas». Las dos copias se
resincronizan por copia literal y `cmp` no da diferencias. El guardián de
F-010 pasa a cinco tablas y gana la lista literal de las columnas nuevas; la
lista de las 56 de `parte_registros` **no se toca**.

**Verificación.** `python -m pytest tests -q -k "f010 or f015_r29"` →
`22 passed`. `-k "f015_r18 or f015_r30"` en los dos servicios →
`17 passed` cada uno. `cmp` de las dos copias: sin salida.

### T4 · sv3, lectura de excepciones (commit `4108b07`)

Puerto en `domain/`, adaptador en `infrastructure/`, y en el conciliador la
caché TTL de la tabla entera (DA8: se lee una vez por pasada y se indexa por
DNI), `_excepcion_para(dni, fecha)` con vigencia `desde ≤ f < hasta` y
`_detalle_jornada(...)`, que es donde se compone calendario + excepción +
resolutor.

**Fase RED (traza real).** `-k "f015_r16 or f015_r17 or f015_r22"`:

```
tests\test_f015_r16_excepciones.py:20: in <module>
    from domain.ports.jornada_empleado_port import JornadaEmpleadoRow
E   ModuleNotFoundError: No module named 'domain.ports.jornada_empleado_port'
...
ERROR tests/test_f015_r16_excepciones.py
ERROR tests/test_f015_r17_tabla_caida_o_vacia.py
ERROR tests/test_f015_r22_sin_dni.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
241 deselected, 3 errors in 2.15s
```

**Verde.** `29 passed, 241 deselected`; suite de sv3 `270 passed`. Con
`jornadas=None` (el default) los tests de F-003 siguen verdes.

### T5 · sv3, el cómputo (commit `4efd1c1`)

En la rama laborable, `candef_efectivo` se sustituye por
`detalle_jornada_dia(...)`; la rama de día no laborable **no se toca** y sigue
yendo delante. Se añaden el WARNING de candef fuera del mapa (deduplicado por
recurso y pasada) y la marca de trazabilidad de R28.

**Fase RED (traza real).** `-k "f015_r20 or f015_r21 or f015_r23 or f015_r28 or f015_r10"`:

```
_________________ test_f015_r20_seis_horas_un_viernes_cuadran _________________

    def test_f015_r20_seis_horas_un_viernes_cuadran() -> None:
        """Escenario A: el viernes la jornada es 42 - 36 = 6."""
>       assert _splits([registro(1, fecha_int=VIERNES, horas=6.0)]) == []
E       AssertionError: assert [{'normal_id'...': -3.0, ...}] == []
E         Left contains one more item: {'normal_id': 1, 'horas_norm': 9.0, 'horas_orig': 6.0, 'extra_horas': -3.0, ...}

tests\test_f015_r20_computo_ultimo_laborable.py:63: AssertionError
...
23 failed, 47 passed, 249 deselected in 2.36s
```

Esa traza **es** el problema que F-015 viene a resolver: el viernes de 6 h de
la cuadrilla generaba `extra −3` todas las semanas.

**Verde.** Suite de sv3 `319 passed`, dorados de F-003 incluidos.

### T6 · Congelados (commit `92ad6b7`)

`revert_extras_auto()` deja de tocar las líneas `encolado`/`registrado` o de
un parte `approved`; `fetch_registros_para_recurso()` trae `sigrid_estado` y
`doc_approved`; en el conciliador las congeladas suman en el total pero se
excluyen de candidatos y de pivote, y si el día no cuadra sin tocarlas no se
genera **ningún** split y se avisa. La regla se escribe **una vez**
(`esta_congelado`, en `application/`) y la importa el repositorio.

**Fase RED (traza real).** `-k "f015_r31 or f015_r32"`:

```
______________ test_f015_r31_una_extra_auto_registrada_sobrevive ______________
        revertidos = _repo(fabrica).revert_extras_auto()
>       assert revertidos == 0
E       assert 1 == 0
tests\test_f015_r31_revert_respeta_congelados.py:53: AssertionError

_____________ test_f015_r32_la_linea_congelada_nunca_es_el_pivote _____________
>       assert _resumen(_splits(regs)) == [(1, 4.0, -2.0)]
E       assert [(2, 6.0, -2.0)] == [(1, 4.0, -2.0)]
E         At index 0 diff: (2, 6.0, -2.0) != (1, 4.0, -2.0)
tests\test_f015_r32_congelados_cuentan_no_se_tocan.py:67: AssertionError

___________ test_f015_r32_un_dia_entero_congelado_no_genera_splits ____________
>           assert _splits(regs) == []
E           AssertionError: assert [{'normal_id'...s': 2.0, ...}] == []
E             Left contains one more item: {'normal_id': 1, 'horas_norm': 8.0, 'horas_orig': 10.0, 'extra_horas': 2.0, ...}
tests\test_f015_r32_congelados_cuentan_no_se_tocan.py:91: AssertionError
...
14 failed, 8 passed, 322 deselected in 2.45s
```

**Verde.** Suite de sv3 `344 passed`. El caso de regresión («un día sin
congelados da exactamente los mismos splits») está dentro del propio test.

### T7 · Configuración y cableado de sv3 (commit `11862f0`)

`construir_mapa_semanal(settings)` es **lo primero** de `build_app`: con el
mapa mal escrito el servicio no llega ni a abrir PostgreSQL. Se prueba la
función (que sí se puede levantar en la suite, como hizo F-003 con
`construir_calendario`) y se comprueba sobre el fuente que el orden en
`build_app` es el correcto y que el conciliador recibe mapa, repositorio de
excepciones y TTL.

**Verificación.** `-k "f015 or f003_r10_wiring"` → suite de sv3
`360 passed`.

### T8 · sv4, lectura de excepciones (commit `828092d`)

`JornadaEmpleadoProvider` (mismo patrón que `CalendarioProvider`: la clase
decide, la lectura entra como *callable*), `list_jornadas_empleado()`, las dos
variables espejo, `build_app(..., jornada_provider=None)` con fail-fast del
mapa, y el guardián de la raíz que compara los dos `config/settings.py`.

**Verificación.** `python -m pytest services/partes-front/tests -q -k f015`
→ `104 passed`; `python -m pytest tests -q -k f015_r33` → `6 passed`.

### T9 · Avisos y KPI de sv4 (commit `133c945`)

`dias_incompletos` y `incompletos` comparan contra `jornada_dia` del día (con
el calendario y la excepción de **ese** trabajador); el contexto gana
`jornada_kpi` y la plantilla lo pinta.

**Fase RED (traza real).** Reproducida contra el árbol de T8 (`828092d`) en un
worktree desechable, con el fichero de tests de T9 copiado dentro:

```
____________ test_f015_r24_el_viernes_de_6_horas_no_es_incompleto _____________

    def test_f015_r24_el_viernes_de_6_horas_no_es_incompleto() -> None:
        """Escenario A: 42 - 36 = 6 es la jornada de ese viernes."""
>       assert _incompletos_trabajador([
            {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
        ]) == set()
E       AssertionError: assert {'2026-03-20'} == set()
E         Extra items in the left set:
E         '2026-03-20'
tests\test_f015_r24_avisos.py:107: AssertionError

___________ test_f015_r24_la_matriz_no_marca_el_viernes_de_6_horas ____________
>       assert _incompletos_obra([
            {"fecha": VIERNES, "horas": 6.0, "candef": 9.0},
        ]) == set()
E       AssertionError: assert {'Pepe Perez|2026-03-20'} == set()
E         Extra items in the left set:
E         'Pepe Perez|2026-03-20'
tests\test_f015_r24_avisos.py:196: AssertionError
```

> La primera ejecución RED de T9 (guardada en el momento) falló por un error
> del propio test —le faltaba el `fixture` de entorno— y por tanto no probaba
> nada: se descarta y se conserva **esta**, que es la que enseña el
> comportamiento vigente antes del cambio.

**Verde.** `-k "f015_r24 or f015_r25"` → `33 passed`; suite de sv4
`599 passed`; `-k f003` en verde.

### T10 · «+ Nuevo» (commit `644073f`)

`jornada_sugerida` **no cambia** (mismas claves cuando no se pasa `fecha`);
con `fecha` válida se añade `jornada_dia` por empleado; con fecha mal escrita,
**422** con `ok: false`, nunca 500.

**Verificación.** `-k f015_r26` → `13 passed`; suite de sv4 `612 passed`.
`node --check services/partes-front/static/app.js` en verde (el fichero no se
tocó: hoy nadie consume `jornada_dia` desde el JS).

### T11 · Documentación (commit `8245390`)

`grep -n "Cuatro tablas" docs/ARCHITECTURE.md` → **sin resultados**. La
semántica 3 explica la jornada del día, el mapa, el último laborable y la
regresión con candef 8; la 7 dice cinco tablas. `partes-proyecto.md` §4.3
reescrita y §5.4 nueva con la tabla. Los dos `.ps1` llevan
`JORNADA_SEMANAL_POR_CANDEF=8:40,9:42` y `JORNADA_CACHE_TTL_S=600` (parseo
PowerShell comprobado; encoding y CRLF conservados). `CLAUDE.md` añade
`application/services/jornada_resolver.py` a la lista cerrada de duplicación
con fecha y motivo (decisión del humano, `design.md` §13 bis, duda 1).

### T12 · **MANUAL (humano)** — pendiente

Ver sección 7.

### T13 · Verde y mutación (este informe)

`bash harness/init.sh` → **exit 0**, `ENTORNO LISTO`. Campaña de mutación en
la sección 9.

## 4. Decisiones tomadas durante la implementación

Ninguna reabre la spec; todas resuelven huecos que aparecieron al bajarla a
código. Las que el reviewer debe mirar con más atención son **DI1** y **DI2**.

- **DI1 · Atajo cuando `S = 5·c`: la regla no se evalúa porque no cambia
  nada.** Si la jornada semanal es exactamente cinco veces el candef, entonces
  `max(0, S − 4c) = c` y el último laborable recibe **lo mismo** que
  cualquier otro día: el resultado no depende de qué día sea. El resolutor lo
  detecta y **no recorre la semana**. Consecuencias, todas buenas:
  - **coste cero para todo el mundo que hoy tiene candef 8** (`S = 40 = 5×8`):
    ni una consulta de calendario más que antes de F-015, ni una;
  - por eso el test dorado de F-003
    `test_f003_r8_el_dni_del_grupo_llega_al_puerto`, que exige **exactamente
    una** consulta al calendario, sigue en verde **sin tocarlo**. Sin el
    atajo habría que haberlo modificado, y eso está prohibido;
  - también reduce la superficie de R23: con candef 8 un viernes degradado no
    marca el parte del lunes, porque el viernes ni se consulta.
  El precio es que `DetalleJornada.ultimo_laborable` queda en `False` en ese
  caso (no se ha aplicado ningún resto, que es lo que el campo significa y lo
  que dice su docstring). No afecta a R28 —la marca solo se emite cuando la
  jornada difiere del candef, o sea cuando `S ≠ 5c`— ni a R25, cuyo
  `ultimo_laborable` es un número de horas calculado aparte.
  Test que lo fija: `test_f015_r13_con_S_igual_a_5c_no_se_consulta_el_resto_de_la_semana`.
- **DI2 · `empleado_jornada` tiene 19 columnas, no 16.** La tabla de
  `design.md` §6 enumera 19 (`id`, `dni_norm`, `jornada_semanal`, 7 del
  patrón, `desde`, `hasta`, `origen`, `nota`, `is_active` y las 4 de
  auditoría). El «16 columnas» de `tasks.md` T12 y de `design.md` §8 es una
  cuenta que se dejó fuera `created_by`, `updated_at_utc` y `updated_by`. Se
  implementa la tabla del §6 (que es la normativa) y **la verificación manual
  de T12 debe esperar 19 columnas**.
- **DI3 · Todas las columnas `NOT NULL` de la tabla nueva llevan
  `server_default`**, incluidas `dni_norm` (`''`), `desde` (`1900-01-01`) y
  `created_at_utc` (epoch). Lo exige el criterio de R30 y es lo prudente: el
  DDL complementario emite un `ALTER TABLE … ADD COLUMN` por columna en cada
  arranque, y el día que se añada una columna a una tabla ya con filas, sin
  `server_default` PostgreSQL rechaza el DDL y el servicio no levanta. Son
  centinelas que en la práctica no se usan: `create_all()` crea la tabla
  completa. El `''` de `dni_norm` no casa con ningún trabajador (nunca se
  consulta la tabla por DNI vacío).
- **DI4 · Los dos `jornada_resolver.py` pierden `from __future__ import
  annotations`.** No es cosmética: con las anotaciones aplazadas, `@dataclass`
  las resuelve mirando `sys.modules[cls.__module__]`, y los dos guardianes
  que cargan el fichero **por ruta** como módulo suelto (el de F-003 y el de
  F-015) revientan con `AttributeError: 'NoneType' object has no attribute
  '__dict__'`. El guardián de F-003 es un dorado que no se puede tocar; el de
  F-015 sí registra el módulo, pero igualar los dos habría sido modificar un
  test de F-003. Las anotaciones nativas de 3.12 bastan para lo que hay en el
  fichero. Queda explicado en un comentario en la cabecera de ambas copias.
- **DI5 · `.gitignore` ignora `.claude/worktrees/`** (commit `f78bfd7`). Son
  copias efímeras del repositorio que crea Claude Code para trabajar en
  paralelo (en esta sesión, el agente que redacta la spec de F-016). Sin la
  regla el árbol nunca está limpio y `harness/mutacion_paralela.py` se niega a
  arrancar («el árbol principal tiene cambios sin commitear»). Es higiene, no
  feature; se declara aquí por transparencia.
- **DI6 · Una fila mal formada de `empleado_jornada` se descarta al construir
  el índice**, no al consultarla: así el WARNING sale **una vez por lectura**
  en lugar de una por celda de la matriz de obra, y `excepcion_para` devuelve
  `None` limpio. `Excepcion.valida()` es la regla, y vive en el resolutor (o
  sea, en las dos copias).
- **DI7 · Los `.env.example` están en el `.gitignore` de cada servicio**
  (`*.example`), así que se han actualizado **en local pero no entran al
  repositorio**. El test de R33 comprueba su contenido solo si el fichero
  existe (y hace `skip` si no), para no romper en un clon limpio. Conviene que
  el humano lo sepa: la variable viaja de verdad por
  `infra/create_capps_partes.ps1` y `infra/create_sv4_front.ps1`, que sí están
  versionados.
- **DI8 · El KPI resuelve la excepción con el primer día del periodo
  mostrado.** La vigencia puede cambiar dentro del mes; el KPI es un resumen y
  necesita una fecha. Los avisos, que son lo que importa, se resuelven día a
  día.
- **DI9 · `esta_congelado` vive en `application/` y la importa el
  repositorio.** Escribirla dos veces sería exactamente lo que R32 quiere
  evitar (si el repositorio congelase distinto que el conciliador, la
  reversión borraría lo que el cálculo da por bueno). La dirección
  `infrastructure → application` ya existía en este servicio (`text_match`).

## 5. Lo que NO cambió (y se comprobó que no cambió)

- **`jornada_efectiva` y `candef_valido`**: ni la firma ni la semántica. Todo
  lo nuevo se construye encima (R11).
- **Los tests dorados de F-003**: ninguno se ha tocado. `test_f003_r15_splits_dorados.py`,
  `test_f003_r11_jornada_resolver.py`, `test_f003_r12_jornada_resolver.py`,
  `test_f003_r10_wiring_sv3.py`, `test_f003_r2_vistas_festivos.py` y el resto
  siguen en verde tal cual estaban.
- **`parte_registros`**: 56 columnas, las mismas (R21). `hora_candef` sigue
  guardando el candef **crudo** de Sigrid.
- **sv1, sv2 y sv5**: intactos. El payload hacia sv5 no cambia (le llegan
  líneas ya desglosadas).
- **La rama de día no laborable** de `_reclasificar_extras_jornada`, el
  recorte por `registro_id` descendente, la extra negativa única sobre el
  pivote y el trato del recurso sin código HE.
- **`jornada_sugerida`** de `/api/sigrid/empleados` sin el parámetro `fecha`.

## 6. Riesgo operativo (qué pasa al desplegar)

1. **La tabla se crea sola** en el primer arranque de sv3 o de sv4
   (`create_all` + `ddl_complementario()`), vacía. No hay migración manual.
2. **Con los datos de hoy (candef 8 en todo el mundo) no cambia ni una hora
   ni un aviso.** Es la propiedad R11, protegida por los dorados de F-003 y
   por `test_f015_r11_regresion_candef8.py`.
3. **La ventana peligrosa sigue siendo la inversa** (`design.md` §11.2 y §13
   ter): F-015 sin F-014 es regresión cero; **F-014 sin F-015 sí hace daño**
   (candef 9 con jornada plana ⇒ −3 h/semana). La petición de F-014 no se
   envía hasta que F-015 esté desplegada. Eso no es asunto de esta rama, pero
   conviene que no se pierda.
4. **Un `JORNADA_SEMANAL_POR_CANDEF` mal escrito impide arrancar** el servicio
   (sv3 y sv4). Es deliberado y está documentado en `azure-apps/partes.md`: un
   mapa a medias repartiría mal las horas de todos los partes en silencio.
5. **Lo ya registrado en Sigrid deja de recalcularse.** Es lo correcto (D7),
   pero cambia el comportamiento de `revert_extras_auto()`: a partir de ahora
   una línea `encolado`/`registrado` o de un parte aprobado conserva sus horas
   pase lo que pase. Si un día hay que forzar el recálculo de un parte
   aprobado, habrá que desaprobarlo primero.

## 7. Verificaciones MANUAL pendientes (T12, humano)

No se pueden hacer sin BBDD real ni despliegue. **Ninguna se ha ejecutado.**

1. **Arranque de sv3 y de sv4 en local o en Azure.** En el log de los dos,
   `esquema inicializado (N sentencias complementarias)` con **N mayor** que
   el de F-010 (crece en **19**: 18 columnas no primarias + el índice). En la
   base `partes`, `\d empleado_jornada` debe mostrar **19 columnas** (ver
   DI2, no 16) y el índice `ix_empleado_jornada_dni_norm`.
2. **Portal, vista de un trabajador de la cuadrilla.** Hoy, con candef 8, el
   KPI debe decir «8 h · 40 h/sem · último laborable 8 h» y **no debe cambiar
   ningún aviso**. Cuando F-014 esté aplicada (candef 9), el viernes de 6 h
   debe salir **sin** aviso de incompleto y el KPI «9 h · 42 h/sem · último
   laborable 6 h».
3. **Un parte ya aprobado o registrado no cambia su desglose** tras la primera
   pasada de sv3 con la versión nueva (R31/R32). Comprobarlo sobre un parte
   con `sigrid_estado = 'registrado'`.
4. **Render visual del KPI** (R25): que las tres líneas nuevas del bloque
   «Cantidad por defecto» caben y se leen.

Acuse o captura anotada, aquí mismo o en `progress/current.md`.

## 8. Evidencias

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **1 064 en verde, 0 fallos**: raíz **92** (15 → 92), sv3 **360** (112 → 360), sv4 **612** (462 → 612). sv5 sin cambios. **+475 tests nuevos de F-015** |
| **Cobertura de las líneas cambiadas** | **95,4 % (498/522 líneas)**, umbral 80 % — línea `PUERTA COBERTURA` de `bash harness/init.sh`, nivel `estandar` |
| **Mutantes generados / supervivientes** | ver sección 9 |
| **Tiempo de ejecución de la suite** | raíz 7,64 s · sv3 4,64 s · sv4 78,21 s (**≈ 91 s** el conjunto que ejecuta `init.sh`) |
| **`bash harness/init.sh`** | **exit 0** — `ENTORNO LISTO` |
| **Copias gemelas** | `orm_models.py` byte-idéntico (`cmp` sin salida) · los dos `jornada_resolver.py` equivalentes en API y comportamiento (guardián R19) |
| **Deuda de ruff del árbol real** | 430 → **455** avisos (+25: `UP035` por `typing.Callable`, que es el estilo del resto del repositorio, y `I001` en dos ficheros). El `python -m ruff check .` de `init.sh` marca 883 porque además recorre `.claude/worktrees/`, la copia efímera del agente de F-016 |

## 9. Campaña de mutación

PENDIENTE — se completa al terminar la campaña.

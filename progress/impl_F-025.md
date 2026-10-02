<!-- progress/impl_F-025.md -->
# F-025 · Incidencia y horas el mismo día — Informe del implementer

Rama `feature/F-025-incidencia-vs-extra`, **solo sv4**, rigor `estandar`.
Spec aprobada el 2026-10-02 (DA1–DA12 tal cual; DA2: día completo V, B, M,
F; parcial AT, FJ, H). Ni una escritura en Sigrid ni en producción, sin
despliegue, sin push, sin secretos. sv2, sv3, sv5, `orm_models.py`,
`congelacion.py`, `jornada_resolver.py` y `_rol_incidencia` intactos (R21,
R22).

## 1. Qué cambió (commits locales)

| Commit | Tarea | Qué |
|---|---|---|
| `d4cda31` | T1 | `config/incidencias.yaml` (7 letras, DA2) y `incidencias_horas.py`: `ClaseIncidencia`, `TablaIncidencias.clase_de`, `parsear_tabla` (R1–R3) |
| `c2eddf7` | T2 | `LineaDia`, `Incompatibilidad`, `detectar`, `resumen_por_dia` (R4–R8) |
| `352cb39` | T3 | `settings.incidencias_path` (`INCIDENCIAS_PATH`) y `construir_tabla_incidencias` al principio de `build_app`, en `app.state.tabla_incidencias` (R1, R2) |
| `247ad55` | T4 | Repositorio: `persona_de`, `_linea_dia`, `_activas_de_fechas` (en lotes), exclusión `incompatible` tras F-024, `_excluida_detalle(..., motivo)`, `avisos_incidencia` por grupo; `GrupoObra.avisos_incidencia` |
| `74c64e5` | T5 | `app.py`: tabla a `lineas_para_registro`, `avisos_incidencia` en `_evaluar_grupo`, `incompatible` en `_motivo_sin_lineas` (R9–R12, R14) |
| `0a45a81` | T6 | `incompat_nivel/motivo` en `RegistroView` y `ObraMatrixCell`; `incidencias` en `get_obra`/`get_worker` (detección sobre TODAS las líneas activas, cruza obras); `dias_incompatibles` en la ruta del trabajador |
| `a8f0162` | T7 | Plantillas (celda con clase y `title`, calendario con clase y marca, insignia en las dos tablas de líneas) y CSS (rojo bloqueo, ámbar aviso) |
| `0b926dd` | T8 | `app.js`: `incompatiblesHtml(n)` y `avisosIncidenciaHtml(avisos)` con `esc()`; CSS del modal |
| `383a41a` | T9 | Test de no regresión R20 y suite completa de sv4 |
| `05e791c` | T10 | Semántica 14 en `docs/ARCHITECTURE.md`; `partes-proyecto.md` §4.1 (H = Huelga, CIH, y enlace a la tabla) y §3.4 (bloqueo y aviso) |
| `a8e0b22` | — | Cero avisos nuevos de ruff en lo tocado (imports, `X \| None`, `noqa: TRY004` justificado) |

Tests nuevos (103): `test_f025_tabla.py` (36), `test_f025_deteccion.py`
(12), `test_f025_aprobacion.py` (31), `test_f025_vistas.py` (24). Ningún test
de F-022 ni F-024 se ha tocado (`git diff dev -- tests/test_f022_*
tests/test_f024_*` vacío). Sin red, Sigrid, colas ni PostgreSQL: SQLite en
memoria, `TestClient`, dobles de sv5/publisher/calendario de F-022 y `node`.

## 2. Decisiones y desviaciones (justificadas)

1. **`INCIDENCIAS_PATH` relativa a la raíz del servicio** (`RAIZ_SERVICIO`),
   no al directorio de trabajo como sv3: en el contenedor (`WORKDIR /app`) es
   lo mismo, y la suite y los worktrees de mutación no dependen de dónde se
   lancen (test con `chdir` a otro sitio).
2. **R2 algo más estricto, sin salirse de «nada en silencio»**: también
   tumban el arranque una entrada que no es mapa, sin `nombre`, o un código
   de Sigrid repetido en dos letras. Lectura y YAML roto → `ValueError` con
   la ruta («no se puede leer/parsear …»).
3. **Desviación de design §5.4**: los avisos de incidencia del modal se
   pintan **juntos, en `aprobar()`, fuera del pliegue**, y no dentro de
   `grupoHtml`. Los tests de F-022 ejecutan `grupoHtml` con node y una lista
   CERRADA de funciones; llamar ahí a una nueva los rompía (`ReferenceError`)
   y la orden era no tocarlos. R19 se cumple (se listan y escapan) y se ven
   aunque la obra esté plegada. `incompatiblesHtml` va tras la cabecera,
   antes de las obras y fuera de «Excluidas»; en el 422 el texto es el del
   servidor (`_motivo_sin_lineas`, R10).
4. **Motivos** (design §5.1): varias incidencias de la misma clase se
   nombran en orden alfabético de letra unidas con «y» («son»). Horas del
   bloqueo: suma con signo de las líneas con `|h| > 0`; del aviso: suma de
   las extra positivas; dos decimales.
5. `avisos_incidencia` siempre en el grupo (lista vacía);
   `excluidas["incompatible"]` solo si > 0 (design §5.2.4): las igualdades de
   F-022/F-024 siguen valiendo. Insignias inline en las dos plantillas; el
   `title` de la celda junta motivo y « · Ver parte del …» en UN atributo.
   `get_worker(worker_key, *, incidencias=None)`: llamadores sin cambios.

## 3. Fase RED (requisitos centrales)

Para cada bloque se escribió el test, se ejecutó contra un esqueleto (o
contra el código previo) y se pegó la salida real; después, el código y
verde. Comando en cada caso: `cd services/partes-front && python -m pytest
<fichero> -q --tb=line`.

**R2, R3 (T1)** — `incidencias_horas.py` era un esqueleto que devolvía una
tabla vacía y `clase_de` → `None`:
```
E   Failed: DID NOT RAISE ValueError
tests\test_f025_tabla.py:119: Failed: DID NOT RAISE ValueError
E   AttributeError: 'NoneType' object has no attribute 'letra'
tests\test_f025_tabla.py:134: AttributeError: 'NoneType' object has no attribute 'letra'
FAILED tests/test_f025_tabla.py::test_f025_r2_falta_una_letra[V] - Failed: DI...
FAILED tests/test_f025_tabla.py::test_f025_r2_clase_desconocida - Failed: DID...
FAILED tests/test_f025_tabla.py::test_f025_r3_por_letra_sin_espacios_y_en_mayusculas
FAILED tests/test_f025_tabla.py::test_f025_r3_sin_letra_conocida_sale_del_codigo_de_hora
25 failed, 5 passed in 0.13s
```
**R2 en el arranque (T3)** — sin `incidencias_path` ni la carga en `build_app`:
```
E   Failed: DID NOT RAISE ValueError
FAILED tests/test_f025_tabla.py::test_f025_r2_arranque_con_ruta_inexistente_falla
FAILED tests/test_f025_tabla.py::test_f025_r2_arranque_con_yaml_mal_escrito_falla
FAILED tests/test_f025_tabla.py::test_f025_r2_arranque_con_una_letra_de_menos_falla
6 failed, 30 deselected in 3.64s
```
**R5, R6 (T2)** — `detectar` y `resumen_por_dia` devolvían `{}`:
```
E   AssertionError: assert {} == {'d1': Incomp..., motivo='b')}
FAILED tests/test_f025_deteccion.py::test_f025_r5_dia_completo_y_ordinarias_bloquea_todas_las_lineas
FAILED tests/test_f025_deteccion.py::test_f025_r6_parcial_y_extra_positiva_avisa_en_todas
FAILED tests/test_f025_deteccion.py::test_f025_r8_si_cumple_los_dos_manda_el_bloqueo
10 failed, 2 passed in 0.18s
```
**R7** (requisito negativo: contra `{}` pasa por definición) — se ejecutó
contra una variante ingenua «cualquier incidencia con otra línea bloquea»
(`-k r7 --tb=short`):
```
tests\test_f025_deteccion.py:108: in test_f025_r7_combinaciones_compatibles_no_llevan_nivel
E   assert {1: Incompati..., motivo='x')} == {}
E     {1: Incompatibilidad(nivel='bloqueo', motivo='x'),
E      2: Incompatibilidad(nivel='bloqueo', motivo='x')}
1 failed, 11 deselected in 0.43s
```
**R9, R11, R13 (T4, repositorio)** — `lineas_para_registro` aceptaba
`incidencias` sin usarlo y `persona_de` devolvía `""`:
```
E   KeyError: 'incompatible'
E   KeyError: 'avisos_incidencia'
E   AssertionError: assert {'registrado'...do_sigrid': 1} == {'registrado'...ompatible': 1}
FAILED tests/test_f025_aprobacion.py::test_f025_r9_repo_bloqueo_excluye_con_su_motivo
FAILED tests/test_f025_aprobacion.py::test_f025_r9_repo_mira_lineas_no_pedidas_y_de_otras_obras
FAILED tests/test_f025_aprobacion.py::test_f025_r11_repo_aviso_viaja_y_se_lista_solo_la_extra
FAILED tests/test_f025_aprobacion.py::test_f025_r13_repo_registrado_cuenta_solo_en_su_estado
FAILED tests/test_f025_aprobacion.py::test_f025_r12_repo_incluir_borradas_no_levanta_el_bloqueo
10 failed, 5 passed in 1.74s
```
**R9–R12, R14 (T5, endpoints)** — con el repositorio ya listo pero sin
pasarle la tabla desde `app.py`:
```
C:\...\tests\test_f025_aprobacion.py:440: assert [2, 3, 7] == [7]
E   KeyError: 'incompatible'
FAILED tests/test_f025_aprobacion.py::test_f025_r9_preflight_excluye_el_dia_en_bloqueo
FAILED tests/test_f025_aprobacion.py::test_f025_r10_todo_excluido_es_422_sin_llamar_a_sv5[/api/aprobar/ejecutar]
FAILED tests/test_f025_aprobacion.py::test_f025_r9_encolar_no_publica_ni_marca_el_bloqueo
FAILED tests/test_f025_aprobacion.py::test_f025_r12_ningun_override_levanta_la_exclusion[extra3]
FAILED tests/test_f025_aprobacion.py::test_f025_r14_el_payload_de_sv5_no_cambia_de_forma
16 failed, 15 passed, 1 warning in 8.05s
```
**R18 (T6, repositorio; T7, HTML)** — campos en los DTO a `None` y
plantillas sin las clases:
```
tests\test_f025_vistas.py:78: AssertionError: assert None == 'bloqueo'
FAILED tests/test_f025_vistas.py::test_f025_r18_repo_la_incidencia_en_otra_obra_marca_las_dos
FAILED tests/test_f025_vistas.py::test_f025_r17_r18_repo_lineas_de_la_vista_de_trabajador
tests\test_f025_vistas.py:234: AssertionError: assert 'mx-incompat' in {'mx-cell', 'mx-inc', 'mx-pick'}
FAILED tests/test_f025_vistas.py::test_f025_r18_html_la_obra_de_la_incidencia_tambien
```
R19 (no central) también tuvo RED: `app.js no define avisosIncidenciaHtml`
(9 failed). R20 es un test de no regresión: pasa antes y después por diseño.

## 4. Verificación (resultado real)

- **`bash harness/init.sh` final** (HEAD `c45d933`, todo commiteado salvo
  este informe, `current.md` y `tasks.md`): **ENTORNO LISTO**; raíz `419
  passed, 1 skipped in 66.18s`; sv4 `1535 passed, 1 warning in 394.50s`;
  sv1/sv2/sv3/sv5 verdes (caché, sin cambios); `PUERTA COBERTURA: 100.0% de
  204 líneas cambiadas cubiertas (204/204, umbral 80%, nivel estandar)`;
  `PUERTA TAMAÑO … impl 213/220`; ruff 557 avisos (= `dev`).
- Antes de la mutación (HEAD `a8e0b22`), `init.sh` ya dio ENTORNO LISTO con
  `PUERTA COBERTURA: 100.0% de 204 líneas cambiadas cubiertas`.
- `node --check static/app.js` OK; Jinja2 de las dos plantillas OK. ruff: 0
  avisos en lo nuevo; los ficheros modificados, los mismos que en `dev`.

## 5. Mutación y evidencias

`python -m harness.mutacion --feature F-025 --workers 6 --timeout 600`
(HEAD `a8e0b22`, 5 ficheros, 466 líneas en alcance; muestreo del nivel
`estandar`: 20 de 70, semilla `20260820`): **20 evaluados, 14 muertos, 6
supervivientes, 0 timeouts, 0 sin veredicto, 1861.6 s** (línea base de cada
worktree 533–539 s). Análisis completo en `progress/mutacion_F-025.md`:

| Superviviente | Decisión | Comprobado a mano |
|---|---|---|
| `incidencias_horas.py:152` `round(valor, 2→3)` | test nuevo `test_f025_r6_las_horas_del_motivo_van_con_dos_decimales` | `1 failed, 12 passed` |
| `incidencias_horas.py:185` `valor > ε → >= ε` | **equivalente**: solo se llega tras `abs(valor) > ε` | `13 passed` |
| `parte_repository.py:555` `_peor`, `== → !=` | test nuevo `test_f025_r15_peor_nivel_gana_el_bloqueo_en_cualquier_orden` | `1 failed, 33 passed` |
| `parte_repository.py:555` `_peor`, `and → or` | el mismo test | `1 failed, 33 passed` |
| `parte_repository.py:1475` aviso con `horas >= 0` | test nuevo `test_f025_r11_repo_aviso_solo_lista_extras_positivas` | `1 failed, 33 passed` |
| `parte_repository.py:1478` `lineas[-1] → [-2]` | test nuevo `test_f025_r11_repo_aviso_de_la_unica_linea_pedida` | `1 failed, 33 passed` |

Tests en commit `9c52389` (sin tocar código de producción, así que la
campaña sobre `a8e0b22` sigue midiendo el mismo código). **0 sin resolver.**

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 `1535 passed`; raíz `419 passed, 1 skipped`; F-025 `107` (36 + 13 + 34 + 24) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 204 líneas cambiadas cubiertas` |
| Mutantes generados / evaluados / supervivientes | 70 / 20 / 6 → 1 equivalente justificado, 5 con test nuevo |
| Tiempo de la suite | sv4 394.50 s; raíz 66.18 s; mutación 1861.6 s |

## 6. Fuera de alcance y pendientes

Fuera (design §7, DA9): horas dentro de una racha («V……V»), jornada con
permiso parcial, `parte_detail` y listado de partes, bloquear al crear o
editar (DA4), reescribir lo ya registrado (DA6). `azure-apps`: no cambia lo
que se expone ni se consume (el preflight es interno; `INCIDENCIAS_PATH`
tiene valor por defecto y va en la imagen).

**MANUAL (humano)**. Desplegar solo sv4 lo pide el humano; escrituras solo
en modo pruebas (obra 0404, `PRUEBA-IA`), limpieza con
`prueba_escritura_sigrid.py`.

- **M1 · antes de desplegar** (PG `partes`, solo lectura, con firewall): la
  consulta de design §9 (recuento de días-trabajador en conflicto por letra
  y `sigrid_estado`). Anotar el resultado en `progress/current.md`.
  Esperado: cifra pequeña; si es grande, revisar DA2 antes de desplegar.
- **Arranque tras desplegar**: en el log de `ca-sv4-front` debe salir
  `[incidencias][wiring] clases desde /app/config/incidencias.yaml:
  V=CIV:dia_completo, B=CIE:dia_completo, AT=CIA:parcial, …`. Sin esa línea
  y con un `ValueError: incidencias: …`, el portal no levanta (a propósito).
- **M2** (navegador, Ctrl+F5, obra 0404): con «+ Nuevo», para una persona,
  un día con M y el mismo día 8 h; desde la celda, crear una extra. Esperado:
  celda roja con el motivo en el `title`, insignia «⛔ no se registra» en sus
  líneas; «Aprobar» → bloque rojo «N línea(s) no se registran…» y las líneas
  en «Excluidas» con su motivo; el resto llega a Sigrid y esas no cambian de
  estado. Aprobar SOLO esas líneas → «No se puede registrar: … con una
  incidencia de día completo y horas el mismo día…».
- **M3**: FJ + 2 h extra el mismo día → celda e insignia ámbar «⚠ revisar»;
  el modal muestra «Hay 1 linea(s) extra en un día con una incidencia
  parcial…» y se registra.
- **M4**: incidencia M en la obra A y una extra en la obra B el mismo día →
  marcadas las dos celdas (A y B) y, en la ficha de la persona, el día en
  rojo con la marca ⛔ y su motivo.
- **M5 · Administración**: confirmar DA2 (sobre todo F y H) y que el texto
  de los motivos se entiende.

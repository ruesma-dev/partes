<!-- progress/impl_F-050.md -->
# F-050 · Informe del implementer

Rama `feature/F-050-misma-fila-para-el-mismo-trabajador` (worktree `partes-wt-f050`), sobre
`dev` (`ff2ed8e`). Solo sv4. Estado: **T1–T10, T12 y T13 hechas; `blocked` en T11**: la
campaña de mutación no pasa de la línea base (motivo y propuesta en `progress/current.md`).

## Qué cambió (un commit por tarea)

| Tarea | Commit | Cambio |
|---|---|---|
| Paso 0 | `0378ab5`, `614dc45` | rebase sobre `dev`; DA1/DA1b/DA11 y M1 anotadas; `design.md` a 250 líneas |
| T1 | `0e92f19` | `_clave_trabajador` + `_recurso_de`; `worker_key_for_registro` delega (R1–R3, R11) |
| T2 | `78d8636`, `cbb3eb8` | literal `emp-77` → `rec-501` (22 ficheros) y el dato de los fixtures que compartían recurso (decisión del humano del 2026-10-20, abajo) |
| T3 | `82d2a2a` | `tests/test_f050_vistas.py`: R5, R8–R10, R12, R13 (verdes solo con T1) |
| T4 | `48d0f66` | `get_parte` y `list_partes` con la clave única (R4, R6, R7) |
| T5 | `21b1650` | `fila_para_alta_manual` y su uso en `crear_parte_manual` (R16–R18) |
| T6 | `b769e0d` | `clave_actual_de_clave_antigua` + 307 en `trabajador_detail` (R14, R15) |
| T7 | `085bb80`, `a9ee57a` | ficha más reciente en `get_worker`; `data-emp-ide`/`data-emp-reside`; `wireAddLine`; `verHrefNuevoParte` (R19, R20) |
| T8 | `d7e965e` | `_empresa_por_recurso` extraída de `list_obras`; `empresas`/`empresa_texto` en `WorkerRow` y `WorkerDetail`; orden; columna «Empresa» y cabecera (R23–R26) |
| T9 | `12e4092` | `docs/ARCHITECTURE.md` semántica 14: orden de la clave |
| T10 | `6519b1e` | comprobación de R21 (Evidencias) |
| T12, T13 | este cierre | M2–M6 y despliegue en `progress/current.md`; `init.sh` en verde |

**Producción** (todo sv4): `infrastructure/database/parte_repository.py`,
`interface_adapters/web/app.py`, `templates/trabajador_detail.html`,
`templates/trabajadores_list.html`, `static/app.js`. Además `docs/ARCHITECTURE.md`, la spec
(R22 y T2 anotados por la decisión del humano), `harness/features.json`, `BACKLOG.md` y
`progress/current.md`. **Tests nuevos**: `services/partes-front/tests/test_f050_{clave,vistas,
alta_manual,portal,empresa}.py` (SQLite de `tests/dobles.py`, TestClient y `node`; sin red ni
PostgreSQL; datos sintéticos).

## T2 · decisión del humano aplicada («apruebo», 2026-10-20)

`progress/propuesta_T2_F-050.diff` aplicado tal cual: `sembrar_parte` y
`test_f025_aprobacion.sembrar` ganan `recurso_ide: int = 501`; la persona B (ficha 88) va con
el 502 (`emp-88` → `rec-502`; f019, f022, f025 vistas); en f019 `publicado` la ficha 77 con el
602 del mensual (`rec-501` → `rec-602`); f035 `_asignar` gana `clave` opcional y r12 pasa
`clave="rec-903"`. Ninguna aserción cambia: `git diff -U0 dev -- services/partes-front/tests`
no tiene otras líneas que literales de clave y esos datos. Suite de sv4 tras T2:
`2263 passed, 1 skipped`.

## Decisiones de diseño (dentro de la spec)

- **R14 con la regla anterior exacta.** `clave_actual_de_clave_antigua` filtra con
  `_clave_trabajador(casada=False, …) == clave`, que es byte a byte la regla de antes (ficha
  ⇒ `emp-`; si no, leído ⇒ `nom-`). Una línea **con ficha** y el mismo leído no cuenta para
  una `nom-` antigua, como dice R14 («las líneas que darían esa clave con la regla
  anterior»); el filtro abreviado de design §3 («leído igual») la habría contado y dado 404.
  Lo fija `test_f050_r14_repo_nom_solo_de_lineas_sin_ficha`. `emp-abc` no casa con ninguna
  `emp-{int}` ⇒ None (lo mismo que el «E no entero ⇒ None» del design).
- **R6.** Las `sin-trabajador` del detalle van por `("sin-trabajador", empleado_line_no)`. Un
  leído de solo espacios era antes una clave propia; ahora es `sin-trabajador` de su fila.
- **R16.** La clave de la línea nueva se calcula una vez por alta (`casada` = ficha o
  `recurso_manual`; recurso = `empleado_reside`, que es el `recurso_ide` que se escribe) y el
  par (fila, leído) una vez por día, compartido por la incidencia y cada tipo.
- **R19.** `data-emp-ide="{{ detail.empleado_ide or '' }}"` (literal del design).
  `WorkerDetail.empleado_ide` es ahora la ficha de la línea más reciente que la tenga (antes,
  la de la primera leída); con `emp-`/`nom-` el valor no cambia.
- **R20.** El «Ver» queda en la función pura `verHrefNuevoParte(reside, emp)` del IIFE de
  `app.js`, que el test ejecuta en `node`.
- **R23–R25.** Regla de F-033 para todo grupo (también `nom-`/`sin-trabajador`, design §3 y
  DA11) con el recurso de la línea (`recurso_ide`, si no `empleado_reside`); el mapa
  recurso→empresa, idéntico al de `list_obras` (`test_f033_columna_empresa.py` intacto y verde).
- **R26.** Orden de `list_workers`: `(casada primero, nombre, menor empresa o 10**9)`.
- Los ficheros nuevos pasan `ruff check` desde la raíz (la deuda previa no bloquea).

## Fase RED (traza real; comando desde `services/partes-front`)

`C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --tb=line <fichero>`; rutas recortadas.

**T1** (`tests/test_f050_clave.py`, sin código): `6 failed, 49 passed`
(`assert 'nom-NOMBRE_APELLIDO' == 'rec-6001'`, `assert 'emp-77' == 'rec-501'`,
`ImportError: cannot import name '_clave_trabajador'`). Después: `55 passed`.

**T3** (`tests/test_f050_vistas.py -k "r5 or r8 or r9 or r10 or r12 or r13"`, contra el
`parte_repository.py` de `0e92f19^`, restaurado después):
```
test_f050_vistas.py:163: AssertionError: assert ['nom-APELLID...BRE_APELLIDO'] == ['rec-6001']
test_f050_vistas.py:173: AssertionError: assert {'emp-77', 'e...'nom-P._OCHO'} == {'rec-501', 'rec-502'}
test_f050_vistas.py:181: AssertionError: assert {'nom-JUAN_IGUAL'} == {'rec-9101', 'rec-9102'}
test_f050_vistas.py:186: AssertionError: assert {'emp-93', 'nom-PERSONA_ONCE'} == {'rec-9201', 'rec-9202'}
test_f050_vistas.py:196: assert 2 == 1
test_f050_vistas.py:224: AssertionError: assert ['emp-81', 'emp-82'] == ['rec-8101', 'rec-8201']
test_f050_vistas.py:242: AttributeError: 'NoneType' object has no attribute 'registros'
test_f050_vistas.py:268: assert [] == [3, 4]
test_f050_vistas.py:279: assert (0, 0) == (2, 0)
test_f050_vistas.py:313: assert [3] == []
17 failed, 1 passed in 2.50s
```
Con T1 y sin más código: `18 passed`.

**T4** (`tests/test_f050_vistas.py tests/test_f050_clave.py`):
```
test_f050_vistas.py:346: assert [[2], [1]] == [[2, 1]]
test_f050_vistas.py:351: assert [[3], [4], [5]] == [[3, 4], [5]]
test_f050_vistas.py:369: assert [[1], [3], [2]] == [[1, 3], [2]]
test_f050_vistas.py:383: assert [[1], [2]] == [[1, 2]]
test_f050_vistas.py:393: assert 2 == 1
test_f050_clave.py:230: AssertionError: get_parte
test_f050_clave.py:240: AssertionError: assert 'r.empleado_...nombre_leido' not in '# infrastru...'
7 failed, 73 passed in 4.65s
```
Después: `80 passed`.

**T5** (`tests/test_f050_alta_manual.py`, contra el repositorio de `48d0f66`):
```
test_f050_alta_manual.py:104: AssertionError: assert [(1, 'APELLID...LIDO NOMBRE')] == [(3, 'Nombre ...re Apellido')]
test_f050_alta_manual.py:135: AssertionError: assert (1, 'CINCUENTA, FICHA') == (4, 'Ficha Cincuenta')
test_f050_alta_manual.py:158: AssertionError: assert [(1, 'APELLID...LIDO NOMBRE')] == [(7, 'APELLID...LIDO NOMBRE')]
test_f050_alta_manual.py:172: AssertionError: assert (1, 'APELLIDO NOMBRE') == (3, 'APELLIDO NOMBRE')
test_f050_alta_manual.py:203: AssertionError: assert (True, 1, 'APELLIDO NOMBRE') == (True, 3, 'Nombre Apellido')
test_f050_alta_manual.py:212: AssertionError: assert (1, 'APELLIDO NOMBRE') == (8, 'APELLIDO NOMBRE')
test_f050_alta_manual.py:227: AssertionError: assert [('d-e6', 1, ...LIDO NOMBRE')] == [('d-e6', 3, ...LIDO NOMBRE')]
7 failed, 4 passed in 2.56s
```
Los 4 que pasan: R18 y «documento nuevo / sin filas ⇒ 1» (exigen lo de hoy) y
`…_cae_en_la_fila_de_la_persona` (integración con R6, ya hecho en T4). Después, con
`test_f035_repositorio.py`: `42 passed`.

**T6** (`tests/test_f050_portal.py -k "r14 or r15"`):
```
test_f050_portal.py:114: AttributeError: 'ParteReviewRepository' object has no attribute 'clave_actual_de_clave_antigua'
test_f050_portal.py:136: assert 404 == 307
test_f050_portal.py:151: assert 404 == 200
16 failed, 1 passed, 1 warning in 9.36s
```
Después: `17 passed`.

**T7** (`tests/test_f050_portal.py`):
```
test_f050_portal.py:230: AssertionError: assert 77 == 78
test_f050_portal.py:245: KeyError: 'data-emp-reside'
test_f050_portal.py:267: assert 'reside: d.empReside' in '\n  function wireAddLine() {...'
test_f050_portal.py:279: assert 'verHrefNuevoParte(document.getElementById("emp-reside").value,' in '...'
test_f050_portal.py:259: AssertionError: app.js no define verHrefNuevoParte
11 failed, 18 passed, 1 warning in 13.19s
```
Después, con `test_f035_vistas.py` y `test_f040_vistas.py`: `55 passed`; `node --check` OK.

**T8** (`tests/test_f050_empresa.py`):
```
test_f050_empresa.py:93: AttributeError: 'WorkerRow' object has no attribute 'empresas'
test_f050_empresa.py:121: AttributeError: 'WorkerDetail' object has no attribute 'empresas'
test_f050_empresa.py:232: AssertionError: assert ['Trabajador', 'Categoria'] == ['Trabajador', 'Empresa']
test_f050_empresa.py:265: assert '· Ruesma' in '<div class="page-header"> ... Casado en Sigrid</span> </p> </div>'
17 failed, 2 passed, 1 warning in 8.45s
```
Los 2 que pasan («sin consultas nuevas» y «sin empresa, la cabecera no la pinta») exigen lo
de hoy. Después, con `test_f033_columna_empresa.py` y `test_f050_vistas.py`: `53 passed`.

## Fuera de alcance y pendiente

- Fuera (requirements «Fuera de alcance»): unir E11, respaldo de empresa por obra, corregir
  líneas manuales ya guardadas y el aviso de jornada incompleta por nombre.
- **Pendiente: T11** (mutación, `blocked`); después, reviewer.
- **MANUAL (humano)**: despliegue solo de sv4 y M2–M6 (`design.md` §6; pasos en
  `progress/current.md`).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de F-050 | 139 en 5 ficheros (`clave` 57, `vistas` 23, `alta_manual` 11, `portal` 29, `empresa` 19), todos verdes |
| Suite de sv4 (tras T8, sin cobertura) | `2347 passed, 1 skipped, 1 warning in 569.06s (0:09:29)` |
| Suite de sv4 dentro de `init.sh` (con cobertura) | `2347 passed, 1 skipped, 1 warning in 1879.78s (0:31:19)` |
| Suite raíz dentro de `init.sh` | `493 passed, 3 skipped in 63.80s` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 60 líneas cambiadas cubiertas (60/60, umbral 80%, nivel estandar)` |
| R21 (T10) | `git diff dev --stat` de sv1/sv2/sv3/sv5, `infra`, `CLAUDE.md`, `orm_models.py`, `application/`, `infrastructure/sigrid/`, `obra_detail.html`, `parte_detail.html`: **vacío**; en tests solo las `A` de F-050 y las `M` de T2; `crear_extra_desde`, `list_unmatched_workers`, `obra_key_for_registro`, `esta_casado` y `persona_de` idénticas a `dev` (comparación por AST) |
| Mutantes generados / supervivientes | **ninguno evaluado**: la campaña aborta en la línea base (abajo) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (exit 0); PUERTA TAMAÑO dentro de topes (requirements 150/150, design 250/250) |

### Mutación (T11): `blocked`

`C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m harness.mutacion --feature F-050 --workers 3`
(sin `--timeout`; log en el scratchpad, fuera del worktree), exit 3:

```
F-050: 2 fichero(s), 163 línea(s) de producción (origen rama, ff2ed8e..feature/F-050-misma-fila-para-el-mismo-trabajador)
Muestreo: hasta 20 mutantes, semilla 20260820 (nivel estandar).
Timeout por mutante: se derivará de la línea base medida, con suelo 120 s y margen 2.0. La propia línea base dispone de 600 s.
Campaña paralela: hasta 3 workers, uno por worktree.
LÍNEA BASE SIN TERMINAR en …/mutacion_F-050_bm_dyzup/wk_1/services/partes-front: la suite SIN MUTAR agotó los 600 s que se le concedieron (el suelo 'mutacion.timeout_por_mutante_s' multiplicado por la holgura de 5), con 3 worker(s) compitiendo por la máquina.
```

La suite de sv4 sola tarda 569 s; tres a la vez no caben en 600 s. Bajar los workers o subir
el suelo de `harness/rigor.json` se sale de lo pedido (`--workers 3`, sin tocar el arnés): no
lo improviso. Opciones A/B/C en `progress/current.md`. Los worktrees de la campaña se
borraron solos; queda `progress/mutacion_F-050.md` por hacer.

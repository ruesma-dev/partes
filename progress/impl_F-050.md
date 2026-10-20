<!-- progress/impl_F-050.md -->
# F-050 · Informe del implementer (PARCIAL: `blocked` en T2)

Rama `feature/F-050-misma-fila-para-el-mismo-trabajador` (worktree `partes-wt-f050`),
rebasada sobre `dev` (`ff2ed8e`). Estado: **`blocked` en T2** (motivo y propuesta en
`progress/current.md`). Este informe se completa cuando se retome.

## Paso 0 (hecho)

- `git rebase dev`: conflictos solo en `BACKLOG.md` (generado: se tomó el de `dev` y lo
  regeneró `init.sh`), `harness/features.json` (se conservan F-046, F-048, F-051 de `dev`
  y se añade F-050) y `progress/current.md` (F-050 arriba y el resto de `dev` debajo).
- Commit `0378ab5`: DA1 (opción A), DA1b y DA11 marcadas como aprobadas por el humano el
  2026-10-20 en `design.md` §8 (DA5 y DA6 ampliadas, confirmadas con DA1); resultado de M1
  en §6; `features.json` con la `description` y los `acceptance` alineados con la spec
  (empresa visible incluida) y F-050 `in_progress`.
- Commit `614dc45`: el anotado dejaba `design.md` en 258 líneas (tope 250, PUERTA TAMAÑO de
  `init.sh` en rojo); se recortó a 250 resumiendo M1, DA1, DA1b, DA5, DA6 y DA11 sin perder
  contenido. `BACKLOG.md` regenerado.

## T1 · clave de trabajador (hecha, commit `0e92f19`)

`_clave_trabajador` (pura) + `_recurso_de` + `worker_key_for_registro` delegando, en
`services/partes-front/infrastructure/database/parte_repository.py`. Tests en
`services/partes-front/tests/test_f050_clave.py` (R1, R2, R3 contra una copia literal de la
función de `dc03468`, R11). `persona_de` sin cambios de código.

### Fase RED (T1)

Comando: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest -q -rf --tb=line tests/test_f050_clave.py`
(desde `services/partes-front`, antes de tocar el repositorio):

```
FFFF...F.............................................F.                  [100%]
E   AssertionError: assert 'nom-NOMBRE_APELLIDO' == 'rec-6001'
tests\test_f050_clave.py:69: AssertionError: assert 'nom-NOMBRE_APELLIDO' == 'rec-6001'
E   AssertionError: assert 'emp-77' == 'rec-501'
tests\test_f050_clave.py:82: AssertionError: assert 'emp-77' == 'rec-501'
E   AssertionError: assert 'emp-77' == 'rec-501'
tests\test_f050_clave.py:91: AssertionError: assert 'emp-77' == 'rec-501'
E   AssertionError: assert 'emp-77' == 'rec-999'
tests\test_f050_clave.py:99: AssertionError: assert 'emp-77' == 'rec-999'
E   ImportError: cannot import name '_clave_trabajador' from 'infrastructure.database.parte_repository'
E   AssertionError: assert 'emp-77' == 'rec-501'
tests\test_f050_clave.py:208: AssertionError: assert 'emp-77' == 'rec-501'
FAILED tests/test_f050_clave.py::test_f050_r1_casada_sin_ficha_con_recurso_da_rec
FAILED tests/test_f050_clave.py::test_f050_r1_con_ficha_y_recurso_da_rec - As...
FAILED tests/test_f050_clave.py::test_f050_r1_recurso_ide_antes_que_empleado_reside
FAILED tests/test_f050_clave.py::test_f050_r1_sin_recurso_ide_usa_empleado_reside
FAILED tests/test_f050_clave.py::test_f050_r1_funcion_pura_cada_rama - Import...
FAILED tests/test_f050_clave.py::test_f050_r11_persona_de_sin_dni_es_la_clave_nueva
6 failed, 49 passed in 1.97s
```

(Los 49 que ya pasaban son R2, R3 y R11 con DNI: exigen que lo de hoy NO cambie.)
Tras el código: `55 passed in 2.24s`.

## T2 · tests existentes (PARCIAL, commit `78d8636`; `blocked`)

Suite completa de sv4 con T1: **122 fallos en 23 ficheros** (`2141 passed`). Cambiando
SOLO el literal `emp-77` → `rec-501` (el recurso de los fixtures de `tests/dobles.py` y
`tests/test_f025_aprobacion.py::sembrar`) en 22 ficheros: **106 vuelven a verde**; quedan
**16 en 4 ficheros** que no se arreglan con el literal (detalle y propuesta en
`progress/current.md`; diff verificado en `progress/propuesta_T2_F-050.diff`).

Ficheros con solo el literal (62 líneas): f003 r12, r13, r23, r2, r7; f004 endpoints y
vistas; f015 r17, r24, r25; f019 portal; f022 aprobar y vistas; f023 catálogo; f024
borrado y comprobar; f025 aprobación y vistas; f028; f043; f046 marcas; f048 traza.

## Pendiente al retomar

T2 (según la decisión), T3–T13. Evidencias (tests, cobertura, mutación, tiempos): al
cerrar.

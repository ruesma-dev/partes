<!-- progress/impl_F-001.md -->
# F-001 · Test de estructura del monorepo (calentamiento) — informe de implementación

- Rama: `feature/F-001-test-estructura` (verificada con `git branch --show-current`).
- Modo: `sdd=false` → la mini-spec son los `acceptance` de `harness/features.json`.
- Rigor declarado: **estandar** (exige fase RED, cobertura y mutación).
- Fecha: 2026-08-13.

## Qué cambió

Dos ficheros **nuevos**, ninguno modificado. El diff frente a `dev` es
exactamente esto:

```
A       tests/conftest.py
A       tests/test_estructura_monorepo.py
```

| Fichero | Qué hace |
|---|---|
| `tests/conftest.py` | Inserta la raíz del repositorio en `sys.path` para que `import harness.servicios` funcione con independencia del directorio desde el que se lance pytest. Nada más: sin fixtures, sin plugins. |
| `tests/test_estructura_monorepo.py` | 6 tests con nombre trazable que validan `harness/servicios.json` contra el árbol real y contra la propia validación del arnés. |

Commits (uno por tarea, en español, formato `F-XXX Tn:`):

```
d682ed0 F-001 T1: conftest de la suite raiz para que pytest resuelva imports desde la raiz del repo
c3aeb58 F-001 T2: test de estructura del monorepo (rutas declaradas, punto de entrada y rechazo de ruta inexistente)
```

## Trazabilidad con los criterios `acceptance`

| Criterio | Cómo se cubre |
|---|---|
| R1 · `tests/test_estructura_monorepo.py pasa sin red ni BBDD` | `test_f001_r1_la_declaracion_de_servicios_no_esta_vacia`, `test_f001_r1_cada_ruta_declarada_existe_y_es_un_directorio`, `test_f001_r1_cada_servicio_python_tiene_punto_de_entrada`. Solo sistema de ficheros del repo: ni sockets, ni driver de BBDD, ni credenciales, ni variables de entorno. |
| R2 · `El test falla si se declara un servicio con ruta inexistente` | `test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion` (+ dos tests de control, abajo). |
| R3 · `bash harness/init.sh en verde` | No tiene test: se cumple ejecutando el portero, que es además quien ejecuta esta suite. Salida real más abajo. |

## Decisiones de diseño

1. **Se reutiliza `harness/servicios.py`, no se reimplementa el parseo.** Los
   tests llaman a `cargar_servicios(raiz=...)`. Reescribir aquí la lectura del
   JSON habría creado una segunda verdad que podría divergir de la que usa el
   portero, que es justo el fallo que la feature viene a evitar.
2. **La comprobación `is_dir()` se repite en el test aunque el cargador ya la
   haga.** No es redundancia gratuita: el test declara por escrito qué se
   exige del árbol, y si mañana el cargador relajase esa validación (que es
   exactamente la rotura 3 de la fase RED) el test seguiría cazándolo por su
   cuenta.
3. **Punto de entrada = `main.py` *o* `pyproject.toml`.** Los cinco servicios
   Python de este monorepo tienen hoy `main.py`; se admite `pyproject.toml`
   para no obligar a tocar el test el día que uno se empaquete.
4. **R2 se prueba con una declaración falsa en `tmp_path`, nunca tocando
   `harness/servicios.json`.** Un test que modificara el fichero real dejaría
   el repositorio en un estado distinto según hubiera terminado o hubiera
   reventado a mitad. El helper `_escribir_declaracion` es el único punto que
   escribe, y siempre bajo el `tmp_path` de pytest.
5. **Dos tests de control junto al de R2**, porque el `pytest.raises` por sí
   solo es débil:
   - `..._la_misma_declaracion_con_la_ruta_creada_si_carga`: misma declaración
     palabra por palabra, con la carpeta creada → carga bien. Sin él, un
     validador que rechazase *todo* pasaría por bueno el test de R2.
   - `..._la_declaracion_real_del_repositorio_no_se_toca`: guardarraíl contra
     que el helper acabe escribiendo algún día sobre el fichero real.
6. **Se afirma sobre el contenido del mensaje de error** (nombre del servicio y
   ruta que falla), no solo sobre el tipo de excepción: un `ValueError` mudo no
   sirve para arreglar nada.

## Verificaciones ejecutadas (salida real)

### Suite de la raíz

```
$ ./.venv/Scripts/python.exe -m pytest tests -q --tb=short
......                                                                   [100%]
6 passed in 0.25s
```

### Lint de los ficheros nuevos

```
$ ./.venv/Scripts/python.exe -m ruff check tests --output-format=concise
All checks passed!
```

El contador global de `init.sh` sigue en **444 avisos** de deuda previa, igual
que antes de la feature: los ficheros nuevos no añaden ninguno.

### Portero del arnés (`bash harness/init.sh`, tal cual)

Extracto de la salida final; termina en verde:

```
[OK] Arnés v1.4.0 (2026-08-13)
[OK] Python: Python 3.12.7
     7 features, 7 abiertas, en curso: ['F-001'], bloqueadas: ninguna
[OK] features.json válido
[OK] harness/rigor.json y niveles declarados: válidos
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 444 avisos (deuda previa, no bloquea)
......                                                                   [100%]
6 passed in 0.49s
[OK] pytest en verde (con medición de cobertura)
[OK] harness/servicios.json válido
[AVISO] servicio sv1-email (services/partes-email): sin directorio de tests — NADIE está comprobando los tests de sv1-email
[AVISO] servicio sv2-extraccion (services/partes-api): sin directorio de tests — NADIE está comprobando los tests de sv2-extraccion
[AVISO] servicio sv3-persistencia (services/partes-persistencia): sin directorio de tests — NADIE está comprobando los tests de sv3-persistencia
[AVISO] servicio sv4-front (services/partes-front): sin directorio de tests — NADIE está comprobando los tests de sv4-front
[AVISO] servicio sv5-transfer (services/partes-transfer): sin directorio de tests — NADIE está comprobando los tests de sv5-transfer
[AVISO] servicio infra (infra): lenguaje 'otro' y sin comando_tests — NADIE está comprobando los tests de infra
[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)
[OK] Rama actual: feature/F-001-test-estructura
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

Los seis `[AVISO]` de servicios sin tests ya estaban antes de esta feature
(están en la ejecución de partida) y quedan **fuera de alcance**: F-001 crea la
suite de la raíz, no las de cada servicio.

## Fase RED (rigor `estandar`)

El entregable de esta feature **es el propio test**: no hay código de
producción nuevo cuyo fallo previo se pueda enseñar. Se aplica por tanto el
procedimiento que CHECKPOINTS.md prevé para ese caso: romper deliberadamente lo
que el test vigila **en una copia aislada, nunca en el árbol real**, y pegar la
traza.

**Montaje de la copia aislada** (fuera del repositorio, en el scratchpad de la
sesión: `…/scratchpad/red-f001`): se copian `harness/` y `tests/`, y se crea un
árbol de servicios de mentira que cumple la declaración (cinco carpetas con
`main.py` + `infra/`). Se comprueba primero que la copia es un **espejo fiel** y
que se está ejecutando el módulo de la copia, no el del repositorio:

```
$ cd <scratchpad>/red-f001
$ python -c "import sys; sys.path.insert(0,'.'); import harness.servicios as m; print('modulo usado:', m.__file__)"
modulo usado: C:\...\scratchpad\red-f001\harness\servicios.py

$ python -m pytest tests -q --tb=short
......                                                                   [100%]
6 passed in 0.26s
```

### Rotura 1 — se borra la carpeta de un servicio declarado (`services/partes-api`)

```
$ rm -rf services/partes-api
$ python -m pytest tests -q --tb=short
tests\test_estructura_monorepo.py:40: in _servicios_declarados
    return cargar_servicios(raiz=str(RAIZ))
harness\servicios.py:168: in cargar_servicios
    _comprobar_conjunto(servicios, raiz)
harness\servicios.py:133: in _comprobar_conjunto
    raise ValueError(
E   ValueError: servicio 'sv2-extraccion': la ruta 'services/partes-api' no existe en el repositorio
=========================== short test summary info ===========================
FAILED tests/test_estructura_monorepo.py::test_f001_r1_la_declaracion_de_servicios_no_esta_vacia
FAILED tests/test_estructura_monorepo.py::test_f001_r1_cada_ruta_declarada_existe_y_es_un_directorio
FAILED tests/test_estructura_monorepo.py::test_f001_r1_cada_servicio_python_tiene_punto_de_entrada
3 failed, 3 passed in 0.30s
```

Restaurada la carpeta: `6 passed in 0.05s`.

### Rotura 2 — la carpeta existe pero se queda sin punto de entrada

```
$ rm -f services/partes-transfer/main.py
$ python -m pytest tests -q --tb=short
..F...                                                                   [100%]
================================== FAILURES ===================================
__________ test_f001_r1_cada_servicio_python_tiene_punto_de_entrada ___________
tests\test_estructura_monorepo.py:93: in test_f001_r1_cada_servicio_python_tiene_punto_de_entrada
    assert encontrados, (
E   AssertionError: servicio 'sv5-transfer' (services/partes-transfer): declarado 'python' y no tiene ninguno de ['main.py', 'pyproject.toml']. O le falta el punto de entrada, o el lenguaje declarado no es el suyo
E   assert []
=========================== short test summary info ===========================
FAILED tests/test_estructura_monorepo.py::test_f001_r1_cada_servicio_python_tiene_punto_de_entrada
1 failed, 5 passed in 0.27s
```

Restaurado el `main.py`: `6 passed in 0.05s`.

### Rotura 3 — `harness/servicios.py` deja de comprobar que la ruta exista

Es la rotura que ataca directamente a R2: en la copia se sustituye el bloque
`if not (Path(raiz) / servicio.ruta).is_dir(): raise ValueError(...)` de
`_comprobar_conjunto` por un `pass`.

```
$ python -m pytest tests -q --tb=short
...F..                                                                   [100%]
================================== FAILURES ===================================
_________ test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion _________
tests\test_estructura_monorepo.py:112: in test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion
    with pytest.raises(ValueError) as error:
E   Failed: DID NOT RAISE ValueError
=========================== short test summary info ===========================
FAILED tests/test_estructura_monorepo.py::test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion
1 failed, 5 passed in 0.12s
```

Restaurado `harness/servicios.py` en la copia: `6 passed in 0.30s`.

**El árbol real no se tocó en ningún momento.** Comprobado después de las tres
roturas:

```
$ git status --short
 M harness/features.json      <- lo dejó el líder al pasar F-001 a in_progress
 M progress/current.md        <- lo dejó el líder
$ git diff --name-status dev...HEAD
A       tests/conftest.py
A       tests/test_estructura_monorepo.py
```

## Evidencias

| Evidencia | Valor real | Cómo se obtuvo |
|---|---|---|
| Tests ejecutados y resultado | **6 tests, 6 passed, 0 failed** | `./.venv/Scripts/python.exe -m pytest tests -q` y la sección 7 de `bash harness/init.sh` |
| Cobertura de las líneas cambiadas | **N/A con motivo impreso**: `PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de producción frente a dev)` | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| Mutantes generados y supervivientes | **0 generados, 0 evaluados, 0 muertos, 0 supervivientes, 0 timeouts**; alcance 0 líneas de producción | `python -m harness.mutacion --feature F-001` → `progress/mutacion_F-001.md` |
| Tiempo de ejecución de la suite | **0,25 s** en ejecución directa; **0,49 s** bajo `coverage` dentro de `init.sh` | salida de pytest |

Sobre los dos `N/A`/ceros, para que el reviewer no tenga que deducirlos: ambos
salen del **mismo hecho**, y no de haber omitido la herramienta. Las dos
puertas miden líneas de **producción** cambiadas, y el diff de F-001 frente a
`dev` son dos ficheros que viven íntegramente en `tests/`. La campaña de
mutación **se lanzó** y dejó su informe; lo que no hay es materia que mutar.
Verificable de forma independiente con `git diff --name-status dev...HEAD` y
releyendo `progress/mutacion_F-001.md`.

## Verificaciones MANUAL (humano) pendientes

Ninguna. La feature no toca Sigrid, ni PostgreSQL, ni Azure, ni el portal: todo
lo comprobable está automatizado y ejecutado.

## Fuera de alcance (deliberado)

- Las suites de cada servicio (`services/*/tests/`): los seis `[AVISO]` de
  «NADIE está comprobando los tests de …» siguen ahí, tal y como estaban antes.
- Configuración de pytest a nivel de proyecto (`pytest.ini` / `pyproject.toml`)
  y CI: no hacen falta para este circuito y nadie los pidió.
- La deuda de lint previa (444 avisos de `ruff`).
- `harness/features.json` y `progress/current.md` aparecen modificados sin
  commitear: son cambios del líder, no míos. Marcar la feature `done` no me
  corresponde; eso ocurre tras el APROBADO del reviewer.

## Qué falta para cerrar

Revisión del `reviewer` contra `CHECKPOINTS.md` (C1–C5 y C4 bis) y, con su
veredicto APROBADO, que el líder pase F-001 a `done`.

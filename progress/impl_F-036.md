<!-- progress/impl_F-036.md -->
# F-036 · Informe del implementer

## Fase RED (trazas reales)

### T1 · caracterización (R20, R21) — en verde ANTES de tocar código

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_caracterizacion.py
18 passed in 0.30s
$ python -m pytest -q tests/test_f023_de_alta_gemelos.py tests/test_f024_borrado_no_congela_gemelos.py
18 passed in 0.52s
```

### T2 · R1 (`res.cla` en el maestro)

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_maestro.py
>       assert "res.cla AS cla" in sql
E       AssertionError: assert 'res.cla AS cla' in 'SELECT res.ide AS ide, res.cif AS cif, res.conide AS conide, ... ORDER BY res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
>       assert [(r.ide, r.cla) for r in recursos] == \
E       AttributeError: 'RecursoRow' object has no attribute 'cla'
>       assert RecursoRow(ide=1, cif=None, conide=None).cla is None
E       AttributeError: 'RecursoRow' object has no attribute 'cla'
3 failed in 0.75s
```
Tras el código: `3 passed`; suite sv3 `776 passed`.

### T3 · R2, R3 (filtro persona, DNI del recurso, INFO)

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_maestro.py
      7 E       AttributeError: 'IndicePersonas' object has no attribute 'dni_de_recurso'
      6 E         Use -v to get more diff
      6 E         
      5 E       AttributeError: module 'application.services.seleccion_sigrid' has no attribute 'es_persona'
      3 E       AssertionError: assert (900, 'ok') == (None, 'desconocido')
      3 E         At index 0 diff: 900 != None
      1 E       assert frozenset({1, 28, 31}) == frozenset({28})
      1 E       AttributeError: module 'application.services.seleccion_sigrid' has no attribute 'CLA_PERSONA'
      1 E       AttributeError: 'IndicePersonas' object has no attribute 'ficha_enlazada'
      1 E       AssertionError: assert (None, 'ambiguo') == (901, 'ok')
      1 E       AssertionError: assert (901, 'ok') == (902, 'ok')
      1 E         Extra items in the left set:
      1 E         At index 0 diff: None != 901
      1 E         At index 0 diff: 901 != 902
21 failed, 4 passed in 1.42s
```
Tras el código: `79 passed` (maestro + F-023 selección); suite sv3 `798 passed`. Nota: `dni_de_recurso` y `ficha_enlazada` (de T4 en `tasks.md`) se adelantan a T3 porque el INFO de R3 los necesita.

### T4 · R3, R4, R5, R7 (`candidatos_nombre`, `casar_por_dni`)

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_seleccion.py
     17 E       AttributeError: 'IndicePersonas' object has no attribute 'casar_por_dni'
      3 E       AttributeError: 'IndicePersonas' object has no attribute 'candidatos_nombre'
20 failed in 0.86s
```
Tras el código: `20 passed in 0.23s`.

### T5 · R10, R11, R12 (`match_nombre` por persona)

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_casado.py -k nombre
     16 E       TypeError: EmpleadoMatcher.match_nombre() got an unexpected keyword argument 'candidatos'
16 failed in 0.46s
```
Tras el código: `16 passed in 0.42s`; suite sv3 `834 passed`. El `match_nombre` de fichas
de F-023 queda como `match_nombre_fichas` transitorio para que el pipeline siga en verde
hasta T7, que lo retira.

### T6 · R4–R8, R13, R14 (`casar_trabajador`)

Primero, sin el módulo: `ModuleNotFoundError: No module named 'application.services.casado_recurso'`
(error de colección). Para ver el fallo test a test, con un esqueleto que solo lanza
`NotImplementedError`:

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_casado.py
     37 E       NotImplementedError
37 failed, 16 passed in 2.99s      (los 16 en verde son los de match_nombre de T5)
```
Tras el código: `53 passed in 0.69s`.

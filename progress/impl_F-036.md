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

### T7 · R6, R13–R17, R22 (pipeline)

```
$ cd services/partes-persistencia && python -m pytest -q tests/test_f036_pipeline.py
E       AssertionError: assert (None, None, ...otra_empresa') == (None, 'MO/95...'recurso_dni')     # R7/R14
E       AssertionError: assert (None, None, ...'recurso_dni') == (None, 'MO/96...'recurso_dni')     # R14 (codigo)
E       AssertionError: assert (60, 'E60', '...965, 'nombre') == (60, 'E60', '...', 965, 'dni')    # DA1
E       AssertionError: assert (None, None, ...curso_nombre') == (None, 'MO/96...curso_nombre')    # R14
E       AssertionError: assert (None, None, ...mbre_ambiguo') == (None, None, ...'dni_ambiguo')    # R5
E       AssertionError: assert 1 == 0                                                              # R6 alias perezoso
E       assert [] == [(1, 20260915)]                                                               # memo por parte
E       AssertionError: assert ModuleSpec(name='application.services.fichas_de_recurso', ...) is None   # R17
E       AssertionError: assert ['tests\\test...didatas', ...] == []                                # R17
E       assert (910, 911) == (911, 911)                                                            # R22 (fixture, ver nota)
10 failed, 10 passed in 6.39s
```
Tras el código: `20 passed`; suite sv3 `871 passed`; `git grep -n "fichas_de_recurso\|fichas_candidatas\|matchers.recursos" services/partes-persistencia` vacío.

Nota honesta sobre R22: el fallo de la traza era del fixture (dos partes de la misma obra y día:
el segundo **sustituye** al primero, `_deactivate_same_day_obra`); se corrigió poniendo el parte
nuevo otro día. Con eso, R22 pasa también con el código anterior: el casado ya solo corría en
`_match` de un parte nuevo. Es de caracterización, no de fase RED.

Tests de F-023/F-030 retirados o adaptados (desviación declarada en design §7):

- `test_f030_casado_recurso.py`: **retirados** los de `fichas_de_recurso` (R4, 9), los del
  proveedor (`Matchers.recursos`, 3), los de logs del respaldo (R6, 5) y los de `_Prohibido`
  sobre `recursos` (R7, 3). **Adaptados**: R12 (`codigo` = `con.cod` del recurso y `dni`
  normalizado, R14), R8 «no hay alias de recurso» → `test_f030_r8_alias_de_un_recurso_sin_ficha_casa`
  (ahora casa, `recurso_nombre`, R8), R9 nombre de recurso (`codigo`), R9 otra empresa (la
  ficha 11 gana su recurso). Renombrados 3 para quitar «fichas_de_recurso» del nombre.
- `test_f023_pipeline_match.py`: fixture con recurso 940 de DIANA (baja del recurso);
  `r23_alias_sin_dni_fuera_de_r17_no_es_valido` → `r23_alias_sin_dni_toma_el_de_su_ficha`
  (`dni_otra_empresa`, R8) + nuevo `r23_alias_sin_dni_ni_ficha_no_es_valido`; `r24` con fichas
  sin DNI → `none` (R3: un recurso persona sin DNI no es candidato) en
  `r24_fichas_sin_dni_no_compiten_por_nombre` y `r24_una_sola_ficha_sin_dni_no_casa_por_nombre`;
  `r24_empate_con_otra_persona` y `r24_la_otra_ficha_del_mismo_dni...` ganan recursos.
- `test_f023_seleccion_sigrid.py`: retirado `r17_fichas_candidatas_de_alta_y_de_la_empresa`.

### T9 · R18 (sv5 `recursos_por_dni` con `res.cla = 1`)

```
$ cd services/partes-transfer && python -m pytest -q tests/test_f036_recursos_por_dni_persona.py
E           AssertionError: SELECT REPLACE(REPLACE(UPPER(ISNULL(emp.dni,'')),'-',''),' ','') AS dnin, res.ide AS reside FROM res JOIN emp ON emp.ide = res.conide WHERE REPLACE(...) IN (?)
E           assert None
E            +  where None = <function search ...>('\bAND res\.cla = 1\b', "SELECT ... IN (?)")
1 failed, 1 passed in 2.90s
```
Tras el código: `2 passed`; suite sv5 `524 passed, 1 warning`.

### T10 · R19 (guardián raíz `tests/test_f036_recurso_persona_gemelos.py`)

El guardián se copió **fuera del repo** (scratchpad) con los tres ficheros vigilados y se
ejecutó `python -m pytest -q tests/test_f036_recurso_persona_gemelos.py -k "not falla"` en
cada copia:

```
== dev (los ficheros de antes de F-036)
E       AssertionError: CLA_PERSONA = None, se esperaba 1
E           AssertionError: IndicePersonas.__init__ ya no filtra con es_persona
E       AssertionError: _SQL_RECURSOS ya no lee res.cla
E       AssertionError: CLA_PERSONA = None, se esperaba 1
4 failed, 7 deselected in 1.76s
== rota_sv5 (segunda rama de recursos_por_dni sin AND res.cla = 1)
E           AssertionError: una rama de recursos_por_dni perdio res.cla
1 failed, 3 passed, 7 deselected in 1.29s
== rota_sv3 (IndicePersonas sin filter(es_persona, ...))
E           AssertionError: IndicePersonas.__init__ ya no filtra con es_persona
1 failed, 3 passed, 7 deselected in 1.26s
```
En el repo: `11 passed in 0.44s` (incluye 7 tests que estropean una copia en memoria y exigen
que la comprobación falle).

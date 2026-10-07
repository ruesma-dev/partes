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

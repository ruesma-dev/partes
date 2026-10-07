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

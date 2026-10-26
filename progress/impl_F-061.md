# F-061 · Informe del implementer

Rama `feature/F-061-parte-vacio-tras-borrar-lineas`, worktree `partes-wt-f061`. Solo sv4
(`services/partes-front`). Rigor `estandar`. Spec: `specs/F-061-parte-vacio-tras-borrar-lineas/`.

## Fase RED

### T1 · `tests/test_f061_borrado.py` y `tests/test_f061_papelera.py` (R1–R11)

Comando (desde `services/partes-front`):
`python -m pytest tests/test_f061_borrado.py tests/test_f061_papelera.py -q`

```
=================================== ERRORS ====================================
_________________ ERROR collecting tests/test_f061_borrado.py _________________
E   ModuleNotFoundError: No module named 'application.services.parte_vacio'
________________ ERROR collecting tests/test_f061_papelera.py _________________
E   ModuleNotFoundError: No module named 'application.services.parte_vacio'
ERROR tests/test_f061_borrado.py
ERROR tests/test_f061_papelera.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
1 warning, 2 errors in 2.87s
```

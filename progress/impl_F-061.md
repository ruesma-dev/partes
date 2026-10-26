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

Con `parte_vacio.py` ya creado (T2), el mismo comando sigue en ROJO por lo que falta en el
repositorio y el portal (`--tb=line`, causas; 26 failed, 10 passed):

```
tests\test_f061_borrado.py:72: AttributeError: 'ParteReviewRepository' object has no attribute 'borrar_linea'
tests\test_f061_borrado.py:113: assert False            (soft_delete_registro no retira el parte)
tests\test_f061_borrado.py:124: AssertionError: assert {'ok': True} == {'ok': True, ...': 'doc-f004'}
tests\test_f061_borrado.py:150: assert False            (soft_delete_worker lo manda a la papelera de partes)
tests\test_f061_borrado.py:173: AssertionError: assert False   (_deshacer_creadas no retira)
tests\test_f061_borrado.py:201: AttributeError: type object 'ParteReviewRepository' has no attribute '_sql_bloqueo_documentos'
tests\test_f061_borrado.py:212: AttributeError: type object 'ParteReviewRepository' has no attribute '_bloquear_documentos'
tests\test_f061_papelera.py:76: AttributeError: 'ParteReviewRepository' object has no attribute 'borrar_linea'
tests\test_f061_papelera.py:157: Failed: DID NOT RAISE DuplicadoActivoError
tests\test_f061_papelera.py:167: Failed: DID NOT RAISE DuplicadoActivoError
tests\test_f061_papelera.py:204: assert False            (restore_document no devuelve las líneas)
```

### T2 · funciones puras (`tests/test_f061_limpieza.py`, parte pura)

Su ROJO es el de T1 (`ModuleNotFoundError: No module named 'application.services.parte_vacio'`).
Tras crear el módulo: `python -m pytest tests/test_f061_limpieza.py -q` ⇒ `35 passed in 0.27s`.

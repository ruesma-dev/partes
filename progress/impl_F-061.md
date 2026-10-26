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

### T7 · `tests/test_f061_portal.py` (R12, R13 y el aviso de R7)

Comando: `python -m pytest tests/test_f061_portal.py -q --tb=line` (10 failed, 2 passed):

```
tests\test_f061_portal.py:48: AssertionError: app.js no define destinoTrasBorrar   (x4)
tests\test_f061_portal.py:102: assert (<re.Match ...'_bindClick(".line-del", ...> and '_irTrasBorrar([d])' in ...
tests\test_f061_portal.py:116: AssertionError: [data-restore-doc]
tests\test_f061_portal.py:148: assert (2, 3) == (1, 2)      (list_partes contaba las de la papelera)
tests\test_f061_portal.py:160: AttributeError: 'ParteRow' object has no attribute 'sin_lineas'
tests\test_f061_portal.py:171: AttributeError: 'ParteRow' object has no attribute 'sin_lineas'
tests\test_f061_portal.py:184: assert 0 == 1                (la plantilla no pinta «Sin líneas»)
```

Tras el cambio: `12 passed`; `node --check static/app.js` sin errores; `partes_list.html` parsea
en Jinja2 (test `test_f061_r13_partes_list_parsea_en_jinja2`).

### T8 · R14–R18 (`tests/test_f061_limpieza.py`, script y repositorio)

Comando: `python -m pytest tests/test_f061_limpieza.py -q --tb=line`. Primero, sin el script:

```
E   ModuleNotFoundError: No module named 'limpiar_partes_vacios'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.96s
```

Con el script y sin los métodos del repositorio (5 failed, 38 passed):

```
limpiar_partes_vacios.py:92: AttributeError: 'ParteReviewRepository' object has no attribute 'partes_vacios_activos'   (x4)
tests	est_f061_limpieza.py:286: AttributeError: 'ParteReviewRepository' object has no attribute 'limpiar_vacios'
```

Tras `partes_vacios_activos` y `limpiar_vacios`: `43 passed`. `python limpiar_partes_vacios.py
--ejecutar` (sin `--esperados`) ⇒ `error: --ejecutar exige --esperados N`, código 2, sin tocar la base.

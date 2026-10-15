# F-048 · Informe del implementer (PARCIAL: bloqueada en T1)

Estado: **blocked** (2026-10-15). Motivo y propuesta en `progress/current.md`
(seis tests guardianes de las 56 columnas de `parte_registros`, fuera de design §5).
Este informe se completará al reanudar; por ahora solo guarda la fase RED de T1.

## Hecho hasta el bloqueo (T1 sin su verde completo)

- `services/partes-persistencia/domain/models/parte_records.py`: `RegistroNormalizado.horas_extra_leidas`.
- `services/partes-persistencia/infrastructure/database/orm_models.py` y
  `services/partes-front/infrastructure/database/orm_models.py`: columna `Float` nula tras
  `horas_orig` (copias byte-idénticas, `cmp` sin diferencias).
- `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py`
  (`save_parte`): `horas_extra_leidas=reg.horas_extra_leidas`.
- `services/partes-persistencia/tests/test_f048_esquema.py` (R6, R24, campo de R2).

## Fase RED · T1 (R6, R24)

Comando (desde `services/partes-persistencia`, antes de tocar el código):
`python -m pytest -q --tb=line -p no:cacheprovider tests/test_f048_esquema.py`

```
E   AssertionError: assert 'horas_extra_leidas' in {'line_index': Field(name='line_index',type='int',default=<dataclasses._MISSING_TYPE object at 0x0000027015EE6B10>,def...015EE6B10>,init=True,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD), ...}
E   TypeError: RegistroNormalizado.__init__() got an unexpected keyword argument 'horas_extra_leidas'
=========================== short test summary info ===========================
FAILED tests/test_f048_esquema.py::test_f048_r24_ddl_complementario_anade_la_columna
FAILED tests/test_f048_esquema.py::test_f048_r24_columna_float_nula_y_sin_defecto
FAILED tests/test_f048_esquema.py::test_f048_r24_columna_justo_tras_horas_orig
FAILED tests/test_f048_esquema.py::test_f048_r2_el_registro_normalizado_la_lleva_nula_por_defecto
FAILED tests/test_f048_esquema.py::test_f048_r6_save_parte_guarda_y_se_relee
5 failed in 5.56s
```

Errores de los tres primeros (cabecera de la salida, recortada): `assert 'ALTER TABLE
parte_registros ADD COLUMN IF NOT EXISTS horas_extra_leidas FLOAT' in (...)` (falso),
`KeyError: 'horas_extra_leidas'` (la columna no existe en `__table__.c`) y
`ValueError: 'horas_extra_leidas' is not in list` (orden tras `horas_orig`).

Tras el cambio: `tests/test_f048_esquema.py` + `tests/test_f010_r6_ddl_complementario.py`
⇒ **20 passed**; sv4 `test_f010_r6_ddl_complementario_sv4.py` +
`test_f015_r30_ddl_empleado_jornada_sv4.py` ⇒ **14 passed**. Los seis guardianes de
`progress/current.md` ⇒ **6 failed** (motivo del bloqueo).

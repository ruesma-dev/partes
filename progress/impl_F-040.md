# F-040 · informe del implementer (PARCIAL: feature `blocked`)

> Estado al 2026-10-08: T1–T3 hechas, T4 hecha en código y tests nuevos pero
> **bloqueada** por tres tests de F-023 que se ponen rojos y la spec no
> declara como adaptables. Motivo y opciones: `progress/current.md`
> (sección F-040). Este informe se completa al retomar.

Entorno: worktree `partes-wt-f040`, rama `feature/F-040-recursos-sin-dni-por-nombre`;
`.venv` del repositorio principal (`C:/Users/pgris/PycharmProjects/partes/.venv`),
porque el worktree no tiene uno. `bash harness/init.sh` en verde al empezar
(sv4 1796 passed / 1 skipped en 12 min 38 s; sv5 524 passed).

## Tareas

| Tarea | Commit | Estado |
|---|---|---|
| T1 caracterización R13 | `f8143e9` | hecha: 19 tests en verde contra el código de antes; guardianes F-010/F-023/F-024/F-036 de la raíz en verde (52 passed) |
| T2 esquema sv3+sv4 (R20, R21) | `fd63c6f` | hecha |
| T3 `elegir_sin_dni` (R9) | `375a8e0` | hecha |
| T4 clave, casar_por_clave, R1, R10, R11 | `11a5a11` | código hecho; **bloqueada** (3 tests de F-023 en rojo) |
| T5–T13 | — | pendientes |

## Adaptaciones de tests existentes (hasta ahora)

- sv3 `tests/test_f010_r6_ddl_complementario.py` y sv4
  `tests/test_f010_r6_ddl_complementario_sv4.py` (design §8, «tests de DDL
  F-010»): exentan de «solo aditivo / IF NOT EXISTS» **solo** la sentencia
  exacta `ALTER TABLE empleado_alias ALTER COLUMN empleado_ide DROP NOT NULL`
  (`RELAJACIONES_PERMITIDAS`); sv4 añade esa sentencia a la tupla exacta de
  `DDL_EXTRA_POSTGRES`; sv3 gana `test_f040_r21_la_relajacion_permitida_es_solo_la_de_f040`.
- sv3 `tests/test_f036_seleccion.py` (declarada: «los de `candidatos_nombre`
  con DNI obligatorio»): los dos tests de `candidatos_nombre` esperan ahora
  también los recursos sin DNI; el primero se renombra a
  `test_f036_r3_candidatos_nombre_solo_persona_de_alta_y_empresa`.

## Fase RED (trazas reales)

### T2 sv3 — `../../.venv/Scripts/python.exe -m pytest -q --tb=line tests/test_f040_alias_repo.py`

```
E   AssertionError: assert False is True
E   AttributeError: recurso_ide
E   assert 'ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS recurso_ide INTEGER' in ("ALTER TABLE dedicacion_bandeja ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT '1' NOT NULL", ...)
E   AssertionError: assert 'ALTER TABLE empleado_alias ALTER COLUMN empleado_ide DROP NOT NULL' in ('CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active ON parte_documents (source_sha256) WHERE is_active',)
FAILED tests/test_f040_alias_repo.py::test_f040_r20_empleado_ide_es_nullable
FAILED tests/test_f040_alias_repo.py::test_f040_r20_recurso_ide_integer_nullable_al_final
FAILED tests/test_f040_alias_repo.py::test_f040_r21_ddl_anade_recurso_ide - a...
FAILED tests/test_f040_alias_repo.py::test_f040_r21_ddl_relaja_empleado_ide_al_final
4 failed, 1 passed in 4.42s
```

### T2 sv4 — mismo comando en `services/partes-front`

```
E   AssertionError: assert False is True
E   AttributeError: recurso_ide
E   assert 'ALTER TABLE empleado_alias ADD COLUMN IF NOT EXISTS recurso_ide INTEGER' in (...)
E   AssertionError: assert 'ALTER TABLE empleado_alias ALTER COLUMN empleado_ide DROP NOT NULL' in ('CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active ...',)
FAILED tests/test_f040_alias_repo.py::test_f040_sv4_r20_empleado_ide_es_nullable
FAILED tests/test_f040_alias_repo.py::test_f040_sv4_r20_recurso_ide_integer_nullable_al_final
FAILED tests/test_f040_alias_repo.py::test_f040_sv4_r21_ddl_anade_recurso_ide
FAILED tests/test_f040_alias_repo.py::test_f040_sv4_r21_ddl_relaja_empleado_ide_al_final
4 failed, 1 passed in 4.31s
```

(El que pasaba en ambos es `..._ninguna_sentencia_reescribe_filas`, una
guarda que ya se cumplía.)

### T3 sv3 — `../../.venv/Scripts/python.exe -m pytest -q --tb=line tests/test_f040_elegir_sin_dni.py`

```
19 x E   AttributeError: 'IndicePersonas' object has no attribute 'elegir_sin_dni'
19 failed in 0.50s
```

### T4 sv3 — `../../.venv/Scripts/python.exe -m pytest -q --tb=line tests/test_f040_seleccion.py`

```
 1 E   AssertionError: assert 'con_dni' in frozenset({'ambiguo', 'otra_empresa', 'solo_baja'})
 1 E   AssertionError: assert (None, 'sin_recurso') == (903, 'sin_parte')
 1 E   AssertionError: assert ResolucionRec...tra_empresa=0) == ResolucionRec...tra_empresa=0)
 3 E   AssertionError: assert [] == [['doc-1']]
10 E   AttributeError: 'IndicePersonas' object has no attribute 'casar_por_clave'. Did you mean: 'casar_por_dni'?
 1 E   AttributeError: 'IndicePersonas' object has no attribute 'clave_persona'
 1 E   assert [900, 901] == [900, 901, 902, 903, 907]
18 failed, 4 passed in 0.70s
```

(Los 4 que pasaban: `elegir_recurso` con DNI, con ficha, sin preferido y
el `desconocido` del conciliador, que caracterizan lo que R10 no cambia.)

## Evidencias

PENDIENTE: se completa al terminar (la feature está `blocked`).

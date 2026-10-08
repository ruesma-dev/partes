<!-- progress/impl_F-039.md -->
# F-039 · Informe del implementer (BORRADOR: feature blocked)

Rama `feature/F-039-nombre-empresa-en-combos` (worktree `partes-wt-f039`), sin
push. Intérprete: el `.venv` del repo principal. Motivo del bloqueo y opciones:
`progress/current.md` (sección F-039). Este borrador guarda las trazas RED
ya tomadas; se completa al desbloquear (T3).

## Estado

- **T1** hecha, commit `3c8275f`: `nombre_empresa_o_vacio` en
  `application/services/empresas.py`; `empresa_nombre` en
  `/api/sigrid/obras`, `/recursos`, `/empleados`, `/api/conciliacion/buscar`
  y en `_candidato_con_empresa` (`interface_adapters/web/app.py`; ya no
  importa `nombre_empresa`).
- **T2** hecha en el árbol, **sin commitear** (su verificación de suite sv4
  está roja por dos tests ajenos): `empresaSufijo` de `static/app.js` y tests
  R6–R10.
- T3, T4: pendientes.

## Fase RED (trazas reales; `cd services/partes-front`)

**T1 · R1–R5, R11, R12** — `python -m pytest tests/test_f039_nombre_empresa.py -q -rfE --tb=line`
(antes de tocar código):
```
  5 E       KeyError: 'empresa_nombre'
  5 E       AttributeError: module 'application.services.empresas' has no attribute 'nombre_empresa_o_vacio'
  1 E       AttributeError: <module 'interface_adapters.web.app' ...> has no attribute 'nombre_empresa_o_vacio'
  1 E         At index 0 diff: {'ide': 100, 'codigo': '070', 'nombre': 'Obra 0', 'empresa': 1} != {..., 'empresa': 1, 'empresa_nombre': 'Ruesma'}
  3 E             Extra items in the right set: 'empresa_nombre'      (R12 recursos/buscar/empleados)
FAILED ...::test_f039_r1_obras_lleva_empresa_nombre
FAILED ...::test_f039_r2_recursos_lleva_empresa_nombre
FAILED ...::test_f039_r2_recursos_filtrados_por_empresa
FAILED ...::test_f039_r3_buscar_lleva_empresa_nombre
FAILED ...::test_f039_r4_empleados_lleva_empresa_nombre
FAILED ...::test_f039_r5_nombre_empresa_o_vacio[1-Ruesma|28-Porsan|5-Empresa 5|0-Empresa 0|None-]  (x5)
FAILED ...::test_f039_r5_empresa_sin_nombre_es_empresa_n
FAILED ...::test_f039_r11_misma_funcion_que_los_endpoints
FAILED ...::test_f039_r12_obras_resto_de_campos_intacto
FAILED ...::test_f039_r12_resto_de_campos_intacto[recursos|buscar|empleados]  (x3)
16 failed, 1 passed, 1 warning in 21.33s
```
El que pasa es la guarda `test_f039_r11_candidatos_conciliar_con_nombre`
(design §4: R11 ya se cumplía). Tras el código: `17 passed in 22.77s`.

**T2 · R6–R10** — `python -m pytest tests/test_f039_nombre_empresa.py -q -k "r6 or r7 or r8 or r9 or r10" --tb=short`
(con el `empresaSufijo` de F-023):
```
E   AssertionError: assert [' · empresa ... · empresa 1'] == [' · Porsan', ' · Ruesma']
E     At index 0 diff: ' · empresa 28' != ' · Porsan'
E   AssertionError: assert [' · empresa ... · empresa 0'] == [' · Empresa ... · Empresa 0']
E     At index 0 diff: ' · empresa 5' != ' · Empresa 5'
E   assert ' · empresa ' not in '// static/a...});\n})();\n'
E        null) ? " · empresa " + x.empresa : "";
FAILED ...::test_f039_r6_empresa_sufijo_con_nombre
FAILED ...::test_f039_r7_empresa_sufijo_sin_nombre_es_empresa_n
FAILED ...::test_f039_r9_combos_usan_empresa_sufijo
3 failed, 2 passed, 17 deselected, 1 warning in 16.42s
```
Pasan las guardas R8 y R10 (design §4). Tras el código: `node --check
static/app.js` OK y `22 passed in 26.06s` (fichero completo).

## Suite sv4 tras T2 (motivo del bloqueo)

`python -m pytest tests -q` → **2 failed, 1793 passed, 1 skipped in 949.30s**:
```
FAILED tests/test_f015_r26_sugerida_fecha.py::test_f015_r26_sin_fecha_las_claves_son_las_de_siempre
E     Extra items in the left set: 'empresa_nombre'
FAILED tests/test_f023_catalogo_empresa.py::test_f023_r40_endpoint_obras_anade_la_empresa
E     At index 0 diff: {..., 'empresa': 1, 'empresa_nombre': 'Ruesma'} != {..., 'empresa': 1}
```

## Evidencias

PENDIENTE hasta desbloquear (cobertura, mutación muestreada, `init.sh` final).

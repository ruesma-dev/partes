<!-- progress/impl_F-021.md -->
# F-021 · Informe del implementer

Rama `feature/F-021-cuenta-analitica-sigrid`. Rigor **critico**. Spec
aprobada el 2026-10-01 (DA1–DA13 según recomendación).

## 0. Contraste con el código de `dev` (F-023 y F-024 ya mergeadas)

Revisados `sigrid_write_client.py`, `registro_pipeline.py`,
`reglas_registro.py`, `coherencia_recurso.py`, `comprobacion_lineas.py`
(F-024), `interface_adapters/api/app.py` de sv5 y el modal del preflight de
`static/app.js` (sv4). La spec sigue encajando sin cambiar comportamiento
ni decisiones:

- `preparar` ya tiene la empresa de la obra destino (F-023) y lee
  `horas_de_recursos` en el mismo punto; la cuenta se resuelve tras las
  reglas, como dice design §6.2.
- `ObraEntrada` no declara `cenide`: el cliente lo añade con `setattr`
  (`_a_obra`), igual que antes; `getattr(destino, "cenide", 0)` del diseño
  sigue siendo la vía correcta.
- El preflight de sv5 serializa `acciones` con `asdict`: los `caa_*` viajan
  sin tocar el adaptador (R13). `resultado_json.py` ya pasa `escritas` tal
  cual (R15).
- F-024 (comprobación) solo lee por `synckey`/`ide`; no compara `caaide`.
- sv4: `aprobar_preflight` reenvía el `dict` de sv5 (R21 sin código); el
  modal sigue construyéndose con `resumenHtml(pf)`. F-024 añadió `esc()`.

## 1. T1 · Inventario de tests afectados

Búsqueda de `stmt_insert_linea`, `horas_de_recursos`, `HoraRecurso(`,
`AccionLinea(` y comparaciones de `escritas` en las suites de sv5, sv4 y
raíz:

| Test | Qué usa | Impacto |
|---|---|---|
| `tests/dobles.py` (sv5) | `SigridFake.stmt_insert_linea` (sin `caaide`) y `horas_de_recursos` | **Se adapta en T7**: con `caaide` obligatorio el pipeline lo pasa y el doble debe aceptarlo |
| `test_f002_pipeline_fases.py:37-41` | `HoraRecurso(horide, cod, res, pre)` | Ninguno: los campos nuevos tienen valor por defecto |
| `test_f023_escritura_empresa.py:353` | `HoraRecurso(...)` | Ninguno (ídem) |
| `test_f023_escritura_empresa.py:416` | `"horas_de_recursos" not in cli.llamadas` | Ninguno: la obra sin empresa falla antes |
| `test_f002_workers.py:121` | concurrencia de `horas_de_recursos` | Ninguno |
| `test_f002_*`, `test_f023_*`, sv4 `test_f002_aprobar_encolar.py` | `escritas` por `registro_id` o `== []` | Ninguno: no comparan el dict entero |

**Ningún test** llama a `SigridWriteClient.stmt_insert_linea` real ni
compara el SQL de `horas_de_recursos`: no hay tests que adaptar en T6 más
allá del doble.

## 2. Fase RED (trazas reales)

### T2 · regla pura (R1, R2, R4, R5, R6, R8)

`cd services/partes-transfer && python -m pytest -q tests/test_f021_cuenta_analitica.py`

```
____________ ERROR collecting tests/test_f021_cuenta_analitica.py _____________
tests\test_f021_cuenta_analitica.py:18: in <module>
    from application.services.cuenta_analitica import (
E   ModuleNotFoundError: No module named 'application.services.cuenta_analitica'
ERROR tests/test_f021_cuenta_analitica.py
1 error in 0.25s
```

### T5 · cliente (R9, R10, R11, R14)

`cd services/partes-transfer && python -m pytest -q tests/test_f021_cliente_cuenta.py`
(líneas `E`/`FAILED` de la salida real; el diff largo del SQL, recortado)

```
E   {501: [HoraRecurso(horide=11, cod='HL01', res='Laborable', pre=10.0, caa_cod=None, defecto=False), ...]} != {501: [HoraRecurso(horide=11, ..., caa_cod='00000.LAB', defecto=True), ...]}
E   - pre AS pre, cc.cod AS caacod, CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END AS defecto FROM reshor ... LEFT JOIN con cc ON cc.ide = reshor.caaide AND ISNULL(reshor.caaide, 0) <> 0 WHERE ...
E   + pre AS pre FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide WHERE reshor.reside IN (?,?) ORDER BY reshor.reside, auxhor.cod
E   AttributeError: 'SigridWriteClient' object has no attribute 'cuentas_de_centro'   (x6)
E   TypeError: SigridWriteClient.stmt_insert_linea() got an unexpected keyword argument 'caaide'   (x3)
E   Failed: DID NOT RAISE TypeError
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r9_horas_traen_la_cuenta_y_el_defecto
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r9_horas_misma_consulta_con_cuenta_y_defecto
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r10_una_lectura_por_centro_empresa_y_subcuentas
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r10_el_filtro_sql_solo_acota
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r10_los_parametros_son_enteros
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r10_sin_subcuentas_no_lee
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r11_cuentas_truncated_es_excepcion
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r11_cuentas_error_http_es_excepcion
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r14_caaide_es_un_parametro_del_insert
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r8_r14_sin_cuenta_se_escribe_cero_como_parametro
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r14_caaide_se_convierte_a_entero
FAILED tests/test_f021_cliente_cuenta.py::test_f021_r14_caaide_es_obligatorio
12 failed, 1 passed in 0.47s
```
(El que pasa es `test_f021_r9_horas_sin_recursos_no_lee`: comportamiento previo que se conserva.)

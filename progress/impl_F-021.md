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

### T7 · doble con `caaide` obligatorio (R14 a nivel de pipeline)

Con `SigridFake.stmt_insert_linea(..., caaide)` obligatorio y el pipeline
aún sin tocar, `cd services/partes-transfer && python -m pytest -q`
(agregado con `grep -E "^E |failed|passed" | sort | uniq -c`):

```
      9 E           TypeError: SigridFake.stmt_insert_linea() missing 1 required keyword-only argument: 'caaide'
      1 E         Left contains 3 more items, first extra item: TypeError("SigridFake.stmt_insert_linea() missing 1 required keyword-only argument: 'caaide'")
      1 21 failed, 229 passed, 5 warnings in 10.03s
```
Desviación de orden (D2): la verificación de T7 («suite en verde») solo se
alcanza en T9, porque el doble exige ya `caaide` (DA9) y el pipeline lo
pasa en T9. Se deja así a propósito: es la traza RED de que el pipeline
no escribía la cuenta.

### T8 · pipeline (R8, R10–R18)

`cd services/partes-transfer && python -m pytest -q tests/test_f021_pipeline_cuenta.py`
(agregado con `grep -E "^(E  |FAILED)|passed|failed" | sort | uniq -c`, extracto)

```
     10 E           TypeError: SigridFake.stmt_insert_linea() missing 1 required keyword-only argument: 'caaide'
      1 E       ValueError: not enough values to unpack (expected 1, got 0)
      1 E       Failed: DID NOT RAISE RuntimeError
      1 E         {1: (0, None, None)} != {1: (701, '0100.LAB', None)}
      1 E         {2: (0, None, None)} != {2: (702, '0100.EXT', None)}
      1 E         {3: (0, None, None)} != {3: (0, None, 'obra_sin_cuenta')}
      1 E         {4: (0, None, None)} != {4: (0, None, 'recurso_sin_cuenta')}
      1 E         At index 0 diff: ('escribir', 0) != ('escribir', 701)
      1 E       AssertionError: assert None == 'obra_sin_cuenta'
FAILED ...::test_f021_r8_sin_cuenta_la_linea_se_escribe_igual
FAILED ...::test_f021_r10_una_lectura_por_peticion_con_centro_empresa_y_subs
FAILED ...::test_f021_r10_sin_subcuentas_no_se_lee
FAILED ...::test_f021_r11_fallo_al_leer_cuentas_no_escribe_nada
FAILED ...::test_f021_r11_fallo_al_leer_cuentas_tumba_el_preflight
FAILED ...::test_f021_r12_se_resuelve_en_preparar_tras_las_reglas
FAILED ...::test_f021_r12_preflight_y_ejecutar_obtienen_la_misma_cuenta
FAILED ...::test_f021_r12_la_lectura_de_cuentas_va_fuera_del_lock
FAILED ...::test_f021_r13_el_preflight_trae_la_cuenta_de_cada_accion
FAILED ...::test_f021_r14_r15_insert_con_caaide_y_escritas_con_caa_cod
FAILED ...::test_f021_r17_al_pisar_la_linea_nueva_lleva_la_cuenta
FAILED ...::test_f021_r18_log_por_motivo_sin_datos_personales
FAILED ...::test_f021_r4_la_cuenta_es_de_la_empresa_de_la_obra
FAILED ...::test_f021_r5_obra_sin_centro_no_lee_y_avisa
FAILED ...::test_f021_r5_obra_sin_atributo_cenide_es_sin_centro
FAILED ...::test_f021_modo_pruebas_usa_el_centro_de_la_obra_de_pruebas
16 failed, 2 passed in 1.01s
```
Pasan en RED, a propósito, dos guardas de lo que NO debe cambiar:
`test_f021_r16_ya_registrada_no_se_reescribe_ni_se_actualiza` (el código
previo ya no reescribía) y `test_f021_r10_sin_nada_que_escribir_no_se_lee`.
La parte de R16 «`omitir` sale con `caa_ide = 0` y sin motivo» tampoco
puede fallar en RED: son los valores por defecto de T4. Lo que la protege
es que `_resolver_cuentas` solo toque acciones `escribir` (mutantes de T15).

### T10 · modal del preflight de sv4 (R19–R21)

`cd services/partes-front && python -m pytest -q tests/test_f021_preflight_cuenta.py`
(agregado con `grep -E "^E  |FAILED|passed|failed" | sort | uniq -c`, extracto)

```
      9 E       AssertionError: app.js no define avisosCuentaHtml
      1 E       assert 'avisosCuentaHtml(pf.acciones)' in '\n  function resumenHtml(pf) {\n    var r = pf.resumen || {};\n ... + "</p>" + omHtml;\n  }\n'
FAILED ...::test_f021_r19_app_js_define_avisos_cuenta_y_filtra_escribir
FAILED ...::test_f021_r19_cuenta_todas_las_lineas_con_aviso
FAILED ...::test_f021_r19_escapa_el_texto_que_llega_del_servidor
FAILED ...::test_f021_r19_pinta_una_fila_por_linea_escribir_con_aviso
FAILED ...::test_f021_r19_resumen_html_llama_a_avisos_cuenta
FAILED ...::test_f021_r20_sin_avisos_no_pinta_el_bloque[None]
FAILED ...::test_f021_r20_sin_avisos_no_pinta_el_bloque[acciones0..4]   (x4)
10 failed, 1 passed, 1 warning in 4.32s
```
El que pasa es `test_f021_r21_el_preflight_reenvia_los_caa_de_sv5`: R21 no
exige código (design §5: `aprobar_preflight` ya reenvía la respuesta).

<!-- progress/impl_F-021.md -->
# F-021 · Informe del implementer

Rama `feature/F-021-cuenta-analitica-sigrid`. Rigor **critico**. Spec
aprobada el 2026-10-01 (DA1–DA13 según recomendación). T1–T16 hechas.

## 0. Contraste previo con `dev` (F-023 y F-024 ya mergeadas)

**Nada cambia comportamiento ni decisiones**: `preparar` ya tiene la empresa
(F-023) y lee `horas_de_recursos` en el mismo punto; `cenide` llega por
`setattr`; `acciones` se serializa con `asdict`; F-024 no mira `caaide`;
sv4 reenvía el `dict` de sv5 y el modal sigue saliendo de `resumenHtml`.

## 1. Qué cambió, por servicio

**sv5** (`services/partes-transfer/`)
- `application/services/cuenta_analitica.py` (nuevo, puro): `subcuenta`,
  `subcuenta_de_linea` (R1–R2), `CuentaLinea`, `indexar_cuentas`,
  `resolver_cuenta` (R3–R6) y los tres motivos.
- `domain/models/registro_models.py`: `HoraRecurso.caa_cod/defecto`;
  `AccionLinea.caa_ide/caa_cod/caa_motivo/caa_aviso`, con defaults.
- `infrastructure/sigrid/sigrid_write_client.py`: `horas_de_recursos` con
  `caacod` y `defecto` en la misma consulta (R9); `cuentas_de_centro`
  nuevo, una lectura agrupada con `indexar_cuentas` (R10–R11);
  `stmt_insert_linea(..., caaide)` obligatorio y `caaide` como `?` (R14);
  docstring de cabecera.
- `application/pipelines/registro_pipeline.py`: paso 4b
  `_resolver_cuentas(destino, empresa, acciones, horas)` al final de
  `preparar` (fuera del lock, sin `try`), log INFO por motivo (R18);
  `caaide=int(a.caa_ide)` en el `INSERT` y `caa_cod` en `escritas` (R15).
- `prueba_escritura_sigrid.py`: solo dos comentarios (DA11).
- Tests nuevos: 36 + 13 + 18 (`test_f021_*`); `tests/dobles.py` con
  `cuentas_de_centro` (llamadas, `bajo_lock`, `fallo_cuentas`) y `caaide`.

**sv4** (`services/partes-front/`)
- `static/app.js`: `avisosCuentaHtml(acciones)` (filtra `escribir` con
  `caa_aviso`, `""` si no hay) llamado al final de `resumenHtml(pf)`. Sin
  cambios en Python (R21 ya se cumplía).
- `tests/test_f021_preflight_cuenta.py` (11): R21 por HTTP, texto de
  `app.js` y la función **ejecutada con `node`** (skip si no hay `node`).

**Docs**: `ARCHITECTURE.md` punto 13; `partes-proyecto.md` §3.5 (3b);
`azure-apps/partes.md` (commit local `2fd1e92`, sin push). sv1–sv3, ORM,
reglas, coherencia, `resultado_json.py`, `infra/`, `CLAUDE.md`: sin tocar.

## 2. Decisiones y desviaciones

- **D1 · orden T4 antes que T3**: los tests de `subcuenta_de_linea` (T2)
  construyen `HoraRecurso` con los campos nuevos.
- **D2 · T7 deja la suite en rojo hasta T9**: el doble exige `caaide`
  (DA9) y el pipeline lo pasa en T9; es a la vez la traza RED de R14 a
  nivel de pipeline (abajo).
- **D3 · el cliente importa `indexar_cuentas` de `application/services`**:
  lo pide la firma del diseño (§7, devuelve el dict agrupado); hay
  precedente en sv3/sv4 (`text_match`, `congelacion`).
- **D4 · el aviso de sv4 escapa** nombre, fecha y texto con el `esc()` de
  F-024 (`avisosCalendarioHtml`, el modelo citado, no escapa).
- **D5 · log R18 solo si hay acciones `escribir`**: sin ninguna no hay
  cuentas que resolver (test `..._sin_nada_que_escribir_no_se_lee`).
- Inventario T1: ningún test llamaba al `stmt_insert_linea` real ni
  comparaba el SQL de `horas_de_recursos`; solo había que adaptar el doble
  (los `HoraRecurso(...)` y `escritas` de F-002/F-023 no se ven afectados).
- `ruff`: nuevos limpios; `registro_models.py` +4 `UP045` (estilo del fichero).

## 3. Fase RED (trazas reales, comando exacto encima de cada una)

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
(Pasa `..._r9_horas_sin_recursos_no_lee`: comportamiento previo.)

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
Pasan en RED dos guardas de lo que NO cambia: `..._r16_ya_registrada_...`
y `..._r10_sin_nada_que_escribir_...`. «`omitir` con `caa_ide = 0`» (R16)
son los defaults de T4; lo protege el filtro `escribir` (mutantes T15).

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

## 4. Commits (todos locales)

`2dad9ab` T1 · `7806afb` T2 · `5a9682f` T4 · `9947927` T3 · `f732c2a` T5 ·
`a3788d5` T6 · `3ec0277` T7 · `83fa669` T8 · `ee5a79d` T9 · `d65a880` T10 ·
`6103a82` T11 · `34c2750` T12 · `f88019e` T13 · `42ff47e` T14 (+ `2fd1e92`
en azure-apps) · `b038943` estilo · `37fdcbd`, `fe3af66`, `489a515` T15 ·
el de T16 cierra este informe.

## 5. Evidencias

`bash harness/init.sh`: **verde** («ENTORNO LISTO»). `node --check
static/app.js`: OK. Mutación: 1.ª pasada 35 / **2 supervivientes** (`or 0`
muerto en el pipeline; default `defecto=False` sin test), cerrados en
`37fdcbd`; 2.ª pasada **33/33 muertos** (`progress/mutacion_F-021.md`).

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | sv5 269 passed; sv4 1.230 passed; raíz 419 passed + 1 skipped |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 76 líneas cambiadas cubiertas (76/76, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | 33 / 0 (`--workers 6 --timeout 600`, campaña completa, 82,4 s) |
| Tiempo de la suite | sv5 4,9 s; sv4 325 s; raíz 64 s |
| `app.js` | sin mutación ni cobertura (la herramienta solo cubre Python); cubierto por 8 tests que lo ejecutan con `node` |

## 6. Fuera de alcance y pendientes

Fuera (design §10): rellenar líneas ya registradas (DA6), `cuaide`,
`hmo.caaide`, mostrar la cuenta en otras pantallas. **Nada desplegado, ni
push.** Pendientes MANUAL (humano), detalle y SQL completo en design §9 y
`progress/current.md`:

- **M1** antes de desplegar sv5, lectura en `ruesma`: `SELECT h.ano, h.mes,
  COUNT(*) AS n, SUM(CASE WHEN ISNULL(h.caaide,0)=0 THEN 1 ELSE 0 END) AS
  sin_cuenta FROM hmores h WHERE h.synckey LIKE 'partes:%' GROUP BY h.ano,
  h.mes`. Esperado: 0 filas (o decidir según DA6).
- **M2** tras sv5, modo pruebas `0404`: la consulta de M2 (design §9) da
  `cuenta = <centro 0404>.<subcuenta>` y `ca.cenide = cen_obra`; log
  `[registro] cuentas obra=0404 ok=…`. Limpiar con `prueba_escritura_sigrid.py`.
- **M3** tras sv4 (Ctrl+F5): recurso con subcuenta que la `0404` no tiene
  ⇒ bloque «sin cuenta analitica» en el modal y línea con `caaide = 0`.
- **M4** Administración: la línea de M2 se ve como una tecleada; DA3/DA13.

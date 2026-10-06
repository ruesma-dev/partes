<!-- progress/mutacion_F-031.md -->
# F-031 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-031` el 2026-10-06 11:04.

## Alcance

Origen del diff: **rama** (`fccd09946f3eba178e32bc495e1b3a9766c913dd` .. `feature/F-031-asiento-analitico`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 182 |
| `services/partes-transfer/application/services/cuenta_analitica.py` | 43 |
| `services/partes-transfer/application/services/estado_parte.py` | 73 |
| `services/partes-transfer/comprobar_asiento_analitico.py` | 184 |
| `services/partes-transfer/config/settings.py` | 5 |
| `services/partes-transfer/domain/models/registro_models.py` | 30 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 45 |
| **Total** | **562** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 122 |
| Mutantes evaluados | 122 |
| Muertos | 122 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 304.9 s |
| SHA de HEAD medido | `bf7da1d314c818aa6039cddeef767dda2cfd605f` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_0/services/partes-transfer` | 13.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_1/services/partes-transfer` | 13.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_2/services/partes-transfer` | 13.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_3/services/partes-transfer` | 13.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_4/services/partes-transfer` | 14.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-031_kl1bxita/wk_5/services/partes-transfer` | 13.9 |
| Media por mutante evaluado (s) | 2.5 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Anexo · primera campaña (2026-10-06 10:57, HEAD `5993599`) y cómo se cerró

Misma orden (`--workers 6 --timeout 600`, campaña completa): **126
mutantes, 103 muertos, 23 supervivientes, 0 timeouts**, 317 s. Ninguno
se dio por equivalente: cada uno tiene un test en
`services/partes-transfer/tests/test_f031_mutantes.py` (commit `bf7da1d`)
salvo dos que desaparecieron al quitar código muerto. Esta campaña (la de
arriba) es la que vale: 122/122 muertos.

| # | Línea (campaña 1) | Mutación | Por qué sobrevivía | Cierre |
|---|---|---|---|---|
| 5 | `registro_pipeline.py:262` | `paride or 0` → `or 1` | ningún test con partida de `ide` 1 y otra línea sin partida | `test_m5_sin_partida_no_toma_la_partida_1` |
| 15 | `:341` | `or` → `and` en `if not grupo or not parte.del_periodo` | solo cambia lecturas de un periodo ya registrado | `test_m15_periodo_sin_escribir_no_lee_lineas` |
| 26, 29, 31 | `:388-394` | defectos 1/3/10 de `getattr` | los dobles siempre traen los ajustes | `test_m26_m29_m31_settings_sin_ajustes_usa_1_3_10` |
| 32, 41 | `:404` | `horide or 0` / `hora_ide or 0` → `or 1` | ninguna línea ni acción sin tipo | `test_m32_…`, `test_m41_…` (`_choques` directo) |
| 39 | `:405` | `synckey and … in mias` → `or` | ninguna línea ajena con synckey de OTRO registro nuestro | `test_m39_otra_linea_nuestra_tambien_choca` |
| 49 | `:440` | `recurso_ide or 0` → `and 0` | nadie miraba `Conflicto.recurso_ide` | `test_m49_el_conflicto_lleva_el_recurso` |
| 52 | `:437` | `horide or 0` → `or 1` (contexto) | ninguna línea de contexto sin tipo | `test_m52_linea_sin_tipo_es_contexto_del_tipo_1` |
| 55, 57 | `:437`, `:440` | `hora_ide`/`recurso_ide or 0` → `or 1` | acción sin tipo/recurso, solo defensivo | `test_m57_m55_conflicto_de_accion_sin_recurso_ni_tipo` (`_conflictos` directo) |
| 66, 113, 121 | `cuenta_analitica.py:73`, `registro_models.py:96,105` | `frozen=True` → `False` | nadie probaba la inmutabilidad que pide el design | `test_m66_m113_m121_valores_inmutables` |
| 70 | `comprobar_asiento_analitico.py:50` | `round(…, 6)` → `7` | ninguna diferencia por debajo de la millonésima | `test_m70_la_diferencia_se_redondea_a_la_millonesima` |
| 97 | `:112` | `int(f['n'] or 0)` → `or 1` | `COUNT(*)` nunca es NULL: código muerto | quitado el `or 0` (y el de `nuestras`, `SUM(CASE…)` de un grupo) |
| 107, 110-112 | `:158-161` | `required=True` → `False` | `main` solo se probaba con todos los argumentos | `test_m107_m110_m111_m112_argumentos_obligatorios` |
| 116, 118 | `settings.py:49-50` | defectos 3/10 → 4/11 | nadie leía los defectos de `Settings` | `test_m116_m118_estados_por_defecto_y_por_entorno` |

`app.js` (sv4) queda fuera: la herramienta solo muta Python. Sus cambios
los cubren los tests de `test_f031_preflight_avisos.py` ejecutados con
`node` (rojo antes, verde después) y la verificación M3 en navegador.

<!-- progress/mutacion_F-036.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036` el 2026-10-07 20:28.

## Alcance

Origen del diff: **rama** (`6e56244ac08b5565bfb18afd45e63c8d7fbb0280` .. `feature/F-036-casado-contra-recursos`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 38 |
| `services/partes-persistencia/application/services/casado_recurso.py` | 129 |
| `services/partes-persistencia/application/services/empleado_matcher.py` | 41 |
| `services/partes-persistencia/application/services/medicion_casado.py` | 237 |
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | 53 |
| `services/partes-persistencia/application/services/sigrid_matcher_provider.py` | 19 |
| `services/partes-persistencia/domain/models/parte_records.py` | 6 |
| `services/partes-persistencia/domain/models/sigrid_models.py` | 3 |
| `services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py` | 5 |
| `services/partes-persistencia/medir_casado_recursos.py` | 189 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 7 |
| **Total** | **727** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 108 |
| Mutantes evaluados | 108 |
| Muertos | 108 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 882.8 s |
| SHA de HEAD medido | `ee2c5d14aa06274146c14613f76c2cc1b8b0dad5` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_0/services/partes-persistencia` | 65.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_1/services/partes-persistencia` | 65.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_2/services/partes-persistencia` | 66.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_3/services/partes-persistencia` | 66.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_4/services/partes-persistencia` | 64.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_emo10cka/wk_5/services/partes-persistencia` | 65.5 |
| Media por mutante evaluado (s) | 8.2 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Primera campaña (HEAD `7e06e5e`, 2026-10-07 20:08): 113 mutantes, 103 muertos, 10 supervivientes

Informe íntegro en el historial (`git show eca56bb:progress/mutacion_F-036.md`). Cómo se resolvió
cada superviviente (commit `eca56bb`) antes de esta segunda campaña:

| # | Superviviente | Análisis | Resolución |
|---|---|---|---|
| 1 | `casado_recurso.py` `round(score, 4)` → 5 | Equivalente: el score ya llega a 4 decimales | Se quita el `round` (código muerto) |
| 2 | `empleado_matcher.py` `round(mejor, 4)` → 5 | Equivalente: `name_similarity` ya devuelve `round(…, 4)` | Se quita el `round` |
| 3 | `LineaMedida` `frozen=True` → `False` | Hueco: ningún test exigía inmutabilidad | Test `r28_la_linea_medida_es_inmutable` |
| 4–5 | orden por empresa `e or 0` → `e and 0` / `e or 1` | 4 hueco (empresas ya en orden en el fixture); 5 equivalente | Orden reescrito sin constantes + test `r24_empresas_en_orden_y_la_sin_empresa_al_final` |
| 6–7 | separador de la tabla Markdown `+ 1` → `- 1` / `+ 2` | Hueco: no se comprobaba la fila separadora | Assert de `|---|---|---|---|---|---|` |
| 8 | INFO R3 `not` quitado | Hueco: el fixture daba 2 de 4 con y sin el `not` | Fixture asimétrico: «3 de 5» |
| 9 | `mkdir(parents=True)` → `False` | Hueco: la carpeta padre ya existía | El test escribe en una ruta anidada inexistente |
| 10 | `sys.argv[1:]` → `[2:]` | Equivalente: `main` ignoraba los argumentos | `main()` sin parámetros |

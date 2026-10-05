<!-- progress/mutacion_F-030.md -->
# F-030 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-030` el 2026-10-05 15:33.

## Alcance

Origen del diff: **rama** (`28ea4ad6dca4702ad60233cc3ba75b6c253ba539` .. `feature/F-030-recurso-sin-ficha`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | 38 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 62 |
| `services/partes-persistencia/application/services/fichas_de_recurso.py` | 55 |
| `services/partes-persistencia/application/services/parte_normalizer.py` | 19 |
| `services/partes-persistencia/application/services/sigrid_matcher_provider.py` | 8 |
| `services/partes-persistencia/domain/models/parte_records.py` | 5 |
| `services/partes-persistencia/domain/models/sigrid_models.py` | 4 |
| `services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py` | 8 |
| **Total** | **199** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 18 |
| Mutantes evaluados | 18 |
| Muertos | 18 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 957.2 s |
| SHA de HEAD medido | `551a1d81dc0a9239449cfccb1ef76bb697091b2b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_0/services/partes-front` | 311.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_0/services/partes-persistencia` | 9.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_1/services/partes-front` | 312.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_1/services/partes-persistencia` | 9.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_2/services/partes-persistencia` | 17.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_3/services/partes-persistencia` | 17.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_4/services/partes-persistencia` | 19.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-030_9aunpzei/wk_5/services/partes-persistencia` | 17.3 |
| Media por mutante evaluado (s) | 53.2 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


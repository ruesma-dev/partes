<!-- progress/mutacion_F-023.md -->
# F-023 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-023` el 2026-10-01 02:51.

## Alcance

Origen del diff: **rama** (`e5e2bd91ef891a8582b1ba7df2123db72630cc82` .. `feature/F-023-recurso-alta-empresa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/domain/models/parte_models.py` | 4 |
| `services/partes-front/application/services/obra_catalog.py` | 22 |
| `services/partes-front/infrastructure/database/orm_models.py` | 9 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 17 |
| `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 82 |
| `services/partes-front/interface_adapters/web/app.py` | 7 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 134 |
| `services/partes-persistencia/application/services/empleado_matcher.py` | 36 |
| `services/partes-persistencia/application/services/empresa_membrete.py` | 103 |
| `services/partes-persistencia/application/services/obra_matcher.py` | 53 |
| `services/partes-persistencia/application/services/parte_normalizer.py` | 3 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 103 |
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | 290 |
| `services/partes-persistencia/application/services/sigrid_matcher_provider.py` | 28 |
| `services/partes-persistencia/config/settings.py` | 10 |
| `services/partes-persistencia/domain/models/parte_records.py` | 12 |
| `services/partes-persistencia/domain/models/sigrid_models.py` | 24 |
| `services/partes-persistencia/domain/ports/sigrid_lookup_port.py` | 6 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 9 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 12 |
| `services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py` | 146 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 96 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 63 |
| `services/partes-transfer/application/services/coherencia_recurso.py` | 78 |
| `services/partes-transfer/application/services/reglas_registro.py` | 33 |
| `services/partes-transfer/config/settings.py` | 2 |
| `services/partes-transfer/domain/models/registro_models.py` | 17 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 104 |
| **Total** | **1503** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 214 |
| Mutantes evaluados | 214 |
| Muertos | 214 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2076.5 s |
| SHA de HEAD medido | `ad48d2dd39b92197f09e5d11b6250a71ca8f2823` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_0/services/partes-front` | 292.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_0/services/partes-persistencia` | 16.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_0/services/partes-transfer` | 12.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_1/services/partes-front` | 291.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_1/services/partes-persistencia` | 16.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_1/services/partes-transfer` | 12.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_2/services/partes-front` | 290.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_2/services/partes-persistencia` | 17.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_2/services/partes-transfer` | 12.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_3/services/partes-front` | 291.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_3/services/partes-persistencia` | 16.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_3/services/partes-transfer` | 12.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_4/services/partes-front` | 292.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_4/services/partes-persistencia` | 16.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_4/services/partes-transfer` | 12.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_5/services/partes-front` | 290.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_5/services/partes-persistencia` | 16.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-023_9t9f3t7q/wk_5/services/partes-transfer` | 12.7 |
| Media por mutante evaluado (s) | 9.7 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


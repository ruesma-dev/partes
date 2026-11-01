<!-- progress/mutacion_F-056_enmienda.md -->
# F-056 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-056` el 2026-10-29 12:51.

## Alcance

Origen del diff: **rama** (`3ba340309c2ba78f2e87148f3e467d4d38f11f05` .. `feature/F-056-franquicia-de-extras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/franquicia.py` | 2 |
| `services/partes-front/infrastructure/database/orm_models.py` | 1 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 1 |
| `services/partes-front/interface_adapters/web/app.py` | 1 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 1 |
| `services/partes-transfer/application/pipelines/franquicia_pipeline.py` | 34 |
| `services/partes-transfer/application/services/franquicia.py` | 52 |
| `services/partes-transfer/config/settings.py` | 10 |
| `services/partes-transfer/domain/models/registro_models.py` | 1 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 34 |
| `services/partes-transfer/interface_adapters/api/app.py` | 5 |
| `services/partes-transfer/main.py` | 14 |
| **Total** | **156** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 23 |
| Muertos | 23 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 273.4 s |
| SHA de HEAD medido | `56b5ca3c23b6202c55b606ebb26a39802f946c41` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_vfdm9j06/wk_0/services/partes-transfer` | 37.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_vfdm9j06/wk_1/services/partes-transfer` | 37.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_vfdm9j06/wk_2/services/partes-transfer` | 37.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_vfdm9j06/wk_3/services/partes-transfer` | 37.4 |
| Media por mutante evaluado (s) | 11.9 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

